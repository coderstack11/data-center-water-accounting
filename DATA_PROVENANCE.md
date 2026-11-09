# Data provenance

Every model parameter traces to one of the sources below. Items marked **[scenario]** are
explicit modelling assumptions with no published source and are carried as sensitivity bands.

## Demand, PUE, AI share, accelerators
- **LBNL 2025 Update** — Smith, S.J., Hubbard, A., Newkirk, A., Ganeshalingam, M., Holecek, B.,
  Sartor, D., Mills, M., Shehabi, A. (2026). *United States Data Center Energy Usage Report:
  2025 Update.* LBNL-2001758. DOI 10.71468/P1RP4F. CC BY 4.0.
  Used for: 2024 electricity (192 TWh); 2028 (464); 2030 scenarios (521/649/843); aggregate
  PUE (1.45 → 1.36); AI facility PUE (1.145 → 1.136); AI share of data-centre energy (55% in
  2030); accelerator shipments (7.0 M in 2024, 19 M in 2030); accelerator lifetime (5 yr).
  Note: this report contains no water estimates.
- **LBNL 2024** — Shehabi, A. *et al.* (2024). LBNL-2001637.
  Used for: fleet WUE anchors (0.36 in 2023; 0.45–0.48 projected for 2028). Not superseded on
  water by the 2025 Update.
- **EPRI (2026)** — *Powering Intelligence*, report 3002034696.
  Used for: the fifteen-state distribution of data-centre load only.

## Generation water
- **EIA-923 Schedule 8D, 2024 final release** (`Cooling_Boiler_Generator_Data_Detail_2024.xlsx`)
  — plant/cooling-system monthly cooling water, de-duplicated to one water record per plant
  cooling system and month; yields the measured consumptive and withdrawal factors and the
  state gas-steam shares.
- **Grubert & Sanders (2018)**, *Environ. Sci. Technol.* 52, 6695–6703 — hydropower reservoir
  evaporation, economic allocation (9.53 L/kWh central), from sheet `Hydropower` of the
  article's Supporting Information workbook `es8b00139_si_002.xlsx` (not redistributed; see README).
- **Macknick et al. (2012)**, *Environ. Res. Lett.* 7, 045802 — non-thermal literature factors
  and the hydropower sensitivity bound (17 L/kWh median).
- **EIA AEO2026** Narrative Figures, sheet `9_ElecGenMix` — 2050 generation mix by case;
  also the 2050 national generation total (6,273 TWh, Counterfactual Baseline) used to express
  demand pathways as a share of national electricity.
- **EIA State Electricity Profiles 2024** — state net generation and retail sales, used for the
  self-supply fractions behind the consumption-basis intensity.
- **State–interconnection crosswalk** (`state_and_interconnection.csv`, EPA eGRID) — synchronous
  interconnection membership used to define the import pools of the consumption-basis intensity.
- **EIA FAQ** — transmission and distribution losses (4.8%).

## Cooling technology
- **ASHRAE TC 9.9**, *Liquid Cooling Guidelines for Datacom Equipment Centers* and
  *Thermal Guidelines for Data Processing Environments*, 5th ed. (2021) — facility water
  temperature classes W17/W27/W32/W40/W45/W+; W45 (supply water up to 45 °C) is the
  dry-cooler band and defines the warm-liquid class used here.
- Vendor and press documentation of warm-liquid and two-phase immersion systems — technology
  existence and order-of-magnitude performance only; the PUE values are reconciled with the
  LBNL measured figure rather than taken from vendor claims.
- **Amazon (2024)** water-positive reporting — WUE 0.15 L/kWh, used as the legacy-pool
  modernisation target.

## Chip fabrication
- **TSMC 2024 sustainability and annual reporting** — total energy 27,456 GWh (≈93% purchased
  electricity); 12.9 M 12-inch-equivalent wafers shipped; 37.1 kWh per 12-inch-equivalent wafer
  mask layer; net ultrapure-water intensity and recycling rates.
- **Taiwan Ministry of Economic Affairs, Energy Administration** — 2024 national generation mix
  (gas 42.45%, coal 39.27%, renewables 11.55%, nuclear 4.22%, oil 1.45%, pumped hydro 1.07%).
  No measured Taiwanese cooling-water survey exists; the offshore grid factor is therefore a
  band (0.32–1.36 L/kWh) whose lower bound treats coastal thermal plants as seawater
  once-through cooled.
- **[scenario]** onshore fabrication share (2% → 10 / 25 / 40% by 2050). Anchors that do exist:
  TSMC Arizona Fab 1 entered volume production of 4 nm in Q4 2024, and TSMC has announced
  ~US$165 bn of US investment across six planned fabs. No published projection supports a 2050
  share, so this is carried as a scenario band.

## Water scarcity
- **WRI Aqueduct 4.0** (2023-07-05 release, CC BY 4.0; `Aqueduct40_baseline_annual_y2023m07d05.csv`
  and `Aqueduct40_future_annual_y2023m07d05.csv`, stored zipped, with the data dictionary
  `Aqueduct40_README.xlsx`) — baseline and future annual indicators
  at HydroBASINS level-6 sub-basins, aggregated to states by area weighting. Fields used:
  `bws_score` (baseline water stress), `w_awr_elp_tot_score` (electric-power sector weighted
  risk), and `bau30/bau50/opt50/pes50_ws_x_s` (projected stress).

## Maps
- **US Census Bureau** cartographic boundary file `cb_2024_us_state_20m.zip` — state outlines
  for the Fig. 2 map.

## Comparison
- **Xiao, T. et al. (2025)**, *Nat. Sustain.* 8, 1541–1553, and the associated public repository
  `PEESEgroup/US-AI-Server-Analysis` — used only to populate the comparison table, not as a
  parameter source. Their state-level WUE (1.62–1.82 L/kWh, falling to ~1.48 with advanced
  liquid cooling) differs from the LBNL-calibrated values used here and the difference is
  reported explicitly.

## Boundaries
- **USGS Circular 1441** (Dieter et al., 2018) — national consumptive water use context.
- **Microsoft (2024)**, **Amazon (2026)** — corporate water-positive methodologies.
- **Brander et al. (2018)**, **Bjørn et al. (2022)** — market- versus location-based accounting.
