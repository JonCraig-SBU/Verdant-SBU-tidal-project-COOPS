# ADCP: Tidal Resource Assessment Workflow

This workspace contains notebooks, CSV outputs, and a classifier script used to process and analyze ADCP (Acoustic Doppler Current Profiler) velocity data for tidal resource assessment.

## What is in this folder

- Notebook-driven analysis pipeline for:
  - ADCP data import and reshaping
  - Orientation correction
  - Principal flood/ebb direction estimation
  - Ebb/flood/slack phase labeling
  - Tidal-cycle and turbulence/intensity analysis
  - Annual Energy Production (AEP) estimation from depth-dependent ADCP data
- Reusable Python script:
  - `ebbFloodClassifier.py` for phase classification from depth-averaged velocity time series
- Input and derived data files (`input/*.csv`, `*.csv`)

## Project structure

- `input/`
  - Raw or source files used by notebooks and scripts
  - Includes annual CSVs and `RC.nc`
- `coops-data.ipynb`
  - CO-OPS related data handling
- `dataframe-from-ADCP.ipynb`
  - Build/clean ADCP dataframe
- `orientation-correction.ipynb`
  - Velocity orientation/correction steps
- `principal_flood_ebb_calculation.ipynb`
  - Compute principal axis and flood/ebb bearings
- `label_df-depthDep.ipynb`
  - Label depth-dependent records
- `ebbFloodClassifier.ipynb`
  - Notebook form of phase classifier workflow
- `ebbFloodClassifier.py`
  - Script version of ebb/flood/slack classification
- `profiles.ipynb`
  - Profile-level exploration
- `TI-calculator.ipynb`
  - Turbulence intensity calculations
- `tidal-cycles.ipynb`
  - Tidal-cycle segmentation and analysis
- `adcp_aep_pcu_iec.ipynb`
  - AEP estimation using principal component velocity (PCU) and the IEC bin-sum method
  - Uses hub-bin speed `V_hub(t) = |PCU(t, hub_bin)|` as the turbine inflow input
  - Computes single-turbine and farm AEP, velocity PDFs, and ebb/flood bin probabilities
- Input and output CSV examples:
  - `depthAvg_ADCPdata.csv`
  - `depthAvg_ADCPdata_labeled.csv`
  - `depthDep_ADCPdata.csv` (input to `adcp_aep_pcu_iec.ipynb`)
  - `depth_dependent_velocity_components.csv`
  - `power_curve_generated.csv` (turbine power curve for AEP)
  - `site_probabilities_ebb_flood.csv` (ebb/flood IEC bin probabilities from AEP notebook)

## Quick start

1. Create and activate a Python environment (recommended).
2. Install core packages:

```bash
pip install numpy pandas matplotlib scipy jupyter
```

3. Open notebooks in VS Code or Jupyter and run cells in order.
4. Or run the classifier script directly:

```bash
python ebbFloodClassifier.py
```

## `ebbFloodClassifier.py` usage

Default behavior:

- Input CSV: `depthAvg_ADCPdata.csv`
- Time column: `Date & Time.2`
- East/North columns: `Eas`, `Nor`
- Floodward bearing: `252.38` degrees True
- Slack threshold: `+-0.4 m/s` 
- Smoothing window: `3` samples
- Output: `depthAvg_ADCPdata_labeled.csv`

Examples:

```bash
python ebbFloodClassifier.py --plot
python ebbFloodClassifier.py mydata.csv --time-col "DateTime" --east-col "U_east" --north-col "U_north"
python ebbFloodClassifier.py data.csv --floodward-bearing 88
python ebbFloodClassifier.py data.csv --estimate-axis
python ebbFloodClassifier.py data.csv --ebbward-bearing 268
python ebbFloodClassifier.py data.csv --thr 0.1 --smooth-n 5
```

## Notes

- Units are expected in m/s; the script includes a heuristic conversion when values appear to be in mm/s.
- Keep intermediate and final CSV outputs in this folder for notebook compatibility unless you also update paths in notebooks.

## `adcp_aep_pcu_iec.ipynb` usage

Main inputs (set at the top of the notebook):

- `depthDep_ADCPdata.csv` — depth-dependent ADCP velocity data
- `power_curve_generated.csv` — turbine power curve (`speed_mps`, `power_kw`)
- `HUB_BIN` — 1-based ADCP bin index at turbine hub height (default: 29)

Workflow inside the notebook:

1. Parse ADCP velocities into `u(t, bin)` and `v(t, bin)`.
2. Compute principal axis and PCU (principal component velocity) per bin.
3. Extract hub-bin speed `V_hub` from PCU.
4. Apply IEC bin-sum AEP: histogram of `V_hub`, weighted by turbine power curve.
5. Export bin-level contributions (`aep_bins_hub.csv`) and ebb/flood probabilities (`site_probabilities_ebb_flood.csv`).
6. Scale single-turbine AEP to farm size (`N_TURBINES`).

Key parameters: `BIN_WIDTH` (m/s), `PRATED_KW`, `CUT_IN` / `CUT_OUT` / `RATED_SPEED`, `USE_DEPTH_AVERAGE_FOR_PCA`.

## Suggested workflow

1. Prepare/import raw data in notebook(s).
2. Apply orientation correction.
3. Estimate or set flood/ebb axis.
4. Run phase labeling (`ebbFloodClassifier.py` or notebook equivalent).
5. Continue with depth-dependent, profile, and tidal-cycle analyses.
6. Estimate AEP with `adcp_aep_pcu_iec.ipynb` once `depthDep_ADCPdata.csv` and a power curve are available.
