#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Water accounting model for US data-center growth, 2023-2050
===========================================================
Annual water use is the sum of three components, evaluated for each combination of
demand scenario, cooling pathway, grid pathway and accounting convention:

  (1) On-site cooling water, W_site = WUE x E_IT.  Cooling technology classes carry
      coupled (WUE, PUE) values and enter the installed base through a stock-turnover
      model, so that dry heat rejection carries its electricity (PUE) penalty into
      generation water.
  (2) Electricity-generation water, W_grid = E_dc x I.  The 2024 level of I is anchored
      to measured EIA-923 Schedule 8D thermoelectric water on a data-center-weighted,
      consumption (load-serving) basis; the 2024-2050 trajectory follows per-technology
      water factors applied to the generation mix, interpolated to EIA AEO2026 2050
      endpoints (slow / reference / accelerated renewable growth).
  (3) Chip-fabrication water, W_fab: ultrapure-water intake per wafer, linked to
      AI-accelerator shipments, plus the generation water of fabrication electricity;
      onshore/offshore split.

Functional unit: IT electricity is held fixed across cooling comparisons,
E_IT = E_dc_proj / PUE_ref and E_dc = PUE_fleet x E_IT.

Extends the framework of Xiao et al. (Nature Sustainability 8, 1541-1553, 2025).
Data-derived parameters are read at run time from derived/model_parameters.json,
written by 01_extract_parameters.py from the raw files in data/; the in-code constants
are the same values, kept as a documented fallback.  Hard-coded literature values carry
an inline [source] tag.  Units are stated per line.
Water = CONSUMPTION (not withdrawal) unless noted.
"""

import numpy as np
import pandas as pd

YEARS = np.arange(2023, 2051)                     # 2023..2050 inclusive (energy mix native to 2050; demand CAGR-extended)
GAL_TO_L = 3.78541                                # 1 US gallon = 3.78541 L
def galMWh_to_LkWh(x): return x * GAL_TO_L / 1000.0   # gal/MWh -> L/kWh

# =====================================================================
# MODULE A | DATA-CENTER ELECTRICITY DEMAND  E_dc_proj(t)  [TWh/yr]
# ---------------------------------------------------------------------
# E_dc_proj is TOTAL facility electricity (incl. cooling) at the aggregate PUE_ref.
# Anchored to the LBNL 2025 Update (Smith et al. 2026, LBNL-2001758):
#   2023 = 168 TWh   [implied by "14% increase 2023->2024" with 2024 = 192]
#   2024 = 192 TWh   (4.7% of US electricity)                        [LBNL 2025 Update, S.2]
#   2028 = 464 TWh   Reference Case.  The low and high pathways use 464 scaled by the ratio
#                    of their 2030 anchor to 649 (a model construction, not a published value).
#   2030 = 521 / 649 / 843 TWh
#        low  = Compounded Uncertainty low   (9.5% of US electricity)
#        ref  = Reference Case               (11.8%)
#        high = Compounded Uncertainty high  (15.3%)
#   Post-2030 CAGR 2.0 / 3.5 / 5.0 %/yr is OUR extrapolation (LBNL stops at 2030).
#   NOTE: LBNL's own 2024->2030 Reference CAGR is 21%/yr; the deceleration assumed at
#   2030 is a modelling choice, made explicit here and tested by the structural
#   scenarios in STRUCTURAL_DEMAND below.
#
# PUE_ref(t): the aggregate PUE embedded in the demand projection.
#   LBNL 2025 Update S.3.6: national aggregate PUE 1.45 (2024) -> 1.36 (2030).
#   No published value beyond 2030 -> held constant at 1.36 (stated assumption).
#   E_IT = E_dc_proj / PUE_ref   then   E_dc = PUE_fleet * E_IT   (fixed-IT functional unit).
LBNL_2023, LBNL_2024, LBNL_2028_CHECK = 168.0, 192.0, 464.0
PUE_REF_ANCHORS = [(2023, 1.46), (2024, 1.45), (2030, 1.36), (2050, 1.36)]
def pue_ref_path():
    xs=[a for a,_ in PUE_REF_ANCHORS]; ys=[b for _,b in PUE_REF_ANCHORS]
    return np.interp(YEARS, xs, ys).astype(float)
PUE_REF_PATH = pue_ref_path()
PUE_REF = float(PUE_REF_PATH[1])                  # scalar alias = 2024 value

DEMAND = {                                        # (E2030 TWh, CAGR 2030-2050)
    'low':  (521, 0.020),
    'mid':  (649, 0.035),
    'high': (843, 0.050),
}
# Structural post-2030 forms. All share the same 2030 anchor
# as 'mid' (649 TWh) and differ ONLY in functional form after 2030.
#   share  : data centres stop gaining share of national electricity (LBNL 2030 share held)
#   satur  : logistic saturation toward a ceiling set by LBNL's high 2030 share
#   declin : growth rate decays exponentially from its 2030 value to the grid growth rate
#   capped : interconnection-constrained; capacity additions fall to a fixed GW/yr
US_GEN_2050 = 6273.0        # AEO2026 Counterfactual Baseline total US generation, TWh
US_GEN_2030 = 5500.0        # NERC 2025 LTRA-consistent interpolation used by LBNL for the 11.8% share
STRUCTURAL_DEMAND = ('share', 'satur', 'declin', 'capped')

def demand_path(scn):
    """Total facility electricity E_dc_proj(t) [TWh] for a demand scenario."""
    if scn in STRUCTURAL_DEMAND:
        return _structural_demand(scn)
    E2030, g = DEMAND[scn]
    E = np.zeros_like(YEARS, dtype=float)
    for i, t in enumerate(YEARS):
        if t <= 2024:
            E[i] = LBNL_2023 + (LBNL_2024-LBNL_2023)*(t-2023)        # 2023->2024 linear
        elif t <= 2028:
            E2028 = LBNL_2028_CHECK*(E2030/DEMAND['mid'][0])         # LBNL 2028 Reference, scaled by scenario
            r = (E2028/LBNL_2024)**(1/4)                             # 2024->2028 geometric (front-loaded, per LBNL)
            E[i] = LBNL_2024 * r**(t-2024)
        elif t <= 2030:
            E2028 = LBNL_2028_CHECK*(E2030/DEMAND['mid'][0])
            r = (E2030/E2028)**(1/2)                                 # 2028->2030 geometric
            E[i] = E2028 * r**(t-2028)
        else:
            E[i] = E2030 * (1+g)**(t-2030)                           # our CAGR extrapolation
    return E

def _structural_demand(kind):
    """Post-2030 structural alternatives to perpetual CAGR (all anchored at 649 TWh in 2030)."""
    base = demand_path('mid'); E = base.copy()
    i30 = list(YEARS).index(2030); E30 = base[i30]
    us_growth = (US_GEN_2050/US_GEN_2030)**(1/20) - 1.0              # ~0.66%/yr national growth
    if kind == 'share':          # share of national electricity frozen at the LBNL 2030 value
        for i, t in enumerate(YEARS):
            if t > 2030: E[i] = E30 * (1+us_growth)**(t-2030)
    elif kind == 'satur':        # logistic; ceiling = LBNL high 2030 share (15.3%) of 2050 US generation
        K = 0.153*US_GEN_2050
        k = 0.16
        for i, t in enumerate(YEARS):
            if t > 2030:
                E[i] = K/(1 + (K/E30 - 1)*np.exp(-k*(t-2030)))
    elif kind == 'declin':       # growth rate decays exponentially toward national grid growth
        g0 = 0.035; lam = 0.12
        for i, t in enumerate(YEARS):
            if t > 2030:
                yrs = np.arange(2031, int(t)+1)
                gs = us_growth + (g0-us_growth)*np.exp(-lam*(yrs-2030))
                E[i] = E30*np.prod(1+gs)
    elif kind == 'capped':       # interconnection-constrained capacity additions
        # LBNL: 148 GW interconnection capacity in 2030 at 50% utilisation.
        # Post-2030 additions fall from 17.4 GW/yr (2024-2030 average) to 8 GW/yr.
        add_gw = 8.0
        twh_per_gw = E30/148.0
        for i, t in enumerate(YEARS):
            if t > 2030: E[i] = E30 + add_gw*twh_per_gw*(t-2030)
    return E

# =====================================================================
# MODULE C | GRID WATER INTENSITY  I_grid(t)  [L/kWh]  (bottom-up)
# ---------------------------------------------------------------------
# Per-technology water factors, L/kWh.
# THERMAL factors are MEASURED from EIA-923 Schedule 8D cooling-water detail, 2024: water is
# de-duplicated to one record per plant cooling system and month, generation to one record
# per generator and month.
# Non-thermal technologies report no cooling water.  Hydropower uses the Grubert & Sanders
# (2018) economic allocation of reservoir evaporation (central); hydro_alloc scales it for
# the sensitivity bounds (0 = excluded; 17/WF['hydro'] = Macknick et al. 2012 median).
# Wind ~0; solar PV panel washing and geothermal from Macknick et al. (2012).
WF = {                              # CONSUMPTION, L/kWh  (measured thermal; literature non-thermal)
    'gas_cc':   0.6576, # NG combined cycle  [EIA 2024 measured]
    'gas_other':2.7751, # NG steam turbine   [EIA 2024 measured]
    'coal':     1.6773, # conventional steam coal [EIA 2024 measured]
    'nuclear':  1.377,  # nuclear [EIA 2024 measured]
    'hydro':    9.5309, # reservoir evaporation, economic allocation, CENTRAL [Grubert & Sanders 2018, ES&T; 2.647 m3/GJ]
                        #   Macknick 2012 median 17 (n=3, excluded from their figures); range 5.4-68 -> hydro_alloc sensitivity
    'wind':     0.0,
    'solar':    0.10,   # utility PV panel washing [Macknick 2012]
    'geo':      5.30,   # geothermal [Macknick 2012]
    'bio':      3.1721, # wood/biomass [EIA 2024 measured]
    'other':    3.00,
}
WF_WITH = {                          # WITHDRAWAL, L/kWh (measured thermal; hydropower withdrawal = consumption)
    'gas_cc':7.854,'gas_other':225.119,'coal':84.8844,'nuclear':95.2703,'hydro':9.5309,
    'wind':0.0,'solar':0.0,'geo':5.0,'bio':42.886,'other':64.0,
}
# Directly-measured 2024 national thermoelectric totals (empirical anchors, billion m3):
W_THERMAL_2024_CONS = 3.552         # billion m3  [EIA 2024 Sch.8D, dedup]
W_THERMAL_2024_WITH = 172.855       # billion m3  [EIA 2024 Sch.8D, dedup]

# --- data-derived parameters written by 01_extract_parameters.py ----------------------
# If derived/model_parameters.json is present (produced by STEP 01 from the raw files), the
# thermal water factors, hydro factor, thermal totals and 2050 generation mixes are taken from
# it at run time.  The constants in this file are the same values, kept as a documented fallback.
import os as _os, json as _json
# Project root = the directory that holds code/, data/ and derived/ (override with PROJECT_ROOT).
ROOT = _os.environ.get('PROJECT_ROOT',
                       _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
_PJSON = _os.path.join(ROOT, 'derived', 'model_parameters.json')
if _os.path.exists(_PJSON):
    with open(_PJSON, encoding='utf-8') as _fh: _P=_json.load(_fh)
    WF.update(_P.get('WF_thermal_consumption',{}))
    WF_WITH.update(_P.get('WF_thermal_withdrawal',{}))
    if 'WF_hydro_consumption' in _P: WF['hydro']=WF_WITH['hydro']=_P['WF_hydro_consumption']
    W_THERMAL_2024_CONS=_P.get('thermal_consumption_2024_Bm3',W_THERMAL_2024_CONS)
    W_THERMAL_2024_WITH=_P.get('thermal_withdrawal_2024_Bm3',W_THERMAL_2024_WITH)
    PARAMS_SOURCE='derived/model_parameters.json (extracted from the raw files by 01_extract_parameters.py)'
else:
    PARAMS_SOURCE='in-code constants (run 01_extract_parameters.py to regenerate derived/model_parameters.json)'

# 2024 US generation shares -- REAL [EIA Electric Power Monthly/Annual 2024; Ember 2024; total 4,304 TWh]
MIX_2024 = {'gas_cc':0.347,'gas_other':0.081,'coal':0.149,'nuclear':0.178,
            'hydro':0.056,'wind':0.102,'solar':0.070,'geo':0.004,'bio':0.011,'other':0.002}

# 2050 generation shares -- native EIA AEO2026 endpoints (Narrative Figures, sheet 9_ElecGenMix):
#   ref = Counterfactual Baseline, accel = Low Oil and Gas Supply, slow = High Oil and Gas Supply.
# STEP 01 maps the AEO categories to model buckets; the values below are its output (fallback).
MIX_2050 = {
  'ref':   {'gas_cc':0.3314,'gas_other':0.0777,'coal':0.0008,'nuclear':0.1278,'hydro':0.0496,
            'bio':0.0097,'geo':0.0035,'wind':0.2299,'solar':0.1695,'other':0.0},
  'accel': {'gas_cc':0.1506,'gas_other':0.0353,'coal':0.0078,'nuclear':0.151,'hydro':0.0653,
            'bio':0.0128,'geo':0.0046,'wind':0.364,'solar':0.2086,'other':0.0},
  'slow':  {'gas_cc':0.4458,'gas_other':0.1046,'coal':0.0008,'nuclear':0.1227,'hydro':0.0487,
            'bio':0.0096,'geo':0.0035,'wind':0.1291,'solar':0.1353,'other':0.0},
}
BASE_YEAR_MIX = MIX_2024                           # alias used below
# override 2050 mix with AEO2026-derived native endpoint if provided by STEP 01
if _os.path.exists(_PJSON):
    with open(_PJSON, encoding='utf-8') as _fh: _Pm=_json.load(_fh)
    if 'MIX_2050' in _Pm:
        for _scn in MIX_2050:
            if _scn in _Pm['MIX_2050']: MIX_2050[_scn]=_Pm['MIX_2050'][_scn]
TD_LOSS = 0.048                                   # transmission+distribution loss [EIA 2023: 4.6-5%]
GROSSUP = 1.0/(1.0-TD_LOSS)                        # deliver 1 kWh -> generate 1.048 kWh

def mix_path(re_scn):
    """Linear interpolation of national generation shares 2024->2050, renormalised each year."""
    keys = list(BASE_YEAR_MIX.keys())
    out = {k: np.zeros_like(YEARS, dtype=float) for k in keys}
    for i, t in enumerate(YEARS):
        w = max(0.0, (t-2024)/(2050-2024))            # 2023 clamped to 2024 base
        s = {k: (1-w)*BASE_YEAR_MIX[k] + w*MIX_2050[re_scn][k] for k in keys}
        tot = sum(s.values())
        for k in keys: out[k][i] = s[k]/tot
    return out

def grid_intensity(re_scn, hydro_alloc=1.0, basis='consumption', anchor='measured'):
    """National grid water intensity, L per kWh delivered.

    anchor='measured' (default): the 2024 level is set by the measured EIA-923
    thermoelectric total plus factor-based non-thermal water, and the 2024-2050 shape
    is taken from the factor method as a RATIO.  anchor='factor' returns the
    all-factor construction, retained for comparison.
    """
    I_fac = _grid_intensity_factor(re_scn, hydro_alloc, basis)
    if anchor != 'measured':
        return I_fac
    i24 = list(YEARS).index(2024)
    return I_fac/I_fac[i24]*measured_I_2024(hydro_alloc, basis)

# Which 2024 level anchors the electricity that DATA CENTRES draw.  'dc' uses the
# load-weighted consumption-basis intensity across the fifteen EPRI states (renormalised
# to 100% of load); 'national' uses the national average.  Data centres are strongly
# concentrated and their host states import electricity, so the load-weighted value is
# the more faithful anchor; the national value is retained as a sensitivity.
GRID_ANCHOR_FOR_DC = 'dc'

def dc_intensity_path(re_scn, hydro_alloc=1.0, basis='consumption', anchor=None):
    """Grid intensity serving data-centre load, L/kWh, 2024-2050."""
    I = grid_intensity(re_scn, hydro_alloc, basis)
    if (anchor or GRID_ANCHOR_FOR_DC) != 'dc' or basis != 'consumption':
        return I
    i24 = list(YEARS).index(2024)
    tw = sum(DC_WEIGHTS.values())
    base = sum(w*state_intensity_consumption(st, hydro_alloc)
               for st, w in DC_WEIGHTS.items())/tw
    return I/I[i24]*base

def _grid_intensity_factor(re_scn, hydro_alloc=1.0, basis='consumption'):
    """National-average I_grid(t) [L/kWh]. basis='consumption' or 'withdrawal'."""
    mix = mix_path(re_scn); factors = WF if basis=='consumption' else WF_WITH
    I = np.zeros_like(YEARS, dtype=float)
    for i in range(len(YEARS)):
        s = sum((factors[k]*hydro_alloc if k == 'hydro' else factors[k])*mix[k][i] for k in factors)
        I[i] = s*GROSSUP
    return I

# --- electricity ATTRIBUTION framings (how DC load is assigned a generation water factor) ---
# 'average'      : location-based average grid mix (PRIMARY; physical water at plants serving the load)
# 'market'       : market-based / 100% renewable PPA claim (corporate accounting; ~wind+solar)
# 'marginal_gas' : consequential, gas combined-cycle on the margin
# 'marginal_coal': consequential, coal kept online on the margin (upper bound)
def attribution_intensity(attribution, re_scn='ref', hydro_alloc=1.0):
    if attribution == 'average':
        return grid_intensity(re_scn, hydro_alloc)
    if attribution == 'market':        # 100% wind/solar PPA matching
        val = (0.5*WF['wind'] + 0.5*WF['solar'])*GROSSUP
    elif attribution == 'marginal_gas':
        val = WF['gas_cc']*GROSSUP
    elif attribution == 'marginal_coal':
        val = WF['coal']*GROSSUP
    else:
        raise ValueError(attribution)
    return np.full(len(YEARS), val, float)

# ---- data-center LOCATION weighting ------------------------------------------
# DC-location weights: the 15-state set and its ~80% share of national data-center load are from
# EPRI "Powering Intelligence" (2026); Virginia dominant (only state >20% of its own electricity).
# Within-set shares are approximated (EPRI Fig.1 is graphical).  They sum to 0.80 and are
# renormalised to 1 wherever a load-weighted average across the fifteen states is taken.
DC_WEIGHTS = {'VA':0.235,'TX':0.105,'CA':0.075,'IL':0.052,'OR':0.047,'AZ':0.043,'IA':0.038,
              'GA':0.036,'WA':0.033,'PA':0.028,'NY':0.026,'NJ':0.024,'NE':0.021,'ND':0.019,'NV':0.018}
# State generation mixes (fractions) -- REAL, EIA State Electricity Profiles 2023/2024 (rounded)
STATE_MIX = {  # gas_cc, coal, nuclear, hydro, wind, solar, geo, bio, other  (gas_other folded into gas_cc)
 'VA':{'gas_cc':0.55,'coal':0.02,'nuclear':0.30,'hydro':0.01,'wind':0.00,'solar':0.06,'bio':0.03,'other':0.03},
 'TX':{'gas_cc':0.44,'coal':0.13,'nuclear':0.08,'hydro':0.002,'wind':0.24,'solar':0.09,'other':0.008},
 'CA':{'gas_cc':0.40,'coal':0.00,'nuclear':0.09,'hydro':0.10,'wind':0.07,'solar':0.19,'geo':0.05,'bio':0.03,'other':0.07},
 'IL':{'gas_cc':0.20,'coal':0.12,'nuclear':0.52,'hydro':0.00,'wind':0.12,'solar':0.02,'other':0.02},
 'OR':{'gas_cc':0.22,'coal':0.03,'nuclear':0.00,'hydro':0.50,'wind':0.14,'solar':0.04,'other':0.07},
 'AZ':{'gas_cc':0.42,'coal':0.11,'nuclear':0.28,'hydro':0.05,'wind':0.00,'solar':0.11,'other':0.03},
 'IA':{'gas_cc':0.12,'coal':0.20,'nuclear':0.03,'hydro':0.00,'wind':0.62,'solar':0.02,'other':0.01},
 'GA':{'gas_cc':0.45,'coal':0.12,'nuclear':0.27,'hydro':0.02,'wind':0.00,'solar':0.09,'bio':0.03,'other':0.02},
 'WA':{'gas_cc':0.11,'coal':0.03,'nuclear':0.08,'hydro':0.65,'wind':0.07,'solar':0.01,'other':0.05},
 'PA':{'gas_cc':0.50,'coal':0.07,'nuclear':0.32,'hydro':0.01,'wind':0.03,'solar':0.01,'other':0.06},
 'NY':{'gas_cc':0.45,'coal':0.00,'nuclear':0.22,'hydro':0.23,'wind':0.04,'solar':0.03,'other':0.03},
 'NJ':{'gas_cc':0.50,'coal':0.00,'nuclear':0.40,'hydro':0.00,'solar':0.06,'other':0.04},
 'NE':{'gas_cc':0.08,'coal':0.50,'nuclear':0.13,'hydro':0.02,'wind':0.25,'other':0.02},
 'ND':{'gas_cc':0.03,'coal':0.58,'nuclear':0.00,'hydro':0.02,'wind':0.36,'other':0.01},
 'NV':{'gas_cc':0.58,'coal':0.00,'nuclear':0.00,'hydro':0.04,'solar':0.25,'geo':0.09,'other':0.04},
}
# --- split gas_other out of gas_cc using MEASURED EIA-923 state generation ----------
# STATE_MIX above folds gas steam turbines into combined cycle, although the two differ
# by a factor of four in consumptive water (2.775 vs 0.658 L/kWh).  The split below
# is the measured 2024 gas-steam share of each state's total gas generation (EIA-923 Sch.8D).
GAS_STEAM_SHARE = {'VA':0.005,'TX':0.129,'CA':0.007,'IL':0.000,'OR':0.000,'AZ':0.041,
                   'IA':0.040,'GA':0.045,'WA':0.000,'PA':0.076,'NY':0.233,'NJ':0.000,
                   'NE':0.000,'ND':0.000,'NV':0.024}
def _split_gas(mix, state):
    m = dict(mix); g = m.get('gas_cc', 0.0); f = GAS_STEAM_SHARE.get(state, 0.0)
    if g > 0 and f > 0:
        m['gas_cc'] = g*(1-f); m['gas_other'] = m.get('gas_other', 0.0) + g*f
    return m
STATE_MIX = {s: _split_gas(m, s) for s, m in STATE_MIX.items()}

# --- production vs consumption (load-served) mix ------------------------------------
# EIA State Electricity Profiles 2024: net generation and total retail sales, MWh.
# Virginia generates only 74% of what it sells, so a production-basis mix misstates the
# water intensity of the electricity actually consumed there.
STATE_GEN_SALES_ALL = {
 'AL':(142921216,87522932),  'AK':(6690506,6046503),     'AZ':(116026511,90843288),
 'AR':(61542484,49895812),   'CA':(214191383,245717145), 'CO':(58798395,56842904),
 'CT':(44761412,27351355),   'DE':(4799212,11373916),    'DC':(187195,10142915),
 'FL':(266119236,255095458), 'GA':(139805428,150003965), 'HI':(9160979,8952134),
 'ID':(20035438,26369555),   'IL':(185012935,133226907), 'IN':(97012880,99219607),
 'IA':(70464148,54930422),   'KS':(57696155,41258210),   'KY':(66950848,74405871),
 'LA':(99622835,95356829),   'ME':(14655178,11341591),   'MD':(35424816,59018688),
 'MA':(20914890,49418575),   'MI':(124200090,98991014),  'MN':(58595222,64562108),
 'MS':(77336712,48684612),   'MO':(66875710,77776034),   'MT':(26872883,15567013),
 'NE':(37228950,35191045),   'NV':(45528427,40664639),   'NH':(16942479,10913961),
 'NJ':(60175245,73531424),   'NM':(39697294,30296354),   'NY':(129015493,140497501),
 'NC':(134965396,136904526), 'ND':(42557243,29769698),   'OH':(142746706,153707376),
 'OK':(94069145,72083773),   'OR':(64661249,59680701),   'PA':(241498648,142146514),
 'RI':(9777026,7414247),     'SC':(100485416,83961428),  'SD':(20871994,13637204),
 'TN':(76166766,102962435),  'TX':(566502688,505431317), 'UT':(35133906,34688083),
 'VT':(2258891,5458947),     'VA':(102698615,138044772), 'WA':(102397711,89981629),
 'WV':(50594818,32990570),   'WI':(65276344,68291424),   'WY':(40709150,17216901)}
STATE_GEN_SALES = {   # (net generation MWh, retail sales MWh), EIA 2024
 'VA':(102698615,138044772), 'TX':(566502688,505431317), 'CA':(214191383,245717145),
 'IL':(185012935,133226907), 'OR':(64661249,59680701),   'AZ':(116026511,90843288),
 'IA':(70464148,54930422),   'GA':(139805428,150003965), 'WA':(102397711,89981629),
 'PA':(241498648,142146514), 'NY':(129015493,140497501), 'NJ':(60175245,73531424),
 'NE':(37228950,35191045),   'ND':(42557243,29769698),   'NV':(45528427,40664639)}
def self_supply_fraction(state):
    g, s = STATE_GEN_SALES.get(state) or STATE_GEN_SALES_ALL[state]
    return min(1.0, g/s) if s else 1.0
def _consumption_mix(state):
    """Blend the state's own generation mix with the national mix in proportion to net imports."""
    f = self_supply_fraction(state); own = STATE_MIX[state]
    keys = set(own) | set(MIX_2024)
    return {k: f*own.get(k, 0.0) + (1-f)*MIX_2024.get(k, 0.0) for k in keys}

# --- water scarcity (WRI Aqueduct 4.0) ----------------------------------------------
# Aqueduct 4.0 baseline and future annual indicators, aggregated from HydroBASINS level-6
# sub-basins to states by area weighting.  bws = baseline water stress score (0-5);
# power_risk = the Aqueduct weighted risk score for the electric-power sector.
SCARCITY = {}
try:
    import csv as _csv
    _p = _os.path.join(ROOT, 'derived', 'aqueduct_state_scarcity.csv')   # written by STEP 00
    with open(_p, encoding='utf-8') as _f:
        for _r in _csv.DictReader(_f):
            SCARCITY[_r['state']] = {k: (float(v) if v not in ('', None) else None)
                                     for k, v in _r.items() if k != 'state'}
except Exception as _e:                                # keep the model importable without the file
    pass
SCARCITY_FIELD = {2023:'bws_2023', 2030:'ws_bau2030', 2050:'ws_bau2050'}

def scarcity_weight(year=2050, scenario='bau'):
    """Load-weighted Aqueduct water-stress score across the fifteen data-centre states."""
    fld = {'bau':{2030:'ws_bau2030',2050:'ws_bau2050'},
           'opt':{2050:'ws_opt2050'}, 'pes':{2050:'ws_pes2050'}}[scenario].get(year, 'bws_2023')
    num = den = 0.0
    for s, w in DC_WEIGHTS.items():
        v = SCARCITY.get(s, {}).get(fld)
        if v is None: continue
        num += w*v; den += w
    return num/den if den else float('nan')

# --- MEASURED-ANCHORED GRID INTENSITY -------------------------------------------
# The thermoelectric component of the 2024 base year is taken directly from the EIA-923
# records rather than reconstructed from per-technology factors.  This removes a basis
# mismatch: the per-technology factors are water per kWh of COOLED generation (the correct
# quantity for a marginal question), whereas an average grid intensity requires water per
# kWh of TOTAL generation in each category.  Non-thermal water (reservoir evaporation,
# geothermal, panel washing) has no measured counterpart and still comes from factors.
# Factors continue to supply the SHAPE of the 2024-2050 trajectory; the ratio is largely
# insensitive to the basis mismatch because it cancels between numerator and denominator.
US_GEN_2024 = 4300.0                 # TWh, national net generation, 2024
MEAS_THERMAL_2024_BM3 = None         # filled from model_parameters.json below
try:
    MEAS_THERMAL_2024_BM3 = float(_P['thermal_consumption_2024_Bm3'])
except Exception:
    MEAS_THERMAL_2024_BM3 = 3.552
NONTHERMAL_KEYS = ('hydro', 'geo', 'solar', 'wind')

def _nonthermal_intensity(mix, hydro_alloc=1.0):
    return sum(mix.get(k, 0.0)*WF[k]*(hydro_alloc if k == 'hydro' else 1.0)
               for k in NONTHERMAL_KEYS)*GROSSUP

try:
    MEAS_THERMAL_WDR_2024_BM3 = float(_P['thermal_withdrawal_2024_Bm3'])
except Exception:
    MEAS_THERMAL_WDR_2024_BM3 = 172.855

def _nonthermal_intensity_wdr(mix, hydro_alloc=1.0):
    """Non-thermal withdrawal.  Reservoir evaporation is a pure loss with no return flow,
    so hydropower withdrawal equals its consumption; solar and wind withdraw nothing."""
    return sum(mix.get(k, 0.0)*WF_WITH.get(k, WF[k])*(hydro_alloc if k == 'hydro' else 1.0)
               for k in NONTHERMAL_KEYS)*GROSSUP

def measured_I_2024(hydro_alloc=1.0, basis='consumption'):
    """National 2024 intensity: measured thermoelectric + factor-based non-thermal.

    Both bases are anchored the same way, so consumption and withdrawal rest on one
    basis rather than two.
    """
    if basis == 'withdrawal':
        thermal = MEAS_THERMAL_WDR_2024_BM3*1e12/(US_GEN_2024*1e9)*GROSSUP
        return thermal + _nonthermal_intensity_wdr(MIX_2024, hydro_alloc)
    thermal = MEAS_THERMAL_2024_BM3*1e12/(US_GEN_2024*1e9)*GROSSUP
    return thermal + _nonthermal_intensity(MIX_2024, hydro_alloc)

# measured thermoelectric water by state, 2024 (EIA-923, direct aggregation), million m3
# (derived/*.csv, written by STEP 00)
STATE_THERMAL_MEAS = {}
STATE_THERMAL_MEAS_ALL = {}
STATE_GEN_TWH = {'VA':102.7,'TX':566.5,'CA':214.2,'IL':185.0,'OR':64.7,'AZ':116.0,'IA':70.5,
                 'GA':139.8,'WA':102.4,'PA':241.5,'NY':129.0,'NJ':60.2,'NE':37.2,'ND':42.6,'NV':45.5}
try:
    import csv as _c2
    _p2 = _os.path.join(ROOT, 'derived', 'state_validation_direct_vs_factor.csv')
    with open(_p2, encoding='utf-8') as _f2:
        for _r2 in _c2.DictReader(_f2):
            STATE_THERMAL_MEAS[_r2['state']] = float(_r2['direct_Mm3'])   # million m3
    with open(_p2.replace('state_validation_direct_vs_factor', 'state_thermal_measured_all'),
              encoding='utf-8') as _f3:
        for _r3 in _c2.DictReader(_f3):
            STATE_THERMAL_MEAS_ALL[_r3['state']] = float(_r3['direct_Mm3'])
except Exception:
    pass

# --- consumption (load-serving) basis -------------------------------------------
# A state's own measured water covers only plants inside its borders, so the measured
# intensity is a PRODUCTION-basis quantity.  Virginia generates 103 TWh but consumes 138,
# importing 26% of its electricity; the water for that quarter is consumed elsewhere.
# For the load-serving question we blend the state's own measured intensity with the
# intensity of the pool it imports from, weighted by the self-supply fraction
# (EIA State Electricity Profiles 2024: net generation and total retail sales).
#
# Imports are attributed to the state's synchronous INTERCONNECTION, excluding the
# importing state itself.  An RTO footprint is the wrong unit here: NYISO is New York
# alone and CAISO is essentially California, so "imports from the state's own RTO" would
# be close to "imports from itself" and would leave the production basis unchanged.
# Electricity can only be delivered within a synchronous interconnection, so that is the
# physically correct import pool.  Purchases across pools are not resolved (that would need
# hourly interchange data); the assumption binds only for net importers (five of the
# fifteen states).  Source: EPA eGRID state-interconnection crosswalk.
INTERCONNECT = {}
try:
    import csv as _c4
    with open(_os.path.join(ROOT, 'data', 'state_and_interconnection.csv'),
              encoding='utf-8-sig') as _f4:
        for _r4 in _c4.DictReader(_f4):
            INTERCONNECT[_r4['State Postal Code']] = _r4['Interconnect']
except Exception:
    pass

def import_pool_intensity(state, hydro_alloc=1.0):
    """Water intensity of the pool a state can import from: its interconnection,
    excluding the state itself, on the measured basis."""
    ic = INTERCONNECT.get(state)
    peers = [x for x, v in INTERCONNECT.items()
             if v == ic and x != state and x in STATE_THERMAL_MEAS_ALL
             and STATE_GEN_SALES_ALL.get(x, (0, 0))[0]]
    if not peers:
        return measured_I_2024(hydro_alloc)
    num = sum(STATE_THERMAL_MEAS_ALL[x]*1e9 for x in peers)
    den = sum(STATE_GEN_SALES_ALL[x][0]*1e3 for x in peers)
    thermal = num/den*GROSSUP
    have = [x for x in peers if x in STATE_MIX]
    mix = ({k: sum(STATE_MIX[x].get(k, 0.0) for x in have)/len(have) for k in NONTHERMAL_KEYS}
           if have else MIX_2024)
    return thermal + _nonthermal_intensity(mix, hydro_alloc)

def state_intensity(state, hydro_alloc=1.0, basis='consumption'):
    """State grid water intensity, 2024.  basis='consumption' (default, headline) adds
    imports from the interconnection pool; 'production' counts only in-state generation;
    'factor' is the national-factor reconstruction used for validation."""
    if basis == 'production':
        return state_intensity_measured(state, hydro_alloc)
    if basis == 'factor':
        return _state_intensity(STATE_MIX[state], hydro_alloc)
    return state_intensity_consumption(state, hydro_alloc)

def state_intensity_consumption(state, hydro_alloc=1.0):
    """Load-serving intensity: own generation plus imports from the interconnection pool."""
    f = self_supply_fraction(state)
    own = state_intensity_measured(state, hydro_alloc)
    if f >= 1.0:
        return own
    return f*own + (1-f)*import_pool_intensity(state, hydro_alloc)

def state_intensity_measured(state, hydro_alloc=1.0):
    """2024 state intensity: measured thermoelectric + factor-based non-thermal."""
    tw = STATE_THERMAL_MEAS.get(state)
    if tw is None or state not in STATE_GEN_TWH:
        tw2 = STATE_THERMAL_MEAS_ALL.get(state)
        g2 = STATE_GEN_SALES_ALL.get(state, (0, 0))[0]
        if tw2 is not None and g2:                                  # any state, measured basis
            return tw2*1e9/(g2*1e3)*GROSSUP + _nonthermal_intensity(MIX_2024, hydro_alloc)
        return _state_intensity(STATE_MIX[state], hydro_alloc)      # last resort: factors
    # tw is in million m3 (x1e9 -> L); STATE_GEN_TWH in TWh (x1e9 -> kWh)
    thermal = tw*1e9/(STATE_GEN_TWH[state]*1e9)*GROSSUP
    return thermal + _nonthermal_intensity(STATE_MIX[state], hydro_alloc)

def _state_intensity(mix, hydro_alloc):
    return sum((WF[k]*hydro_alloc if k=='hydro' else WF[k])*v for k,v in mix.items())*GROSSUP

def grid_intensity_dcweighted(re_scn, hydro_alloc=1.0, year=2024, anchor='measured'):
    """Load-weighted intensity across the fifteen data-centre states.

    anchor='measured' (default) is the CONSUMPTION (load-serving) basis: each state's own
    measured intensity blended with its interconnection import pool by the self-supply
    fraction.  This is the headline basis, because a data centre draws the electricity its
    state consumes, not the electricity its state generates.  anchor='production' and
    anchor='factor' return the two comparison bases reported in the SI.  Later years scale
    with the national trajectory; the model does not resolve state generation pathways.
    """
    tw = sum(DC_WEIGHTS.values())
    if anchor == 'measured':          # load-serving: own generation plus interconnection imports
        base = sum(w*state_intensity_consumption(s, hydro_alloc) for s, w in DC_WEIGHTS.items())/tw
    elif anchor == 'production':      # own generation only -- SI validation basis
        base = sum(w*state_intensity_measured(s, hydro_alloc) for s, w in DC_WEIGHTS.items())/tw
    else:                             # factor reconstruction -- SI validation basis
        base = sum(w*_state_intensity(STATE_MIX[s], hydro_alloc) for s, w in DC_WEIGHTS.items())/tw
    I = grid_intensity(re_scn, hydro_alloc, anchor=anchor)
    i24 = list(YEARS).index(2024); iy = list(YEARS).index(int(year))
    return base*I[iy]/I[i24]

# =====================================================================
# MODULE B | COOLING PATHWAYS  (coupled WUE_IT [L/kWh_IT] and PUE)
# ---------------------------------------------------------------------
# WUE per IT-kWh (industry convention). Benchmarks:
#   fleet ~0.5; hyperscaler direct WUE 2024: AWS 0.15/Meta 0.19/MS 0.27/Google 1.32 [Barclays]
#   evaporative tower ~2.6 Mgal/MW/yr; closed-loop DLC <20 L/MW/yr makeup [NVIDIA; Barclays]
# PUE: wet tower 1.05-1.20 ; dry cooler 1.10-1.30  [Barclays report pp.30-32]
#   -> dry ("waterless") reject costs ~+0.10 PUE = energy penalty -> more grid water.
COOLING = {  # name: (WUE_IT L/kWh, PUE)  -- discrete "whole-fleet" pathways (used as bounds / matrix)
    'current_evap':     (0.61, 1.145),  # AI evaporative liquid-assist: WUE LBNL 2024 report Fig 4.5 (AI-specialized);
                                        #   PUE = LBNL 2025 Update AI-facility value for 2024 (same as COOL_C3['aievap'])
    'transitional':     (0.36, 1.18),   # ~LBNL fleet/hyperscale aggregate WUE 0.32-0.36
    'DLC_wet_reject':   (0.15, 1.13),   # AWS 2024 ESG best-practice (0.15 L/kWh)
    'nvidia_warmliquid':(0.01, 1.10),   # NVIDIA Rubin/DSX 45C warm-liquid: near-zero water + low PUE (favorable climate)
    'legacy_dry_penalty':(0.02, 1.26),  # legacy air-cooled dry chiller / hot climate: near-zero water BUT PUE penalty (backfire case)
    'ideal_zero':       (0.00, 1.30),   # hypothetical fully waterless with worst-case PUE penalty
    'ferveret':         (0.00, 1.05),   # two-phase immersion (Ferveret/MIT 2026): zero water AND lowest PUE
    'ferveret_cons':    (0.00, 1.10),   # conservative PUE variant of the above
}

# --- cooling ADOPTION model (time-varying fleet WUE/PUE) -------------------------
# All NEW AI capacity is liquid-cooled (NVIDIA GB200 NVL72 has no air-cooled variant).
# Heat rejection evolves from evaporative-assisted (higher WUE, low PUE) to warm-liquid dry
# rejection (near-zero WUE), entering through new and refreshed machines (stock turnover).
# --- cooling technology classes -------------------------------------------------
# PUE for the AI evaporative class is LBNL's measured value for facilities serving AI
# equipment (1.145 in 2024, 1.136 in 2030) [LBNL 2025 Update S.3.5].
# Warm-liquid PUE is set to 1.13: LBNL reports no expected industry-wide PUE change for
# AI facilities, and an independent thermal-resistance analysis puts the chiller-free
# cooling partial PUE near 1.11 (=> whole-facility ~1.14-1.16).
# WUE/PUE are (low, mid, high) triples so the uncertainty can be propagated.
COOL_C3 = {
    'leg':        ((0.20, 0.24, 0.30), (None, None, None)),  # PUE calibrated below
    'aievap':     ((0.50, 0.61, 0.75), (1.135, 1.145, 1.160)),
    'aidry':      ((0.005, 0.010, 0.050), (1.100, 1.130, 1.160)),  # ASHRAE W45 warm-liquid, dry reject
    'ferveret':   ((0.000, 0.000, 0.010), (1.040, 1.050, 1.080)),  # two-phase immersion
    'drychiller': ((0.010, 0.020, 0.040), (1.230, 1.260, 1.300)),  # legacy chiller-based dry
}
# Climate stratification.  ASHRAE class W45 = facility supply water up to
# 45 C, the "dry cooler / heat reuse" band.  With a ~16 C thermal-resistance stack from
# supply water to ambient, chiller-free dry rejection needs ambient <= ~29 C; hot-climate
# sites therefore need adiabatic assist or trim chilling in summer.
CLIMATE_ADJ = {                     # (WUE multiplier, PUE adder) applied to 'aidry'
    'cool':      (0.5, -0.010),
    'temperate': (1.0,  0.000),
    'hot':       (5.0, +0.030),
}
CLIMATE_OF_STATE = {'WA':'cool','OR':'cool','NY':'cool','IA':'cool','NE':'cool','ND':'cool',
                    'IL':'temperate','PA':'temperate','NJ':'temperate','VA':'temperate','CA':'temperate',
                    'TX':'hot','AZ':'hot','GA':'hot','NV':'hot'}

def _cool_point(level='mid'):
    j = {'lo':0,'mid':1,'hi':2}[level]
    return {k:(v[0][j], v[1][j]) for k,v in COOL_C3.items()}

def climate_weighted_aidry(level='mid'):
    """Load-weighted warm-liquid (WUE, PUE) across the fifteen data-centre states."""
    j = {'lo':0,'mid':1,'hi':2}[level]
    w0, p0 = COOL_C3['aidry'][0][j], COOL_C3['aidry'][1][j]
    tw = sum(DC_WEIGHTS.values()); w=p=0.0
    for s, wt in DC_WEIGHTS.items():
        mw, dp = CLIMATE_ADJ[CLIMATE_OF_STATE[s]]
        w += wt*w0*mw; p += wt*(p0+dp)
    return w/tw, p/tw

# AI share of IT electricity -- re-anchored to LBNL 2025 Update.
#   2024 = 0.38  [Fig. 9: AI-specialised servers ~50 TWh of ~132 TWh IT electricity]
#   2030 = 0.75  [S.3.6: AI servers = 55% of total DC energy; aggregate PUE 1.36]
#   post-2030 extrapolated (LBNL stops at 2030); sensitivity band 0.70-0.90 at 2050.
REPORT_START = 2027
AI_SHARE_ANCHORS = [(2024,0.38),(2027,0.60),(2030,0.75),(2040,0.82),(2050,0.85)]
AI_SHARE_BAND    = {'lo':0.70, 'mid':0.85, 'hi':0.90}     # 2050 value
def ai_share_path(level='mid'):
    xs=[a for a,_ in AI_SHARE_ANCHORS]; ys=[b for _,b in AI_SHARE_ANCHORS]
    ys=list(ys); ys[-1]=AI_SHARE_BAND[level]
    return np.clip(np.interp(YEARS, xs, ys).astype(float), 0, 1)

# --- legacy (non-AI) pool -----------------------------------------------------
# The legacy pool is NOT frozen.  Its PUE is calibrated so that
# the modelled fleet PUE reproduces LBNL's aggregate PUE in 2024 (1.45); the 2050 value
# is a stated assumption (LBNL publishes no post-2030 figure), tested by LEG_PUE_2050_BAND.
# Its WUE declines from the mass-balance value 0.24 toward 0.15 (AWS 2024 measured fleet).
LEG_WUE_2050 = 0.15
LEG_PUE_2050_BAND = {'lo':1.45, 'mid':1.55, 'hi':1.64}    # 'hi' = frozen at the 2024 value

def _calibrate_leg_pue():
    """p_leg(2024) such that fleet PUE(2024) = LBNL aggregate 1.45, with s(2024)=0."""
    a24 = ai_share_path()[list(YEARS).index(2024)]
    p_evap = COOL_C3['aievap'][1][1]
    return (PUE_REF_PATH[list(YEARS).index(2024)] - a24*p_evap)/(1.0-a24)
LEG_PUE_2024 = _calibrate_leg_pue()

def legacy_series(band='mid'):
    """(WUE, PUE) of the non-AI pool by year -- turns over rather than staying frozen."""
    w = np.interp(YEARS, [2023, 2050], [0.24, LEG_WUE_2050])
    p = np.interp(YEARS, [2024, 2050], [LEG_PUE_2024, LEG_PUE_2050_BAND[band]])
    return w, p

COOL_C = {k: (v[0][1], v[1][1] if v[1][1] is not None else LEG_PUE_2024) for k,v in COOL_C3.items()}
ADOPT_TIER = {'slow':(0.90,6), 'base':(0.95,5), 'fast':(1.00,4)}  # (advanced share of NEW machines by 2030, hardware life L yr)
DRY_ADOPT  = ADOPT_TIER                               # alias

def _a_new(anew2030):
    """Advanced-cooling adoption in NEW/refreshed machines by year (0 pre-2027; 0.80 in 2027; ramp to anew2030 by 2030; flat)."""
    a=np.zeros(len(YEARS),float)
    for i,t in enumerate(YEARS):
        if t<2027: a[i]=0.0
        elif t<=2030: a[i]=0.80+(anew2030-0.80)*(t-2027)/3.0
        else: a[i]=anew2030
    return a

def adv_share_path(dry_scn='base', demand_scn='mid'):
    """Advanced-cooling share of the AI stock over YEARS, from the stock-turnover model."""
    ai = ai_share_path(); anew2030, L = ADOPT_TIER[dry_scn]; a_new=_a_new(anew2030)
    E_ai = demand_path(demand_scn)*ai
    share = np.zeros(len(YEARS), float)
    for i in range(len(YEARS)):
        if i==0 or YEARS[i]<2027: continue
        g = E_ai[i]/max(E_ai[i-1],1e-9)
        f_new = np.clip(1-(1-1/L)/g, 0, 1)
        share[i] = (1-f_new)*share[i-1] + f_new*a_new[i]
    return share

def cooling_series(cooling, dry_scn='base', demand_scn='mid', cool_level='mid',
                   ai_level='mid', leg_band='mid', climate=True):
    """Return (WUE(t), PUE(t)) arrays over YEARS via a STOCK-TURNOVER model.
       Advanced cooling enters through NEW/refreshed machines at rate a_new(t); the installed base
       turns over on hardware life L. Fast AI-electricity growth => most stock is new each year, so
       advanced cooling penetrates quickly and keeps rising to 2050 (no 2040 cap).
       'adaptive_warm'/'adaptive_ferveret'/'adaptive_drychiller' select the advanced technology."""
    ADV = {'adaptive_warm':'aidry', 'adaptive_ferveret':'ferveret', 'adaptive_drychiller':'drychiller'}
    if cooling in ADV:
        ai = ai_share_path(ai_level)
        share = adv_share_path(dry_scn, demand_scn)
        pt = _cool_point(cool_level)
        if ADV[cooling] == 'aidry' and climate:
            adv = climate_weighted_aidry(cool_level)      # load-weighted across climate zones
        else:
            adv = pt[ADV[cooling]]
        w_leg, p_leg = legacy_series(leg_band)            # legacy pool turns over
        wue_ai = (1-share)*pt['aievap'][0] + share*adv[0]
        pue_ai = (1-share)*pt['aievap'][1] + share*adv[1]
        wue = (1-ai)*w_leg + ai*wue_ai
        pue = (1-ai)*p_leg + ai*pue_ai
        return wue, pue
    w, p = COOLING[cooling]
    return np.full(len(YEARS), w, float), np.full(len(YEARS), p, float)

# =====================================================================
# MODULE D | CHIP-FAB (LIFECYCLE) WATER  W_fab(t)  [L/yr]
# ---------------------------------------------------------------------
# Chain: E_IT -> installed accelerator power -> annual GPU shipments
#        -> logic wafers (+HBM/packaging uplift) -> freshwater intake.
UTIL = 0.65                                        # avg utilisation (LBNL 0.50, Barclays 0.80) -> mid
LIFE = 5.0                                         # accelerated-server lifetime [yr]
                                                   #   LBNL 2025 Update Reference Case = 5 yr
LIFE_BAND = {'lo':4.0, 'mid':5.0, 'hi':5.5}        #   sensitivity scenarios in the same report
# Accelerator shipments are ANCHORED to LBNL 2025 Update rather than inferred from power alone:
#   2024 = 7.0 M units (73% GPU / 27% ASIC)   [S.3.1.2]
#   2030 = 19  M units                        [S.3.1.2]
# Caveat carried into the text: IDC reports ASIC shipments on a GLOBAL basis and uses the same
# totals for its US forecast, so 7.0 M is an upper bound for US deployment (GPU-only ~5.1 M).
SHIP_ANCHORS = [(2024, 7.0e6), (2030, 19.0e6)]
F_ACC = (0.30, 0.70)                               # accelerator share of IT power (est.); GPU-shipment chain calibrated to Epoch AI AI-Chip-Sales (NVIDIA 4M Hopper + 3M Blackwell cumulative thru Oct 2025)
TDP = (0.70, 2.00)                                 # per-accelerator TDP [kW]: H100 0.7 -> Rubin-era 2.0
GPU_OVERHEAD = 1.30                                # per-GPU IT power = TDP x share of CPU/NVLink/mem
DIES_PER_GPU = (1.0, 2.0)                          # Hopper 1 die -> Blackwell/Rubin 2 dies (2023->2040)
DIE_AREA = 800.0                                   # logic die area [mm^2] (H100 814; GB200 ~2x800)
WAFER_USABLE = np.pi*150**2*0.95                   # 300mm wafer usable area [mm^2] (edge excl.)
PACKING = 0.85                                     # die-packing efficiency
YIELD = (0.75, 0.65)                               # good-die yield: shrinks as dies grow (2023->2040)
HBM_PKG_UPLIFT = 0.60                              # +60% wafer-equiv for HBM stacks + CoWoS [est.]
PHI_NET = 6300.0                                   # net freshwater intake per 12" wafer [L]
                                                   #   = TSMC 2023 total water 101 Mm3 / 16M wafers
                                                   #   (already reflects 85.7% recycling)  [TSMC/IDTechEx]
PHI_NODE_GROWTH = 0.03                             # +3%/yr per-wafer water (nodes add steps) [IDTechEx dir.]
RHO_BASE = 0.857                                   # TSMC recycling 2023
RHO = (0.857, 0.92)                                # recycling improves 2023->2040 (AZ 90%+ by 2028)
# --- onshore share: an EXPLICIT SCENARIO parameter, not a sourced value -------------
# Anchors that do exist: TSMC Arizona Fab 1 entered volume production of 4nm in Q4 2024;
# TSMC has announced ~US$165bn of US investment across six planned fabs.  Extrapolating
# those to a 2050 share is not supported by any published projection, so the share is
# carried as a scenario band.
ONSHORE_BAND = {'lo': (0.02, 0.10), 'mid': (0.02, 0.25), 'hi': (0.02, 0.40)}
ONSHORE = ONSHORE_BAND['mid']

# --- fabrication ELECTRICITY and its generation water -------------------------------
# TSMC 2024: total energy 27,456 GWh, of which ~93% purchased electricity -> ~25,530 GWh;
# total shipments 12.9 M 12-inch-equivalent wafers  ->  ~1,980 kWh per wafer (company mean).
# Leading-edge logic uses more mask layers than the company mean; TSMC reports 37.1 kWh per
# 12-inch-equivalent wafer mask layer in 2024, so an advanced-node wafer at ~80 layers would
# approach ~3,000 kWh.  The company mean is used centrally; the band spans both.
KWH_PER_WAFER = {'lo': 1500.0, 'mid': 1980.0, 'hi': 3300.0}

# Taiwan grid, where the offshore share of accelerator wafers is fabricated.
# Generation mix 2024 (Ministry of Economic Affairs, Energy Administration; national basis):
TW_MIX_2024 = {'gas': 0.4245, 'coal': 0.3927, 'nuclear': 0.0422, 'oil': 0.0145,
               'solar': 0.055, 'wind': 0.036, 'hydro': 0.014, 'waste_bio': 0.0105,
               'pumped': 0.0107}
# Taiwan's large thermal plants are coastal and predominantly seawater once-through cooled.
# Once-through systems consume almost no FRESHWATER (USGS: consumption ~1% of withdrawal),
# so applying US technology factors -- measured on a mostly recirculating freshwater fleet --
# would overstate Taiwan's freshwater intensity.  No measured Taiwanese cooling-water survey
# exists, so the offshore factor is carried as an explicit band:
#   hi  = US technology factors applied to the Taiwanese mix (freshwater-cooled assumption)
#   lo  = coastal thermal treated as seawater-cooled (freshwater ~0), hydro evaporation only
def _taiwan_intensity():
    TD = 1.0/(1.0-0.04)                                   # Taiwan T&D loss ~4%
    hi = (TW_MIX_2024['gas']*WF['gas_cc'] + TW_MIX_2024['coal']*WF['coal']
          + TW_MIX_2024['nuclear']*WF['nuclear'] + TW_MIX_2024['oil']*WF['gas_other']
          + TW_MIX_2024['solar']*WF['solar'] + TW_MIX_2024['wind']*WF['wind']
          + (TW_MIX_2024['hydro']+TW_MIX_2024['pumped'])*WF['hydro']
          + TW_MIX_2024['waste_bio']*WF['bio'])*TD
    thermal = TW_MIX_2024['gas']+TW_MIX_2024['coal']+TW_MIX_2024['nuclear']+TW_MIX_2024['oil']
    lo = (thermal*0.08                                    # seawater once-through: process water only
          + (TW_MIX_2024['hydro']+TW_MIX_2024['pumped'])*WF['hydro']
          + TW_MIX_2024['solar']*WF['solar'])*TD
    return {'lo': lo, 'mid': 0.5*(lo+hi), 'hi': hi}
TW_I = _taiwan_intensity()

def _interp(pair):
    lo, hi = pair
    return lo + (hi-lo)*np.clip((YEARS-2023)/(2040-2023), 0, 1)   # endpoints defined at 2040; held flat to 2050

def fab_water(scn, include_elec=True, wafer_kwh='mid', tw_level='mid', onshore='mid', life='mid'):
    """Returns dict with W_fab total, onshore, offshore [L/yr] and diagnostics."""
    E_dc = demand_path(scn)
    E_IT = E_dc/PUE_REF_PATH                        # TWh
    f_acc = _interp(F_ACC); tdp = _interp(TDP)
    dpg = _interp(DIES_PER_GPU); yld = _interp(YIELD)
    rho = _interp(RHO); onsh = _interp(ONSHORE_BAND[onshore])
    good_dies = WAFER_USABLE/DIE_AREA*PACKING*yld   # good logic dies per wafer
    phi = PHI_NET*(1+PHI_NODE_GROWTH*(YEARS-2023))*(1-rho)/(1-RHO_BASE)  # net L/wafer

    P_IT = E_IT*1e3/(8760*UTIL)                     # nameplate IT power [GW]
    P_acc = f_acc*P_IT                              # accelerator nameplate power [GW]
    ship = np.zeros_like(YEARS, dtype=float)        # annual accelerator GW shipped
    P_prev0 = P_acc[0]/1.6                            # assume ~60% growth into 2023 (avoids base-year 'whole-stock' artifact)
    for i in range(len(YEARS)):
        p_prev = P_acc[i-1] if i > 0 else P_prev0
        ship[i] = max(P_acc[i]-p_prev, 0.0) + p_prev/LIFE_BAND[life]
    p_gpu = tdp*GPU_OVERHEAD                         # per-GPU IT power [kW]
    N_gpu = ship*1e6/p_gpu                           # power-inferred GPUs shipped/yr
    # --- calibrate the power-inferred chain to LBNL's reported unit shipments -------
    iy = list(YEARS)
    k24 = SHIP_ANCHORS[0][1]/N_gpu[iy.index(2024)]
    k30 = SHIP_ANCHORS[1][1]/N_gpu[iy.index(2030)]
    kf  = np.interp(YEARS, [2023, 2024, 2030, 2050], [k24, k24, k30, k30])
    N_gpu = N_gpu*kf
    N_waf_logic = N_gpu*dpg/good_dies                # logic wafers
    N_waf_eq = N_waf_logic*(1+HBM_PKG_UPLIFT)        # + HBM/packaging
    W_direct = N_waf_eq*phi                          # L/yr  DIRECT process freshwater

    # --- generation water for fabrication electricity ------------------------------
    kwh_w = KWH_PER_WAFER[wafer_kwh]
    E_fab_kwh = N_waf_eq*kwh_w                       # kWh/yr of fab electricity
    I_us  = grid_intensity('ref', 1.0)               # US grid, L/kWh (time-varying)
    I_tw  = TW_I[tw_level]                           # Taiwan grid, L/kWh (constant)
    W_elec = E_fab_kwh*(onsh*I_us + (1-onsh)*I_tw)
    W = W_direct + W_elec if include_elec else W_direct
    return {'W_fab': W, 'W_fab_direct': W_direct, 'W_fab_elec': W_elec,
            'W_fab_onshore': W_direct*onsh, 'W_fab_offshore': W_direct*(1-onsh),
            'N_gpu': N_gpu, 'N_wafer_eq': N_waf_eq, 'good_dies': good_dies,
            'E_fab_TWh': E_fab_kwh/1e9}

# =====================================================================
# ASSEMBLY | total lifecycle water for one (demand, cooling, grid) case
# =====================================================================
def run_case(demand_scn, cooling, re_scn, hydro_alloc=1.0, weighting='national', dry_scn='base',
             attribution='average', cool_level='mid', ai_level='mid', leg_band='mid',
             climate=True, fab_elec=True, scarcity=False):
    E_dc_ref = demand_path(demand_scn)              # TWh (total facility electricity, at PUE_ref)
    E_IT = E_dc_ref/PUE_REF_PATH                     # TWh  (fixed-IT functional unit; see Methods)
    wue, pue = cooling_series(cooling, dry_scn, demand_scn, cool_level, ai_level, leg_band, climate)
    E_dc = pue*E_IT                                  # TWh (this cooling's actual facility elec)
    if attribution != 'average':
        I = attribution_intensity(attribution, re_scn, hydro_alloc)
    elif weighting == 'dc':
        I = np.array([grid_intensity_dcweighted(re_scn, hydro_alloc, y) for y in YEARS])
    else:
        I = dc_intensity_path(re_scn, hydro_alloc)  # L/kWh serving data-centre load

    W_site = wue*(E_IT*1e9)                           # L/yr  (WUE per IT-kWh)
    W_grid = (E_dc*1e9)*I                             # L/yr
    W_fab  = fab_water(demand_scn, include_elec=fab_elec)['W_fab']   # L/yr
    W_tot  = W_site+W_grid+W_fab
    # --- internal-consistency assertions (the identities stated under Table 1) ---
    assert np.allclose(W_tot, W_site+W_grid+W_fab, rtol=1e-12), 'component sum != total'
    assert np.allclose(W_grid, E_dc*1e9*I, rtol=1e-12), 'W_grid != E_dc * I'
    assert np.allclose(W_site, wue*E_IT*1e9, rtol=1e-12), 'W_site != WUE * E_IT'
    assert np.allclose(E_dc, pue*E_IT, rtol=1e-12), 'E_dc != PUE * E_IT'
    df = pd.DataFrame({
        'year': YEARS, 'E_IT_TWh': E_IT, 'E_dc_TWh': E_dc, 'PUE': pue, 'WUE': wue,
        'I_grid_LkWh': I,
        'W_site_ML': W_site/1e6, 'W_grid_ML': W_grid/1e6, 'W_fab_ML': W_fab/1e6,
        'W_total_ML': W_tot/1e6,                      # ML = million litres = 1000 m3
        'theta_site': W_site/W_tot, 'theta_grid': W_grid/W_tot, 'theta_fab': W_fab/W_tot,
        'E_dc_proj_TWh': E_dc_ref, 'PUE_ref': PUE_REF_PATH,
    })
    return df

# =====================================================================
# SELF-CHECK   (python code/lifecycle_water_model.py)
# Prints headline quantities of the reference case; writes no files.
# =====================================================================
if __name__ == '__main__':
    print('parameters:', PARAMS_SOURCE)
    r = run_case('mid', 'adaptive_warm', 'ref')            # reference case (Table 1)
    print('\n=== reference case: mid demand / warm-liquid adoption / reference grid ===')
    for y in (2027, 2030, 2040, 2050):
        z = r[r.year == y].iloc[0]
        print(f"{y}: total {z.W_total_ML/1e6:.3f} Bm3  (generation {z.theta_grid*100:.1f}%, "
              f"site {z.theta_site*100:.1f}%, fab {z.theta_fab*100:.2f}%)  I = {z.I_grid_LkWh:.3f} L/kWh")
    m = r.year >= REPORT_START
    print(f"cumulative {REPORT_START}-2050: {r.W_total_ML[m].sum()/1e6:.2f} Bm3")

    mack = 17.0/WF['hydro']                                 # Macknick median, 17 L/kWh
    i24 = list(YEARS).index(2024)
    print('\n=== grid water intensity, 2024, consumption basis [L/kWh] ===')
    print(f"  national (measured anchor)          : {grid_intensity('ref', 1.0)[i24]:.2f}")
    print(f"  DC-weighted, Grubert-Sanders hydro  : {grid_intensity_dcweighted('ref', 1.0, 2024):.2f}")
    print(f"  DC-weighted, Macknick hydro (17)    : {grid_intensity_dcweighted('ref', mack, 2024):.2f}")
    print(f"  DC-weighted, hydro excluded         : {grid_intensity_dcweighted('ref', 0.0, 2024):.2f}")

    (w_wet, p_wet), (w_dry, p_dry) = COOL_C['aievap'], COOL_C['drychiller']
    print('\n=== legacy dry chiller vs AI evaporative liquid-assist ===')
    print(f"  site water saved {w_wet-w_dry:.2f} L/kWh_IT ; PUE penalty {p_dry-p_wet:.3f}")
    print(f"  break-even grid intensity I* = {(w_wet-w_dry)/(p_dry-p_wet):.2f} L/kWh")
