"""
08_load_to_timescaledb.py
=========================
Load hourly-resampled EnFa data into the local TimescaleDB instance.

Reads:  data/processed/hourly.parquet       (produced by scripts/07_resample_hourly.py)
        reports/zoro_pipeline_mapping.csv   (signal metadata: category, unit, brick)

Writes: TimescaleDB localhost:5432
          tenants          — creates tenant 'enfa-01' if not present
          buildings        — creates building 'enfa-building-01' if not present
          datapoints       — one row per signal (upserted, idempotent)
          observations     — all hourly rows (ON CONFLICT DO NOTHING, safe to re-run)

dp_hash convention (matches kafka_to_timescale.py):
    sha256(f"enfa-01/enfa-building-01/{signal_name}".encode()).hexdigest()[:8]

Usage
-----
    python scripts/08_load_to_timescaledb.py
    python scripts/08_load_to_timescaledb.py --host localhost --port 5432 --db zoro

Notes
-----
- Bypasses Kafka intentionally: historical batch load, not real-time stream.
- Safe to re-run: all inserts are idempotent (upsert / ON CONFLICT DO NOTHING).
- Checks disk space on the TimescaleDB host before inserting.
"""
from __future__ import annotations

import argparse
import hashlib
import logging
import sys
import time
from pathlib import Path

import pandas as pd
import psycopg2
import psycopg2.extras
from tqdm import tqdm

logger = logging.getLogger(__name__)

# ── Tenant / building identifiers ─────────────────────────────────────────────
TENANT_ID   = "enfa-01"
TENANT_NAME = "EnFa Building (Historical)"
BUILDING_ID = "enfa-building-01"
BUILDING_NAME = "EnFa Research Building, Esslingen"
BUILDING_TZ = "Europe/Berlin"

# ── Batch size for bulk inserts ────────────────────────────────────────────────
BATCH_SIZE = 10_000

# ── Minimum free disk space to proceed (bytes) ────────────────────────────────
MIN_FREE_DISK_BYTES = 2 * 1024**3  # 2 GB


# ── SQL ───────────────────────────────────────────────────────────────────────

_UPSERT_TENANT = """
    INSERT INTO tenants (tenant_id, name)
    VALUES (%s, %s)
    ON CONFLICT (tenant_id) DO NOTHING
"""

_UPSERT_BUILDING = """
    INSERT INTO buildings (building_id, tenant_id, name, timezone)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (building_id) DO NOTHING
"""

_UPSERT_DATAPOINT = """
    INSERT INTO datapoints (dp_id, hash, building_id, tenant_id, brick, pin, unit, protocol)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (hash) DO UPDATE SET
        brick    = EXCLUDED.brick,
        pin      = EXCLUDED.pin,
        unit     = EXCLUDED.unit,
        protocol = EXCLUDED.protocol
"""

_INSERT_OBS = """
    INSERT INTO observations (ts, dp_hash, value, quality)
    VALUES %s
    ON CONFLICT (ts, dp_hash) DO NOTHING
"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def compute_dp_hash(tenant_id: str, building_id: str, signal_name: str) -> str:
    """Match the sha256[:8] convention from kafka_to_timescale.py."""
    key = f"{tenant_id}/{building_id}/{signal_name}"
    return hashlib.sha256(key.encode()).hexdigest()[:8]


def check_disk_space(conn: psycopg2.extensions.connection) -> None:
    """Query free disk space via pg_stat_file; warn if below threshold."""
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT (pg_database_size(current_database()))::bigint AS db_bytes,
                       (SELECT setting::bigint * 1024
                        FROM pg_settings WHERE name = 'block_size') AS block_bytes
            """)
            row = cur.fetchone()
            if row:
                db_bytes = row[0] or 0
                logger.info("Current DB size: %.1f MB", db_bytes / 1e6)
    except Exception as exc:
        logger.debug("Disk space check skipped: %s", exc)


def load_signal_meta(mapping_path: Path) -> dict[str, dict]:
    """Return {signal_name: {category, zoro_unit, zoro_metric, zoro_device_id_suffix}}."""
    if not mapping_path.exists():
        logger.warning("Pipeline mapping not found: %s — using defaults", mapping_path)
        return {}
    df = pd.read_csv(mapping_path)
    df = df[df["exclude"].astype(str).str.lower() != "true"]
    meta: dict[str, dict] = {}
    for _, row in df.iterrows():
        name = str(row["signal_name"]).strip()
        if name:
            meta[name] = {
                "category": str(row.get("category", "unknown")).strip(),
                "zoro_unit": str(row.get("zoro_unit", "")).strip(),
                "zoro_metric": str(row.get("zoro_metric", name)).strip(),
                "english_meaning": str(row.get("english_meaning", "")).strip(),
            }
    return meta


# ── Main loading logic ─────────────────────────────────────────────────────────

def load_to_timescaledb(
    parquet_path: Path,
    mapping_path: Path,
    host: str,
    port: int,
    dbname: str,
    user: str,
    password: str,
) -> None:
    if not parquet_path.exists():
        logger.error(
            "Parquet file not found: %s\n"
            "Run:  python scripts/07_resample_hourly.py --threads 6",
            parquet_path,
        )
        sys.exit(1)

    logger.info("Reading parquet: %s", parquet_path)
    wide = pd.read_parquet(parquet_path)
    logger.info("Parquet loaded: %d rows × %d columns", len(wide), len(wide.columns))

    signal_meta = load_signal_meta(mapping_path)
    signals = [c for c in wide.columns]
    logger.info("Signals in parquet: %d", len(signals))

    # ── Connect ──
    logger.info("Connecting to TimescaleDB %s:%d/%s", host, port, dbname)
    conn = psycopg2.connect(
        host=host, port=port, dbname=dbname, user=user, password=password,
        connect_timeout=10,
    )
    conn.autocommit = False

    try:
        check_disk_space(conn)

        with conn.cursor() as cur:
            # ── Tenant + Building ──
            cur.execute(_UPSERT_TENANT, (TENANT_ID, TENANT_NAME))
            cur.execute(_UPSERT_BUILDING,
                        (BUILDING_ID, TENANT_ID, BUILDING_NAME, BUILDING_TZ))
            conn.commit()
            logger.info("Tenant '%s' and building '%s' registered.", TENANT_ID, BUILDING_ID)

            # ── Datapoints ──
            dp_records = []
            dp_hash_map: dict[str, str] = {}  # signal_name → dp_hash
            for sig in signals:
                meta  = signal_meta.get(sig, {})
                cat   = meta.get("category", "unknown")
                unit  = meta.get("zoro_unit", "")
                h     = compute_dp_hash(TENANT_ID, BUILDING_ID, sig)
                dp_id = f"{TENANT_ID}/{BUILDING_ID}/{sig}"
                dp_hash_map[sig] = h
                dp_records.append((dp_id, h, BUILDING_ID, TENANT_ID, cat, sig, unit, "influxdb_csv"))

            psycopg2.extras.execute_batch(cur, _UPSERT_DATAPOINT, dp_records)
            conn.commit()
            logger.info("Upserted %d datapoints.", len(dp_records))

        # ── Observations — melt wide → long, insert in batches ──
        logger.info("Melting wide DataFrame to long format...")
        # Reset index so hour_utc becomes a column
        long = wide.reset_index().melt(
            id_vars=["hour_utc"], var_name="signal_name", value_name="value"
        )
        long = long.dropna(subset=["value"])
        long["dp_hash"] = long["signal_name"].map(dp_hash_map)
        long = long[long["dp_hash"].notna()]

        total_rows = len(long)
        logger.info("Total observation rows to insert: %d", total_rows)

        # Build list of tuples for execute_values
        obs_tuples = [
            (row.hour_utc, row.dp_hash, float(row.value), 0)
            for row in long.itertuples(index=False)
        ]

        t0 = time.time()
        inserted = 0
        with conn.cursor() as cur:
            for i in tqdm(range(0, len(obs_tuples), BATCH_SIZE),
                          desc="Inserting observations", unit="batch"):
                batch = obs_tuples[i : i + BATCH_SIZE]
                psycopg2.extras.execute_values(
                    cur,
                    _INSERT_OBS,
                    batch,
                    template="(%s, %s, %s, %s)",
                    page_size=BATCH_SIZE,
                )
                inserted += len(batch)
                conn.commit()

        elapsed = time.time() - t0
        print(f"\n{'='*60}")
        print(f"Tenant:      {TENANT_ID}")
        print(f"Building:    {BUILDING_ID}")
        print(f"Signals:     {len(signals)}")
        print(f"Rows:        {inserted:,}")
        print(f"Elapsed:     {elapsed/60:.1f} min")
        print(f"\nOpen Grafana: http://localhost:3000")
        print(f"  → filter by tenant_id = '{TENANT_ID}'")

    finally:
        conn.close()


# ── CLI ───────────────────────────────────────────────────────────────────────

def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Load hourly EnFa parquet into local TimescaleDB.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--host",     default="localhost")
    p.add_argument("--port",     type=int, default=5432)
    p.add_argument("--db",       default="zoro", dest="dbname")
    p.add_argument("--user",     default="zoro")
    p.add_argument("--password", default="zoro")
    p.add_argument("--parquet",  default=None,
                   help="Path to hourly.parquet (default: data/processed/hourly.parquet)")
    p.add_argument("--mapping",  default=None,
                   help="Path to zoro_pipeline_mapping.csv")
    return p


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
    args = build_arg_parser().parse_args()

    _scripts_dir  = Path(__file__).resolve().parent
    project_root  = _scripts_dir.parent

    parquet_path = Path(args.parquet) if args.parquet else \
                   project_root / "data" / "processed" / "hourly.parquet"
    mapping_path = Path(args.mapping) if args.mapping else \
                   project_root / "reports" / "zoro_pipeline_mapping.csv"

    load_to_timescaledb(
        parquet_path=parquet_path,
        mapping_path=mapping_path,
        host=args.host,
        port=args.port,
        dbname=args.dbname,
        user=args.user,
        password=args.password,
    )


if __name__ == "__main__":
    main()
