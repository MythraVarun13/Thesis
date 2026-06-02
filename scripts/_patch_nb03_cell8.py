"""Fix markdown cell 30c2d8b6d2d1b22c in 03_timeseries_profiling.ipynb."""
import json
from pathlib import Path

NB = Path(__file__).parent.parent / "notebooks" / "03_timeseries_profiling.ipynb"

NEW_MARKDOWN = """\
## Step 4: Signal groups by start date — validated by name

Five signals share start date 2024-02-27, later than all others.
A naive date cutoff would label all five as "weather signals",
but validation shows the split is **deployment timing, not signal type**:

| File | Actual category | Correctly labelled by date? |
|---|---|---|
| `realLeistungGebSystem.csv` | Net building electrical power (BMS) | No — misclassified |
| `sun_alt.csv` | Solar altitude, degrees (derived) | Yes |
| `sun_azi.csv` | Solar azimuth, degrees (derived) | Yes |
| `wind_now.csv` | Current wind speed, m/s | Yes |
| `wind_tomorrow.csv` | Wind forecast, m/s | Yes |

All five were added in a single monitoring system expansion in Feb 2024.
Classification uses **signal name semantics**, not start date.\
"""

nb = json.loads(NB.read_text(encoding="utf-8"))
for cell in nb["cells"]:
    if cell.get("id") == "30c2d8b6d2d1b22c":
        cell["source"] = NEW_MARKDOWN
        print("Patched markdown cell.")
        break

NB.write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
print("Saved.")
