# CLAUDE.md — Zoro Energy Ingestion Pipeline

This file gives you complete context on the Zoro Energy data ingestion pipeline.
Read this before touching any code or infrastructure.

---

## What this project is

A production cloud pipeline that ingests real-time sensor data from customer buildings via MQTT, streams it through Kafka, normalises it, and stores it in TimescaleDB. Data is then queryable via a REST API and visualised in Grafana.

**Production state as of 2026-05-31:**
- Running on GCP (`zoro-energy-enterprise`, `europe-west3`)
- Image tag: `prod-v8`
- Two active customer pipelines: `mock-01` (internal test) and `scs-01` (Schwarz Campus Services — first real PoC customer)
- SCS bridge connected live to `pssolsch01.messaging.smartcity.hn:8893`, awaiting sensor data

---

## Repository

**Primary repo:** `C:\Users\dellg\OneDrive\Documents\ZoroEnergyPlatform`  
Branch: `main`

The working directory `C:\Users\dellg\Documents\ZoroEnergyIngestionPipeline` is used for Claude Code sessions but all source files live in ZoroEnergyPlatform.

---

## Data flow

```
Customer MQTT Broker (MQTTS)
        │  zoro-mqtt-bridge (one per customer)
        ▼
Confluent Kafka — zoro.prod.raw.{tenant}.v1
        │  zoro-format-adapter
        ▼
Confluent Kafka — zoro.prod.obs.{tenant}.v1   (or dlq on parse fail)
        │  zoro-kafka-writer
        ▼
TimescaleDB (PostgreSQL)
        │
        ├── REST API (Cloud Run) — https://zoro-prod-api-euw3-run01-ngas5xm4ca-ey.a.run.app
        └── Grafana dashboard (port 3000 via IAP tunnel)
```

---

## Key source files

| File | Purpose |
|---|---|
| `cloud/ingress/mqtt_bridge.py` | MQTT-to-Kafka bridge. One container per customer. |
| `cloud/ingress/format_adapter.py` | Parses raw Kafka messages → normalised observations. Parser: `_parse_json_v1` (requires `timestamp`, `device_id`, `metric`, `value` numeric, `unit`). Failed messages → DLQ. |
| `cloud/ingress/kafka_to_timescale.py` | Reads obs topic, batch-writes to TimescaleDB. |
| `cloud/ingress/Dockerfile` | Single image for all three ingress workers. `WORKER` env var selects which script runs. |
| `cloud/api/` | FastAPI REST API deployed to Cloud Run. |
| `cloud/terraform/` | All GCP infrastructure as code. |
| `cloud/terraform/vm.tf` | GCE VM definition. Startup script template. |
| `cloud/terraform/scripts/vm-startup.sh` | Generates `docker-compose.yml` on boot and starts all containers. |
| `cloud/terraform/variables_scs.tf` | SCS-specific Terraform variables (separate file — don't modify `variables.tf` for new customers). |
| `cloud/terraform/secrets_scs.tf` | SCS Secret Manager secret. |
| `cloud/terraform/terraform.tfvars` | **GITIGNORED. Contains secrets. Never commit.** |
| `dev/mock-broker/config/passwd` | Mosquitto password file. **This is the authoritative source** — Terraform syncs it to GCS on every apply. Never manually upload to GCS without also updating this file. |
| `cloud/deploy.ps1` | One-command deploy: builds images, pushes to GCR, runs terraform apply, optionally reboots VM. |
| `cloud/sanity_test.sh` | End-to-end test: publishes MQTT → checks TimescaleDB for both mock-01 and scs-01 rows. |

---

## Infrastructure

| Resource | Value |
|---|---|
| GCP project | `zoro-energy-enterprise` |
| Region | `europe-west3` (Frankfurt) |
| VM | `zoro-prod-data-euw3-vm01`, zone `europe-west3-a` |
| VM access | `gcloud compute ssh zoro-prod-data-euw3-vm01 --zone=europe-west3-a --tunnel-through-iap --project=zoro-energy-enterprise` |
| Container registry | `europe-west3-docker.pkg.dev/zoro-energy-enterprise/zoro-prod-euw3-reg01` |
| Assets GCS bucket | `zoro-energy-enterprise-prod-assets` |
| Confluent bootstrap | `pkc-75m1o.europe-west3.gcp.confluent.cloud:9092` |
| Cloud Run API | `https://zoro-prod-api-euw3-run01-ngas5xm4ca-ey.a.run.app` |

---

## Running containers on the VM (all 7 must be up)

| Container | Service | Image |
|---|---|---|
| `zoro-mock-mqtt-broker` | Mosquitto (mock broker) | `eclipse-mosquitto:2.0` |
| `zoro-mqtt-bridge` | MQTT bridge for mock-01 | `zoro-ingress:prod-v8` |
| `zoro-scs-mqtt-bridge` | MQTT bridge for scs-01 | `zoro-ingress:prod-v8` |
| `zoro-format-adapter` | Payload parser | `zoro-ingress:prod-v8` |
| `zoro-kafka-writer` | TimescaleDB writer | `zoro-ingress:prod-v8` |
| `zoro-timescaledb` | TimescaleDB | `timescale/timescaledb:latest-pg16` |
| `zoro-grafana` | Grafana | `grafana/grafana:latest` |

Check: `sudo docker ps --format "table {{.Names}}\t{{.Status}}"`

---

## Kafka topic naming

Pattern: `zoro.prod.{type}.{tenant-code}.v1`

| Type | Description |
|---|---|
| `raw` | Raw MQTT payload bytes, unmodified |
| `obs` | Normalised observations (after format adapter) |
| `dlq` | Dead-letter — payloads that failed parsing |

Current topics: `mock-01` and `scs-01`. format_adapter and kafka_writer use regex patterns (`^zoro\.prod\.raw\..*`, `^zoro\.prod\.obs\..*`) so new customer topics are picked up automatically — no config changes needed.

---

## Customer registry

| Tenant code | Customer | Building ID | MQTT broker |
|---|---|---|---|
| `mock-01` | Internal test | `building-01` | `mock-mqtt-broker:8883` (in-cluster) |
| `scs-01` | Schwarz Campus Services | `de-hnn-bildungscampus-01` | `pssolsch01.messaging.smartcity.hn:8893` |

Building ID convention: `{iso-country}-{city3}-{site}-{seq}` e.g. `de-hnn-bildungscampus-01`

---

## Payload format (JSON v1)

format_adapter's `_parse_json_v1` requires all 5 fields:

```json
{
  "timestamp": "2026-05-24T14:31:23Z",
  "device_id":  "sensor-01",
  "metric":     "temperature",
  "value":      21.3,
  "unit":       "C"
}
```

`value` must be numeric (int or float). If any field is missing or value is a string, message goes to DLQ. The Neuberger format used by SCS likely does NOT match this schema — a `_parse_neuberger_v1` parser may need to be added to format_adapter.py once we see real message samples.

---

## Deploy workflow

```powershell
# From: C:\Users\dellg\OneDrive\Documents\ZoroEnergyPlatform\cloud\
.\deploy.ps1              # build + push + terraform apply (no reboot)
.\deploy.ps1 -RebootVM    # + reboot VM (required when changing env vars / secrets)
```

deploy.ps1 increments the image tag automatically (`prod-v7` → `prod-v8`). After a reboot, the startup script re-runs and recreates all containers with fresh env vars from Secret Manager.

**Known issue:** After VM reboot, docker daemon auto-restarts containers with OLD config before the startup script runs. Run `sudo docker compose -f /opt/zoro/docker-compose.yml up -d --force-recreate {service}` to force the new config.

---

## Adding a new customer

1. Create `cloud/terraform/variables_{customer}.tf` (mirror `variables_scs.tf`)
2. Create `cloud/terraform/secrets_{customer}.tf` (mirror `secrets_scs.tf`)
3. Add customer vars to `vm.tf` templatefile call
4. Add docker-compose service block to `cloud/terraform/scripts/vm-startup.sh`
5. Add customer credentials to `cloud/terraform/terraform.tfvars` (gitignored)
6. Add customer user to `dev/mock-broker/config/passwd` (run `mosquitto_passwd` — see confluent-guide.md)
7. Run `.\deploy.ps1 -RebootVM`
8. Force-recreate the new bridge container if auto-restart used old config

---

## Security constraints

- **Never rotate** Confluent API key `I7BRNEPMSMGBYMGN` without explicit approval
- **terraform.tfvars is gitignored** — never commit it
- Real customer credentials live only in Secret Manager and terraform.tfvars
- TLS probe from VM before connecting to any new broker: `echo | openssl s_client -connect {host}:{port} -brief 2>&1`
- `MQTT_TLS_INSECURE=true` disables cert verification — use only for PoC/private CA brokers, document it

---

## Sanity test

```bash
# SSH to VM then:
sudo bash /opt/zoro/sanity_test.sh
```

Expected output: both `mock-01` and `scs-01` rows in the TimescaleDB query result.

---

## MkDocs documentation site

Material for MkDocs is configured at `mkdocs.yml` in the repo root.

```bash
pip install -r docs-requirements.txt
mkdocs serve        # local preview at http://localhost:8000
mkdocs build        # build static site to site/
```

Key docs:
- `docs/integration-guide.md` — customer-facing MQTT integration guide
- `docs/developer-guide.md` — local dev setup (BOPTEST simulation)
- `docs/confluent-guide.md` — internal Kafka/Confluent ops
- `docs/diagrams/` — 8 Mermaid diagram files (system architecture, data flow, etc.)

---

## Next steps (as of 2026-05-31)

1. **Wait for SCS sensor data** — bridge is connected to `pssolsch01.messaging.smartcity.hn:8893`. When data arrives, inspect raw payload on `zoro.prod.raw.scs-01.v1` to determine if Neuberger format matches `_parse_json_v1` or needs a new parser.
2. **Add Neuberger parser if needed** — add `_parse_neuberger_v1` to `cloud/ingress/format_adapter.py` and add to `PARSERS` list.
3. **Customer integration docs** — `docs/integration-guide.md` is written; share with SCS.
4. **MkDocs deployment** — deploy `site/` to GCS static hosting when ready to publish.
