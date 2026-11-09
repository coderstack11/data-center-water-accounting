# Water accounting model for US data-center growth

Code and data for the manuscript *A systems framework linking water accounting and management
for US data center growth* (under review).

The model estimates annual freshwater consumption associated with US data-center growth from
2023 to 2050 as the sum of three components:

- **on-site cooling water**, from a stock-turnover model of cooling technology classes with
  coupled water usage effectiveness (WUE) and power usage effectiveness (PUE);
- **electricity-generation water**, anchored to measured 2024 thermoelectric cooling water
  (EIA-923 Schedule 8D) on a data-center-weighted, load-serving basis and projected with
  EIA AEO2026 generation mixes;
- **chip-fabrication water**, covering ultrapure-water intake and the generation water of
  fabrication electricity.

IT electricity is held fixed across cooling comparisons, so a cooling technology's PUE
penalty is carried into generation water. Results are computed for every combination of
demand pathway, grid pathway, cooling deployment and electricity-attribution convention,
with hydropower-evaporation sensitivity bounds.

## Repository structure

```
run_all.py                      runs the whole pipeline
LICENSE                         MIT License for the code
code/
  lifecycle_water_model.py      the model; imported by every other script
  00_prepare_derived.py         raw data -> derived/ (state thermoelectric water, Aqueduct stress)
  01_extract_parameters.py      raw data -> extracted_parameters.csv, derived/model_parameters.json
  02_build_results_by_year.py   scenario results -> results_by_year_FINAL.xlsx
  03_make_main_tables.py        Tables 1-2 -> manuscript/main_tables.tex
  make_si_tables.py             Supplementary Tables S1-S11 -> supplementary/si_tables.tex
  make_figures_publication.py   Figs 1-4 -> figures/
  make_figures_si.py            Supplementary Figs S1-S9 -> figures/
  pubstyle.py                   shared figure style
data/                           raw input files, unchanged from their sources, and SHA256SUMS.txt
derived/                        intermediate datasets written by steps 00 and 01
extracted_parameters.csv        each data-derived parameter with its source file, column and formula
results_by_year_FINAL.xlsx      all scenario results, one sheet per year, plus reference sheets
DATA_PROVENANCE.md              source of every model parameter
```

The intermediate datasets and results included in the repository (`derived/`,
`extracted_parameters.csv`, `results_by_year_FINAL.xlsx`) are regenerated identically by the
pipeline. The LaTeX tables and the figures are created when the pipeline is run.

## System requirements

- **Operating system:** none specific. The code is plain Python with no operating-system-specific
  dependencies and runs on any system that supports Python 3.10 or later.
- **Software dependencies:** Python >= 3.10 with numpy >= 1.24, pandas >= 2.0, matplotlib >= 3.7
  and openpyxl >= 3.1 (`requirements.txt`). No other software is required.
- **Versions tested:** Python 3.13 with numpy 2.5.3, pandas 3.0.5, matplotlib 3.11.2 and
  openpyxl 3.1.5; Python 3.10 with numpy 1.24.4, pandas 2.0.3, matplotlib 3.7.5 and
  openpyxl 3.1.2. Both produce identical tables, parameters and results workbooks.
- **Hardware:** no non-standard hardware is required; a standard desktop or laptop computer
  is sufficient.

Figures use Times New Roman when it is installed and a metric-compatible serif font otherwise,
so their pixel dimensions can differ slightly between computers.

## Installation

1. Install Python 3.10 or later.
2. Download or clone this repository.
3. From the repository root (optionally inside a virtual environment), install the dependencies:

   ```
   pip install -r requirements.txt
   ```

Typical install time: about 1-2 minutes on a normal desktop computer.

## Demo

**Quick check** (a few seconds). From the repository root:

```
python code/lifecycle_water_model.py
```

Expected output:

```
parameters: derived/model_parameters.json (extracted from the raw files by 01_extract_parameters.py)

=== reference case: mid demand / warm-liquid adoption / reference grid ===
2027: total 0.613 Bm3  (generation 85.0%, site 14.4%, fab 0.68%)  I = 1.473 L/kWh
2030: total 0.942 Bm3  (generation 90.9%, site 8.4%, fab 0.72%)  I = 1.427 L/kWh
2040: total 1.107 Bm3  (generation 94.5%, site 4.8%, fab 0.77%)  I = 1.277 L/kWh
2050: total 1.354 Bm3  (generation 94.6%, site 4.5%, fab 0.91%)  I = 1.126 L/kWh
cumulative 2027-2050: 25.74 Bm3

=== grid water intensity, 2024, consumption basis [L/kWh] ===
  national (measured anchor)          : 1.46
  DC-weighted, Grubert-Sanders hydro  : 1.52
  DC-weighted, Macknick hydro (17)    : 2.19
  DC-weighted, hydro excluded         : 0.66

=== legacy dry chiller vs AI evaporative liquid-assist ===
  site water saved 0.59 L/kWh_IT ; PUE penalty 0.115
  break-even grid intensity I* = 5.13 L/kWh
```

**Full pipeline** (about 2-3 minutes on a normal desktop computer, of which the figures take
about 1 minute):

```
python run_all.py               # all steps, from the raw files in data/
python run_all.py --no-figures  # tables and results only
```

Expected output: the files in `derived/`, `extracted_parameters.csv` and
`results_by_year_FINAL.xlsx`, identical to the versions included in the repository; the LaTeX
tables `manuscript/main_tables.tex` (Tables 1-2) and `supplementary/si_tables.tex`
(Supplementary Tables S1-S11); and 26 figure files (PNG and PDF for Figs 1-4 and
Supplementary Figs S1-S9) in `figures/`.

## Running the model on other data or assumptions

**Custom scenarios.** The model is a Python module. From the repository root:

```python
import sys; sys.path.insert(0, 'code')
import lifecycle_water_model as M

r = M.run_case('high', 'adaptive_warm', 'accel', dry_scn='fast', attribution='average')
print(r[['year', 'E_dc_TWh', 'W_site_ML', 'W_grid_ML', 'W_fab_ML', 'W_total_ML']])
```

`run_case` returns one row per year from 2023 to 2050. Electricity is in TWh and water in ML
(million litres; divide by 10<sup>6</sup> for billion m<sup>3</sup>). Its arguments:

| Argument | Values |
|---|---|
| `demand_scn` | `'low'`, `'mid'`, `'high'` (LBNL 2025 Update 2030 anchors, then 2.0, 3.5 or 5.0% per year), or the structural forms `'share'`, `'satur'`, `'declin'`, `'capped'` |
| `cooling` | `'adaptive_warm'` (reference, warm-liquid adoption), `'adaptive_ferveret'` (two-phase immersion), `'adaptive_drychiller'` (legacy dry chiller), or a fixed fleet class from `M.COOLING` |
| `re_scn` | grid pathway: `'slow'`, `'ref'`, `'accel'` |
| `dry_scn` | advanced-cooling deployment tier: `'slow'`, `'base'`, `'fast'` |
| `attribution` | `'average'` (location-based), `'marginal_gas'`, `'marginal_coal'`, `'market'` |
| `hydro_alloc` | multiplier on the hydropower factor: `1.0` (Grubert-Sanders, central), `0.0` (excluded), `17/M.WF['hydro']` (Macknick median) |
| `cool_level`, `ai_level`, `leg_band` | `'lo'`, `'mid'`, `'hi'`: cooling WUE/PUE set, AI share of IT electricity in 2050, legacy-pool PUE in 2050 |

**Changing assumptions.** Scenario inputs are named constants in
`code/lifecycle_water_model.py`, for example `DEMAND` and `PUE_REF_ANCHORS` (demand),
`COOL_C3`, `ADOPT_TIER` and `AI_SHARE_ANCHORS` (cooling), `DC_WEIGHTS` and `STATE_MIX`
(data-center locations and state generation), and `KWH_PER_WAFER`, `ONSHORE_BAND` and
`TW_MIX_2024` (chip fabrication). Edit them and rerun `python run_all.py`.

**New input data.** Replace a file in `data/` with another release of the same layout and keep
its file name (or change the name where it is read in `00_prepare_derived.py`,
`01_extract_parameters.py` and the figure scripts), then rerun `python run_all.py`. Steps 00 and
01 re-derive the measured water factors, thermoelectric totals, state water and 2050 generation
mixes from the new files. For a base year other than 2024, also update the 2024 constants in
`lifecycle_water_model.py` (`MIX_2024`, `US_GEN_2024`, `STATE_GEN_TWH`, `STATE_GEN_SALES`,
`STATE_GEN_SALES_ALL`, `GAS_STEAM_SHARE`) and `STATE_GEN_TWH` in `00_prepare_derived.py`.

To keep a separate set of inputs, place them in `<folder>/data/` and set the environment
variable `PROJECT_ROOT=<folder>`; every script then reads from and writes to `<folder>`.
`FIGOUT` sets a different figure folder.

## Reproducing the manuscript

`python run_all.py` regenerates every table and figure of the manuscript and Supplementary
Information from the raw files in `data/`:

| Manuscript item | Produced by | Output |
|---|---|---|
| Tables 1-2 | `03_make_main_tables.py` | `manuscript/main_tables.tex` |
| Supplementary Tables S1-S11 | `make_si_tables.py` | `supplementary/si_tables.tex` |
| Figs 1-4 | `make_figures_publication.py` | `figures/fig1_*` to `figures/fig4_*` |
| Supplementary Figs S1-S9 | `make_figures_si.py` | `figures/figS1_*` to `figures/figS9_*` |
| Parameter provenance | `01_extract_parameters.py` | `extracted_parameters.csv` |
| All scenario combinations, 2023-2050 | `02_build_results_by_year.py` | `results_by_year_FINAL.xlsx` |

The LaTeX tables use the unit macros `\lkwh` (L kWh<sup>-1</sup>) and `\bmc` (billion m<sup>3</sup>)
defined in the manuscript.

## Data

| File in `data/` | Content | Source | Terms |
|---|---|---|---|
| `Cooling_Boiler_Generator_Data_Detail_2024.xlsx` | EIA-923 Schedule 8D cooling, boiler and generator detail, 2024 | [EIA thermoelectric cooling water data](https://www.eia.gov/electricity/data/water/) | US government work, public domain |
| `Narrative_Figures.xlsx` | AEO2026 narrative figure data (sheet `9_ElecGenMix`) | [EIA Annual Energy Outlook](https://www.eia.gov/outlooks/aeo/) | US government work, public domain |
| `Aqueduct40_baseline_annual_y2023m07d05.csv.zip`, `Aqueduct40_future_annual_y2023m07d05.csv.zip`, `Aqueduct40_README.xlsx` | WRI Aqueduct 4.0 baseline and future annual indicators and data dictionary | [WRI Aqueduct 4.0](https://www.wri.org/data/aqueduct-global-maps-40-data) | CC BY 4.0 |
| `cb_2024_us_state_20m.zip` | State boundaries for the Fig. 2 map | [US Census Bureau cartographic boundary files](https://www.census.gov/geographies/mapping-files/time-series/geo/cartographic-boundary.html) | US government work, public domain |
| `state_and_interconnection.csv` | State to synchronous-interconnection crosswalk | EPA eGRID | US government work, public domain |

The two Aqueduct CSV files are stored zipped because of their size (202 MB and 29 MB) and are
read directly from the zip archives. The archive members are byte-identical to the WRI files
(SHA-256 `fab1c0c29d98c74f0deff77eae66fda8bc78e0fde45ed13dbd6ecd4466434e23` and
`22145cec96b2088e3d54f6a12d3b2bcc885a43e69f5b7170bbf42ee9bb0653ce`). Checksums of every file
in `data/` are listed in `data/SHA256SUMS.txt`.

**Not redistributed.** The hydropower water factor comes from the Supporting Information
workbook `es8b00139_si_002.xlsx` (sheet `Hydropower`) of Grubert & Sanders (2018),
*Environmental Science & Technology* 52, 6695-6703,
[doi:10.1021/acs.est.8b00139](https://doi.org/10.1021/acs.est.8b00139). The two values used
(total consumption and intensity per GJ delivered) are recorded in `01_extract_parameters.py`.
To re-extract them, download the workbook from the article's Supporting Information and place
it in `data/`; step 01 then reads it and checks it against the recorded values. Outputs are
identical either way.

Literature and report values that are not read from a data file (LBNL, EPRI, TSMC, vendor and
corporate sources) are listed with their sources in `DATA_PROVENANCE.md` and in section D of
`extracted_parameters.csv`.

## Citation

Manuscript under review; citation details will be added on publication.

## License

The code is released under the MIT License (see `LICENSE`). Files in `data/` are third-party
data and remain under the terms of their original sources listed above.
