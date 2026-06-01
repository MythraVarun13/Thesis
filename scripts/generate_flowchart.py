import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np
from pathlib import Path

OUT = Path("/sessions/keen-upbeat-lamport/mnt/ZE/reports/plots/00_eda_pipeline_flowchart.png")

fig, ax = plt.subplots(figsize=(16, 20))
ax.set_xlim(0, 16)
ax.set_ylim(0, 20)
ax.axis("off")
fig.patch.set_facecolor("white")

def box(ax, x, y, w, h, text, subtitle, color, textcolor="white", fontsize=11):
    rect = FancyBboxPatch((x - w/2, y - h/2), w, h,
                           boxstyle="round,pad=0.15", linewidth=1.5,
                           edgecolor="#333333", facecolor=color, zorder=3)
    ax.add_patch(rect)
    ax.text(x, y + 0.12, text, ha="center", va="center", fontsize=fontsize,
            fontweight="bold", color=textcolor, zorder=4)
    if subtitle:
        ax.text(x, y - 0.32, subtitle, ha="center", va="center", fontsize=8,
                color=textcolor, alpha=0.9, zorder=4, style="italic")

def arrow(ax, x1, y1, x2, y2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color="#555555",
                                lw=1.8, mutation_scale=18), zorder=2)

def side_note(ax, x, y, text, color):
    ax.text(x, y, text, ha="left", va="center", fontsize=8.5,
            color="#333333", zorder=4,
            bbox=dict(boxstyle="round,pad=0.3", facecolor=color, alpha=0.25,
                      edgecolor=color, linewidth=1))

# ── Title ──
ax.text(8, 19.3, "EnFa Dataset — EDA Pipeline", ha="center", va="center",
        fontsize=17, fontweight="bold", color="#1A237E")
ax.text(8, 18.85, "Raw CSV files → ZORO JSON v1 pipeline mapping  |  2026-05-31",
        ha="center", va="center", fontsize=10, color="#555555")

# ── INPUT ──
box(ax, 8, 18.1, 7, 0.75, "📁  Raw Data Input", "233 CSV files · ~40.5 GB · InfluxDB export", "#1565C0")

arrow(ax, 8, 17.72, 8, 17.1)

# ── STEP 1 ──
box(ax, 8, 16.7, 7, 0.75, "Step 1 · File Inventory  (01_scan_files.py)",
    "Count files · sizes · extensions · detect empties", "#1976D2")
side_note(ax, 11.7, 16.7,
          "Output:\n• reports/data_inventory.csv\n• context/data_inventory_context.md",
          "#1976D2")
arrow(ax, 8, 16.32, 8, 15.7)

# ── STEP 2 ──
box(ax, 8, 15.3, 7, 0.75, "Step 2 · Schema Detection  (02_detect_schema.py)",
    "Delimiter · encoding · column names · 6 KB head per file", "#0288D1")
side_note(ax, 11.7, 15.3,
          "Output:\n• reports/file_format_report.csv\n• reports/schema_summary.csv\n• reports/sample_rows/ (233 files)",
          "#0288D1")
arrow(ax, 8, 14.92, 8, 14.3)

# ── FINDING BOX ──
rect2 = FancyBboxPatch((3.8, 13.95), 8.4, 0.55,
                        boxstyle="round,pad=0.1", linewidth=1,
                        edgecolor="#4CAF50", facecolor="#E8F5E9", zorder=3)
ax.add_patch(rect2)
ax.text(8, 14.23, "✓  All 233 files: UTF-8 · semicolon delimiter · standard InfluxDB schema",
        ha="center", va="center", fontsize=9, color="#2E7D32", fontweight="bold", zorder=4)

arrow(ax, 8, 13.95, 8, 13.35)

# ── STEP 3 ──
box(ax, 8, 12.95, 7, 0.75, "Step 3 · Time-Series Profiling  (03_profile_timeseries.py)",
    "Head + tail read · start/end dates · sampling interval · gap detection", "#00838F")
side_note(ax, 11.7, 12.95,
          "Output:\n• reports/timestamp_coverage_report.csv\n• reports/sampling_interval_report.csv\n• context/data_quality_context.md",
          "#00838F")
arrow(ax, 8, 12.57, 8, 11.95)

# ── FINDING BOX ──
rect3 = FancyBboxPatch((2.5, 11.6), 11, 0.55,
                        boxstyle="round,pad=0.1", linewidth=1,
                        edgecolor="#4CAF50", facecolor="#E8F5E9", zorder=3)
ax.add_patch(rect3)
ax.text(8, 11.88,
        "✓  BMS: Dec 2022 → May 2026 (live)  ·  Weather: Feb 2024+  ·  Dominant interval: ~20s  ·  15 snapshot-only files excluded",
        ha="center", va="center", fontsize=9, color="#2E7D32", fontweight="bold", zorder=4)

arrow(ax, 8, 11.6, 8, 11.0)

# ── STEP 4 ──
box(ax, 8, 10.6, 7, 0.75, "Step 4 · Thesis Parsing  (pdftotext + manual analysis)",
    "German thesis PDF → signal dictionary · system architecture · irradiance findings", "#558B2F")
side_note(ax, 11.7, 10.6,
          "Output:\n• context/thesis_context.md\n• val1006-1009 resolved\n• Irradiance gap confirmed",
          "#558B2F")
arrow(ax, 8, 10.22, 8, 9.6)

# ── STEP 5 ──
box(ax, 8, 9.2, 7, 0.75, "Step 5 · Signal Classification  (05_classify_signals.py)",
    "Pattern rules + direct map · German→English · unit hypothesis · confidence", "#E65100")
side_note(ax, 11.7, 9.2,
          "Output:\n• reports/signal_classification.csv\n• reports/sensor_catalog.csv\n• context/signal_dictionary.md",
          "#E65100")
arrow(ax, 8, 8.82, 8, 8.2)

# ── FINDING BOX ──
rect5 = FancyBboxPatch((2.8, 7.85), 10.4, 0.55,
                        boxstyle="round,pad=0.1", linewidth=1,
                        edgecolor="#4CAF50", facecolor="#E8F5E9", zorder=3)
ax.add_patch(rect5)
ax.text(8, 8.13,
        "✓  223 / 233 signals pipeline-ready  ·  3 excluded (artifacts)  ·  5 unknown  ·  High confidence: 197 signals",
        ha="center", va="center", fontsize=9, color="#2E7D32", fontweight="bold", zorder=4)

arrow(ax, 8, 7.85, 8, 7.25)

# ── STEP 6 ──
box(ax, 8, 6.85, 7, 0.75, "Step 6 · ZORO Pipeline Mapping",
    "Each signal → device_id · metric · unit (JSON v1 format)", "#AD1457")
side_note(ax, 11.7, 6.85,
          "Output:\n• reports/zoro_pipeline_mapping.csv\n• reports/zoro_mvp_readiness_matrix.csv\n• context/zoro_use_case_mapping.md",
          "#AD1457")
arrow(ax, 8, 6.47, 8, 5.85)

# ── STEP 7 ──
box(ax, 8, 5.45, 7, 0.75, "Step 7 · Exploratory Visualisation  (08_generate_plots.py)",
    "12 thematic plots · signal gallery · value distributions", "#6A1B9A")
side_note(ax, 11.7, 5.45,
          "Output:\n• reports/plots/ (12 plots)\n• reports/plots/signal_gallery_*",
          "#6A1B9A")
arrow(ax, 8, 5.07, 8, 4.45)

# ── OUTPUT ──
box(ax, 8, 4.05, 7, 0.75, "📄  Final EDA Summary  (EDA_SUMMARY.md)",
    "16-section report · MVP readiness · recommendations", "#4527A0")

arrow(ax, 8, 3.67, 8, 3.05)

# ── TARGET ──
box(ax, 8, 2.65, 7, 0.75, "🚀  ZORO Production Pipeline",
    "JSON v1 → Kafka → TimescaleDB → Grafana", "#1B5E20", fontsize=11)

# ── MVP RECOMMENDATION BOX ──
rect_mvp = FancyBboxPatch((1.2, 1.3), 13.6, 1.0,
                           boxstyle="round,pad=0.15", linewidth=2,
                           edgecolor="#F57F17", facecolor="#FFF8E1", zorder=3)
ax.add_patch(rect_mvp)
ax.text(8, 1.95, "Recommended First MVP:  Heat Pump FDD",
        ha="center", va="center", fontsize=12, fontweight="bold", color="#E65100", zorder=4)
ax.text(8, 1.58, "3 HP units · 3.5 years · defrost at 20s resolution · COP estimable now · 52 signals ready",
        ha="center", va="center", fontsize=9.5, color="#BF360C", zorder=4)

plt.tight_layout(pad=0.5)
plt.savefig(OUT, dpi=130, bbox_inches="tight")
plt.close()
print(f"Saved: {OUT}")
