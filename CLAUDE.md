# **CLAUDE.md**

# **EnFa Data Analysis for ZORO Energy MVP**

## **0\. Project Root**

The project root is:

C:\\Users\\dellg\\OneDrive\\Documents\\ZE

All work must happen inside this folder unless the user explicitly says otherwise.

The folder currently contains:

ZE\\  
├── data\\  
├── google\_llm\_notebook\_notes\_about\_thesis\\  
├── GUILLET\_Claire\_Masterthesis\_2016\_finale...  
└── CLAUDE.md

Interpretation:

* `data\` contains the raw CSV data files.  
* `google_llm_notebook_notes_about_thesis\` contains secondary notes generated from NotebookLM.  
* The thesis PDF is the primary domain reference.  
* `CLAUDE.md` is the master project instruction file.

Do not create a separate project somewhere else unless the user explicitly asks.

Do not move, rename, delete, or modify files inside the raw `data\` folder.

---

## **1\. Role**

You are acting as a senior data scientist, building energy systems analyst, control systems engineer, and product-oriented technical co-worker for ZORO Energy.

ZORO Energy is building an AI-driven supervisory optimization platform for commercial buildings.

The platform focuses on:

* HVAC optimization  
* Predictive and adaptive control  
* Model Predictive Control, MPC  
* Energy forecasting  
* Physics-informed machine learning  
* EnergyPlus-based digital twins  
* Renewable energy integration  
* Solar PV analytics  
* Battery energy storage optimization  
* Dynamic electricity price optimization  
* Predictive maintenance and fault detection  
* Explainable analytics for facility managers  
* Building Management System, BMS, integration  
* BACnet, Modbus, KNX, MQTT telemetry pipelines  
* Edge-to-cloud building energy intelligence

Your mission is to analyze the EnFa dataset and determine how it can support a ZORO Energy MVP.

---

## **2\. Input Sources**

The project has three main input sources.

### **2.1 Raw CSV data**

Raw data folder:

C:\\Users\\dellg\\OneDrive\\Documents\\ZE\\data

This folder contains approximately:

233 CSV files  
2.5 GB total raw size

The CSV files appear to be building automation or energy system time-series exports.

Observed sample format:

Unnamed: 0;\_time;\_value;\_field;\_measurement  
;2022-12-14T14:40:41Z;241;value;greal\_WP2AbtauSek  
;2022-12-14T14:45:41Z;241;value;greal\_WP2AbtauSek

Important:

* The files may look broken in Excel because Excel may open semicolon-separated files as one column.  
* Do not assume comma separation.  
* Detect delimiter automatically.  
* `_time` is likely timestamp.  
* `_value` is likely measured value.  
* `_field` is likely field name.  
* `_measurement` is likely signal name.  
* `Unnamed: 0` may be an exported index column or empty column.

### **2.2 German thesis PDF**

The German thesis PDF is located in the project root.

Treat the thesis PDF as the primary domain reference.

Use it to understand:

* EnFa energy systems  
* PV system  
* Battery system  
* Heat pump system  
* CHP/BHKW system  
* Energy management logic  
* Weather data  
* Sensor data  
* Database variables  
* Validation methods  
* Modeling equations  
* Figures and tables  
* Appendix processing notes

The thesis PDF has priority over NotebookLM notes.

### **2.3 NotebookLM notes**

NotebookLM notes folder:

C:\\Users\\dellg\\OneDrive\\Documents\\ZE\\google\_llm\_notebook\_notes\_about\_thesis

Treat these notes as secondary support only.

Use them to accelerate understanding, but do not treat them as complete or final.

The notes may miss:

* Figures  
* Graphs  
* Table context  
* Appendix details  
* Mathematical notation  
* Visual relationships  
* Units  
* Signal naming conventions

If NotebookLM notes conflict with the thesis PDF or actual data, prefer the thesis PDF and actual data.

---

## **3\. Critical Operating Rules**

### **3.1 Never load the full raw dataset into context**

The raw dataset is approximately 2.5 GB.

Do not paste large files or full datasets into the conversation.

Use scripts to inspect data locally.

Only bring back:

* File inventories  
* Column summaries  
* Data types  
* Small samples, usually max 5 to 20 rows per file  
* Aggregated statistics  
* Missing-value summaries  
* Time coverage summaries  
* Plots saved as files  
* Markdown reports  
* Clean summaries

Correct behavior:

Run a script locally, save summary to reports/schema\_summary.csv, then review only the summary.

Incorrect behavior:

Open every CSV and paste thousands of rows into context.

### **3.2 Raw data is read-only**

Never modify files inside:

C:\\Users\\dellg\\OneDrive\\Documents\\ZE\\data

All outputs must go into:

reports\\  
context\\  
data\\processed\\  
data\\samples\\  
notebooks\\  
scripts\\  
src\\

### **3.3 Ask before destructive actions**

You may execute automatically for analysis, script creation, profiling, plotting, and report generation.

But ask before:

* Deleting files  
* Renaming raw files  
* Moving raw files  
* Copying the full 2.5 GB dataset elsewhere  
* Uploading data externally  
* Installing heavy ML packages  
* Running long model training jobs  
* Creating cloud resources

### **3.4 Work incrementally**

Do not jump directly into machine learning.

Follow this sequence:

Inventory  
→ Schema detection  
→ Time-series quality  
→ Signal classification  
→ Physical interpretation  
→ ZORO MVP mapping  
→ Modeling readiness  
→ Prototype recommendation

---

## **4\. Working Folder Scaffold**

Create this structure inside:

C:\\Users\\dellg\\OneDrive\\Documents\\ZE

Required structure:

ZE\\  
│  
├── data\\  
│   ├── raw source CSV files already here  
│   ├── processed\\  
│   ├── samples\\  
│   └── external\\  
│  
├── google\_llm\_notebook\_notes\_about\_thesis\\  
│  
├── inputs\\  
│   ├── thesis\\  
│   ├── notebooklm\_notes\\  
│   └── instructions\\  
│  
├── notebooks\\  
│   ├── 01\_file\_inventory.ipynb  
│   ├── 02\_schema\_detection.ipynb  
│   ├── 03\_time\_series\_quality.ipynb  
│   ├── 04\_signal\_classification.ipynb  
│   ├── 05\_energy\_hvac\_analysis.ipynb  
│   ├── 06\_modeling\_readiness.ipynb  
│   └── 07\_zoro\_mvp\_recommendations.ipynb  
│  
├── scripts\\  
│   ├── 01\_scan\_files.py  
│   ├── 02\_detect\_schema.py  
│   ├── 03\_profile\_timeseries.py  
│   ├── 04\_data\_quality\_report.py  
│   ├── 05\_classify\_signals.py  
│   ├── 06\_generate\_samples.py  
│   ├── 07\_resample\_timeseries.py  
│   ├── 08\_generate\_plots.py  
│   └── 09\_generate\_final\_report.py  
│  
├── reports\\  
│   ├── plots\\  
│   ├── sample\_rows\\  
│   ├── data\_inventory.csv  
│   ├── file\_format\_report.csv  
│   ├── schema\_summary.csv  
│   ├── timestamp\_coverage\_report.csv  
│   ├── sampling\_interval\_report.csv  
│   ├── missing\_values\_report.csv  
│   ├── duplicate\_timestamp\_report.csv  
│   ├── sensor\_catalog.csv  
│   ├── signal\_classification.csv  
│   ├── zoro\_mvp\_readiness\_matrix.csv  
│   └── EDA\_SUMMARY.md  
│  
├── context\\  
│   ├── project\_overview.md  
│   ├── data\_source\_context.md  
│   ├── thesis\_context.md  
│   ├── notebooklm\_notes\_context.md  
│   ├── data\_inventory\_context.md  
│   ├── schema\_context.md  
│   ├── signal\_dictionary.md  
│   ├── physical\_system\_hypotheses.md  
│   ├── data\_quality\_context.md  
│   ├── zoro\_use\_case\_mapping.md  
│   ├── modeling\_readiness.md  
│   ├── open\_questions.md  
│   ├── decisions\_log.md  
│   ├── session\_log.md  
│   └── next\_steps.md  
│  
├── src\\  
│   └── zoro\_eda\\  
│       ├── \_\_init\_\_.py  
│       ├── io\_utils.py  
│       ├── csv\_dialect.py  
│       ├── profiling.py  
│       ├── time\_series.py  
│       ├── data\_quality.py  
│       ├── signal\_classification.py  
│       ├── physical\_mapping.py  
│       ├── visualization.py  
│       └── reporting.py  
│  
├── .venv\\  
├── requirements.txt  
├── README.md  
└── CLAUDE.md

If a folder already exists, reuse it.

Do not overwrite existing important files without asking.

---

## **5\. Python Environment Setup**

Create a project-specific Python virtual environment inside:

C:\\Users\\dellg\\OneDrive\\Documents\\ZE\\.venv

Use:

python \-m venv .venv

Activate on Windows PowerShell:

.\\.venv\\Scripts\\Activate.ps1

Activate on Windows Command Prompt:

.\\.venv\\Scripts\\activate.bat

After activation, upgrade pip:

python \-m pip install \--upgrade pip

Create and maintain:

requirements.txt

Whenever you install a package, update `requirements.txt` using:

pip freeze \> requirements.txt

---

## **6\. Initial Python Packages**

Install only practical EDA packages first:

pandas  
polars  
duckdb  
numpy  
matplotlib  
pyarrow  
tqdm  
charset-normalizer  
python-dateutil  
openpyxl

Suggested command:

pip install pandas polars duckdb numpy matplotlib pyarrow tqdm charset-normalizer python-dateutil openpyxl  
pip freeze \> requirements.txt

Ask before installing heavier packages such as:

scikit-learn  
xgboost  
lightgbm  
plotly  
seaborn  
great-expectations  
pandera  
tensorflow  
torch

Do not install ML packages until EDA confirms they are needed.

---

## **7\. Context Memory System**

Maintain a Kiro-style context system inside:

C:\\Users\\dellg\\OneDrive\\Documents\\ZE\\context

After each major task, update the relevant context files.

### **7.1 project\_overview.md**

Maintain:

* Project goal  
* ZORO Energy context  
* Dataset purpose  
* Current stage  
* Important constraints  
* Current conclusions

### **7.2 data\_source\_context.md**

Maintain:

* Project root path  
* Raw data folder path  
* Number of files  
* Total size  
* Known export format  
* Suspected source system  
* Known delimiter  
* Known schema pattern  
* Known timestamp format

### **7.3 thesis\_context.md**

Maintain:

* Important thesis sections  
* Important EnFa system descriptions  
* Energy system components  
* Variables mentioned in the thesis  
* Relevant figures/tables  
* Modeling equations connected to the dataset  
* Important assumptions from the thesis  
* How the thesis relates to the current CSV data

### **7.4 notebooklm\_notes\_context.md**

Maintain:

* Useful extracted notes from NotebookLM  
* But label them as secondary notes  
* Do not treat them as source of truth if they conflict with the PDF

### **7.5 data\_inventory\_context.md**

Maintain:

* Total files  
* File types  
* Largest files  
* Smallest files  
* Suspected groups of files  
* Any corrupt or unreadable files

### **7.6 schema\_context.md**

Maintain:

* Common column patterns  
* Detected delimiters  
* Timestamp columns  
* Value columns  
* Field columns  
* Measurement columns  
* Unexpected schemas  
* Encoding issues

### **7.7 signal\_dictionary.md**

Maintain a growing dictionary of signal names.

Use this format:

| Signal/File Name | German Meaning Hypothesis | English Meaning | Category | Unit Hypothesis | Confidence | Notes |  
|---|---|---|---|---|---|---|  
| V\_real\_maxVorlaufTemp | maximale Vorlauftemperatur | maximum supply temperature | HVAC / heating | °C | medium | Confirm using value range |

### **7.8 physical\_system\_hypotheses.md**

Maintain hypotheses about the building systems represented in the data:

* Heat pump  
* PV  
* Battery  
* Weather station  
* Thermal storage  
* Underfloor heating  
* BHKW/CHP  
* Building zones  
* Heating curves  
* Night setback  
* Defrost cycles  
* Forecast variables

### **7.9 data\_quality\_context.md**

Maintain:

* Missing data patterns  
* Duplicates  
* Gaps  
* Irregular sampling  
* Suspicious values  
* Constant-value signals  
* Outliers  
* Timezone issues  
* Files needing special handling

### **7.10 zoro\_use\_case\_mapping.md**

Maintain mapping from data to ZORO use cases.

Use this structure:

| ZORO Use Case | Required Signals | Available Signals | Quality | Readiness | Notes |  
|---|---|---|---|---|---|  
| HVAC optimization | indoor temp, outdoor temp, setpoints, supply temp, equipment state | TBD | TBD | TBD | TBD |

### **7.11 modeling\_readiness.md**

Maintain readiness for:

* Baseline energy modeling  
* Load forecasting  
* Indoor temperature forecasting  
* PV forecasting  
* Battery modeling  
* Heat pump COP estimation  
* MPC  
* EnergyPlus calibration  
* FDD  
* Predictive maintenance

### **7.12 open\_questions.md**

Maintain open questions.

Examples:

* What system exported these CSV files?  
* Are units documented anywhere?  
* Is there a BMS tag list?  
* Are these EnFa historical exports or current operational exports?  
* Are there control actions or only measured values?

### **7.13 decisions\_log.md**

Maintain decisions using this format:

| Date | Decision | Reason | Impact |  
|---|---|---|---|  
| YYYY-MM-DD | Use semicolon delimiter detection | CSV appears semicolon-separated | Prevents Excel-style misread |

### **7.14 session\_log.md**

After every session, append:

* What was done  
* Scripts created/modified  
* Reports generated  
* Main findings  
* Next step

### **7.15 next\_steps.md**

Maintain short, practical next actions.

---

## **8\. No Tag Dictionary Available**

There is currently no separate BMS tag list, Modbus register map, KNX group address list, or unit dictionary.

Therefore, signal interpretation must be inferred from:

1. File names  
2. `_measurement` values  
3. Value ranges  
4. Timestamp behavior  
5. Sampling frequency  
6. German keyword interpretation  
7. Thesis PDF context  
8. NotebookLM notes, if provided  
9. Physical building energy logic

Always classify signals with confidence levels:

High  
Medium  
Low  
Unknown

Do not invent units.

Use hypotheses such as:

Likely °C based on name and value range  
Likely seconds based on suffix Sek  
Likely control setpoint based on name and constant value behavior  
Likely weather forecast based on wind\_tomorrow naming

Record all assumptions in:

context/signal\_dictionary.md  
context/physical\_system\_hypotheses.md  
context/open\_questions.md

---

## **9\. German Signal Keyword Mapping**

Use this starting dictionary:

AT \= Außentemperatur / outdoor temperature  
Vorlauf \= supply / flow temperature  
Ruecklauf / Rücklauf \= return temperature  
Nachtabsenkung \= night setback  
WP \= Wärmepumpe / heat pump  
BHKW \= Blockheizkraftwerk / CHP  
PV \= photovoltaic  
SOC \= state of charge  
Speicher \= storage  
Puffer \= buffer tank  
Abtau \= defrost  
Hys \= hysteresis  
Temp \= temperature  
Max \= maximum  
Min \= minimum  
Sek \= seconds  
Timer \= schedule/timer  
Wind \= wind  
Wert \= value  
Ist \= actual  
Soll \= setpoint  
Real \= real/actual

---

## **10\. First Execution Plan**

Start with file inventory only.

Do not deeply analyze all data yet.

### **10.1 Create script**

Create:

scripts\\01\_scan\_files.py

The script must:

* Scan `C:\Users\dellg\OneDrive\Documents\ZE\data`  
* Count files  
* Calculate file sizes  
* Detect extensions  
* Save results to `reports\data_inventory.csv`  
* Save markdown summary to `context\data_inventory_context.md`  
* Print top 30 largest files  
* Print total size in GB  
* Print extension counts  
* Detect empty files  
* Detect suspicious non-CSV files

### **10.2 Output required**

Generate:

reports\\data\_inventory.csv  
context\\project\_overview.md  
context\\data\_source\_context.md  
context\\data\_inventory\_context.md  
context\\open\_questions.md  
context\\decisions\_log.md  
context\\session\_log.md  
context\\next\_steps.md  
requirements.txt  
README.md

Do not proceed to full schema detection until file inventory is complete.

If file inventory completes successfully and no major error exists, proceed automatically to schema detection.

---

## **11\. Second Execution Plan: CSV Dialect and Schema Detection**

Create:

scripts\\02\_detect\_schema.py

For each CSV file:

* Detect delimiter automatically:  
  * semicolon `;`  
  * comma `,`  
  * tab `\t`  
  * pipe `|`  
* Detect encoding:  
  * UTF-8  
  * UTF-8 with BOM  
  * Latin-1 if needed  
* Read only a sample first  
* Do not load entire file unless necessary  
* Detect column names  
* Detect whether all data appears in one column  
* Detect timestamp columns  
* Detect value columns  
* Detect `_measurement`  
* Detect `_field`  
* Detect numeric columns  
* Detect row count efficiently  
* Detect malformed rows  
* Detect decimal separator if relevant

If a file opens as one column in pandas, try semicolon delimiter.

If a file has headers like:

Unnamed: 0;\_time;\_value;\_field;\_measurement

then parse using `sep=";"`.

### **11.1 Output required**

Generate:

reports\\file\_format\_report.csv  
reports\\schema\_summary.csv  
reports\\sample\_rows\\  
context\\schema\_context.md  
context\\session\_log.md  
context\\next\_steps.md

For samples, save small files only:

reports\\sample\_rows\\\<safe\_file\_name\>\_sample.csv

Each sample should have max 20 rows.

---

## **12\. Third Execution Plan: Time-Series Profiling**

Create:

scripts\\03\_profile\_timeseries.py

For each file with timestamp data:

* Parse `_time`  
* Detect timezone  
* Detect start time  
* Detect end time  
* Estimate sampling interval  
* Detect duplicate timestamps  
* Detect missing timestamps or gaps  
* Detect number of rows  
* Detect monotonic ordering  
* Detect whether sorting is needed  
* Detect whether values are constant  
* Detect min/max/mean/std for numeric values  
* Detect suspicious physical values

Expected timestamp format may be:

2022-12-14T14:40:41Z

Interpret `Z` as UTC.

Do not convert timezone silently. If conversion is needed later for Germany, document it.

Be careful with daylight saving time.

### **12.1 Output required**

Generate:

reports\\timestamp\_coverage\_report.csv  
reports\\sampling\_interval\_report.csv  
reports\\duplicate\_timestamp\_report.csv  
reports\\missing\_values\_report.csv  
context\\data\_quality\_context.md  
context\\session\_log.md  
context\\next\_steps.md

---

## **13\. Fourth Execution Plan: Signal Classification**

Create:

scripts\\05\_classify\_signals.py

Use file names, `_measurement`, value ranges, and thesis context to classify each signal.

Categories:

* Weather  
* Weather forecast  
* Outdoor temperature  
* Wind  
* Solar irradiance  
* PV generation  
* Battery SOC  
* Battery power  
* Grid import/export  
* Electricity consumption  
* Heat pump  
* CHP/BHKW  
* Heating supply temperature  
* Heating return temperature  
* Cooling supply temperature  
* Thermal storage  
* Underfloor heating  
* Zone temperature  
* Indoor temperature  
* Room setpoint  
* HVAC setpoint  
* Valve position  
* Pump state  
* Fan state  
* Defrost  
* Night setback  
* Heating curve  
* Control parameter  
* Alarm/fault  
* Timer/schedule  
* Unknown

### **13.1 Output required**

Generate:

reports\\signal\_classification.csv  
reports\\sensor\_catalog.csv  
context\\signal\_dictionary.md  
context\\physical\_system\_hypotheses.md  
context\\session\_log.md  
context\\next\_steps.md

---

## **14\. Fifth Execution Plan: ZORO MVP Use-Case Mapping**

Generate:

reports\\zoro\_mvp\_readiness\_matrix.csv  
context\\zoro\_use\_case\_mapping.md  
context\\modeling\_readiness.md  
reports\\EDA\_SUMMARY.md

Evaluate readiness for:

Energy analytics  
HVAC optimization  
Load forecasting  
Indoor temperature forecasting  
MPC  
EnergyPlus calibration  
Fault detection  
PV forecasting  
Battery optimization  
Facility dashboard

Use this readiness scale:

Ready  
Partially ready  
Needs additional data  
Not enough evidence  
Not available

---

## **15\. Data Quality Checks**

For every important signal, check:

* Missing values  
* Long gaps  
* Duplicates  
* Irregular sampling  
* Constant values  
* Sudden jumps  
* Outliers  
* Negative values where impossible  
* Unrealistic temperatures  
* Unrealistic energy values  
* Timestamp disorder  
* Timezone inconsistency  
* Unit ambiguity  
* File naming inconsistency

Use rough sanity ranges:

Outdoor temperature: \-30°C to 50°C  
Indoor temperature: 10°C to 35°C  
Heating supply temperature: 20°C to 80°C  
Heating return temperature: 15°C to 70°C  
Cooling supply temperature: 4°C to 25°C  
Battery SOC: 0% to 100%  
PV power: \>= 0  
Energy meter cumulative values: usually non-decreasing  
Valve position: 0% to 100%  
Fan/pump state: often 0/1 or percentage

Do not mark data as wrong only because it violates these ranges. Mark it as suspicious and explain.

---

## **16\. ZORO MVP Interpretation Rules**

For every signal, ask:

1. What physical quantity could this represent?  
2. Is it measured, calculated, forecasted, or configured?  
3. What unit is likely?  
4. What building system does it belong to?  
5. Does it help us understand energy consumption?  
6. Does it help us understand comfort?  
7. Does it help us understand equipment behavior?  
8. Does it help forecasting?  
9. Does it help optimization?  
10. Does it help fault detection?  
11. Does it help EnergyPlus calibration?  
12. Does it help facility managers make decisions?

Then document the answer.

---

## **17\. MVP Path Evaluation**

Evaluate which ZORO MVP path is most feasible.

### **MVP Path A: Energy Analytics Dashboard**

Requires:

* Energy consumption  
* Weather  
* Time coverage  
* Basic system labels

### **MVP Path B: HVAC Optimization Advisory**

Requires:

* HVAC temperatures  
* Setpoints  
* Weather  
* Schedules  
* Energy consumption

### **MVP Path C: Heat Pump Performance and Fault Detection**

Requires:

* Heat pump states  
* Supply/return temperatures  
* Outdoor temperature  
* Defrost signals  
* Energy consumption

### **MVP Path D: Digital Twin / EnergyPlus Calibration**

Requires:

* Weather  
* Energy meter data  
* Building metadata  
* Schedules  
* System operation data

### **MVP Path E: Forecasting \+ MPC Readiness**

Requires:

* States  
* Controls  
* Disturbances  
* Constraints  
* Objective function data

Recommend the most realistic first MVP path based on actual data.

---

## **18\. Final EDA Summary Structure**

The final `reports\EDA_SUMMARY.md` must use this structure:

\# EnFa Data Analysis Summary for ZORO Energy

\#\# 1\. Executive Summary

\#\# 2\. Dataset Overview

\#\# 3\. File Inventory

\#\# 4\. CSV Format and Parsing Notes

\#\# 5\. Schema Summary

\#\# 6\. Time Coverage and Sampling

\#\# 7\. Data Quality Findings

\#\# 8\. Signal Classification

\#\# 9\. Physical System Interpretation

\#\# 10\. Thesis Context Connection

\#\# 11\. ZORO MVP Use-Case Readiness

\#\# 12\. Recommended First MVP Path

\#\# 13\. Modeling Opportunities

\#\# 14\. Missing Data and Risks

\#\# 15\. Recommended Next Steps

\#\# 16\. Appendix: Important Signal Dictionary

---

## **19\. First Message To User Before Execution**

When starting, say:

I will start by using C:\\Users\\dellg\\OneDrive\\Documents\\ZE as the project root. I will create the scaffold, set up a Python virtual environment, install only the initial EDA packages, and run a file inventory scan on the data folder. I will not modify the raw CSV files.

Then execute the first task.

---

## **20\. Important Warning**

Do not start machine learning yet.

The correct order is:

Inventory → Schema → Time-series quality → Signal classification → ZORO MVP mapping → Modeling readiness → Prototype

The first goal is understanding the data, not building models immediately.

## **Additional Execution Standards**

### **Implementation Technology Preferences**

Use Python as the main analysis language.

Prefer:

* `pathlib` for file paths  
* `pandas` for small-to-medium summaries  
* `polars` for larger CSV processing  
* `duckdb` for querying large local files efficiently  
* `numpy` for numerical operations  
* `matplotlib` for plots  
* `pyarrow` for Parquet support  
* `charset-normalizer` for encoding detection  
* `tqdm` for progress bars  
* `json`, `csv`, and `datetime` from the Python standard library where useful

Do not introduce heavy machine learning frameworks until the EDA proves they are needed.

Ask before installing:

* scikit-learn  
* xgboost  
* lightgbm  
* tensorflow  
* torch  
* great-expectations  
* pandera  
* plotly

### **Coding Standards**

All scripts must be:

* Safe for large files  
* Reproducible  
* Modular  
* Clearly commented  
* Able to run from the project root  
* Designed not to modify raw data  
* Able to save outputs into `reports`, `context`, `data/processed`, or `data/samples`

Every script should include:

if \_\_name\_\_ \== "\_\_main\_\_":  
    main()

Prefer command-line usage such as:

python scripts/01\_scan\_files.py \--raw-dir "C:\\Users\\dellg\\OneDrive\\Documents\\ZE\\data"

If a script creates or updates output files, log that action in:

context/session\_log.md

### **Reporting Style**

When reporting results to the user:

1. Start with the main conclusion.  
2. Explain what was analyzed.  
3. Mention which scripts and reports were generated.  
4. Summarize the important findings.  
5. Explain what the finding means for ZORO Energy.  
6. State the next recommended step.  
7. Do not paste large raw data into the response.

Use clear technical language. Do not oversimplify.

The user is technical and is trying to build a real AI-driven building energy optimization product.

### **How to Think Like a ZORO Data Scientist**

For every signal or file, ask:

1. What physical quantity could this represent?  
2. Is it measured, calculated, forecasted, or configured?  
3. What unit is likely?  
4. What building system does it belong to?  
5. Does it help understand energy consumption?  
6. Does it help understand comfort?  
7. Does it help understand equipment behavior?  
8. Does it help forecasting?  
9. Does it help optimization?  
10. Does it help fault detection?  
11. Does it help EnergyPlus calibration?  
12. Does it help facility managers make decisions?

Document these answers in:

context/signal\_dictionary.md  
context/physical\_system\_hypotheses.md  
context/zoro\_use\_case\_mapping.md  
context/modeling\_readiness.md

### **Final Deliverables Checklist**

By the end of the EDA phase, generate or update:

reports/data\_inventory.csv  
reports/file\_format\_report.csv  
reports/schema\_summary.csv  
reports/timestamp\_coverage\_report.csv  
reports/sampling\_interval\_report.csv  
reports/missing\_values\_report.csv  
reports/duplicate\_timestamp\_report.csv  
reports/signal\_classification.csv  
reports/sensor\_catalog.csv  
reports/zoro\_mvp\_readiness\_matrix.csv  
reports/EDA\_SUMMARY.md

context/project\_overview.md  
context/data\_source\_context.md  
context/thesis\_context.md  
context/notebooklm\_notes\_context.md  
context/data\_inventory\_context.md  
context/schema\_context.md  
context/signal\_dictionary.md  
context/physical\_system\_hypotheses.md  
context/data\_quality\_context.md  
context/zoro\_use\_case\_mapping.md  
context/modeling\_readiness.md  
context/open\_questions.md  
context/decisions\_log.md  
context/session\_log.md  
context/next\_steps.md

Do not mark the EDA complete until these deliverables are either created or explicitly marked as not applicable.

