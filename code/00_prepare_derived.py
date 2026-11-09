#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STEP 00 - BUILD ALL DERIVED DATASETS FROM THE RAW SOURCE FILES.

Every file written by this script is reproducible from data/ alone.  Nothing downstream
reads a dataset that this script does not create.  Run this first (from the repository root):

    python code/00_prepare_derived.py

Inputs   (data/)
  Cooling_Boiler_Generator_Data_Detail_2024.xlsx   EIA-923 Schedule 8D
  Aqueduct40_baseline_annual_y2023m07d05.csv       WRI Aqueduct 4.0 baseline     (read from .csv.zip)
  Aqueduct40_future_annual_y2023m07d05.csv         WRI Aqueduct 4.0 projections  (read from .csv.zip)
  The two Aqueduct CSVs are distributed zipped because of their size; they are read directly
  from the zip archives, or from the unzipped .csv if present.

Outputs  (derived/)
  state_thermal_gen_2024_from_EIA923.csv   state x technology net generation
  state_validation_direct_vs_factor.csv    measured vs factor-reconstructed state water
  factors_by_tech_and_cooling.csv          water factors by technology x cooling family
  state_intensity_direct.csv               state intensity, factor and measured bases
  aqueduct_state_scarcity.csv              state water stress, baseline and projections
"""
import os, sys, io, csv, zipfile, collections, warnings
import pandas as pd, numpy as np
warnings.filterwarnings('ignore')

# Project root = the directory that holds code/, data/ and derived/ (override with PROJECT_ROOT).
ROOT    = os.environ.get('PROJECT_ROOT', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA    = os.path.join(ROOT, 'data')
DERIVED = os.path.join(ROOT, 'derived')
os.makedirs(DERIVED, exist_ok=True)

GAL_TO_L = 3.785411784
GROSSUP  = 1.0/(1.0-0.048)                      # T&D loss gross-up, EIA
WC = 'Water Consumption Volume (Million Gallons)'
WW = 'Water Withdrawal Volume (Million Gallons)'
NG = ['Net Generation from Steam Turbines (MWh)',
      'Net Generation Associated with Single Shaft Combined Cycle Units (MWh)',
      'Net Generation Associated with Combined Cycle Gas Turbines (MWh)']
TECHMAP = {'Natural Gas Fired Combined Cycle':'gas_cc','Natural Gas Steam Turbine':'gas_other',
           'Conventional Steam Coal':'coal','Nuclear':'nuclear','Wood/Wood Waste Biomass':'bio'}
# EPRI fifteen-state data-centre load distribution and 2024 net generation (EIA)
DC_STATES = ['VA','TX','CA','IL','OR','AZ','IA','GA','WA','PA','NY','NJ','NE','ND','NV']
STATE_GEN_TWH = {'VA':102.7,'TX':566.5,'CA':214.2,'IL':185.0,'OR':64.7,'AZ':116.0,'IA':70.5,
                 'GA':139.8,'WA':102.4,'PA':241.5,'NY':129.0,'NJ':60.2,'NE':37.2,'ND':42.6,'NV':45.5}
STATE_NAME = {'Virginia':'VA','Texas':'TX','California':'CA','Illinois':'IL','Oregon':'OR',
              'Arizona':'AZ','Iowa':'IA','Georgia':'GA','Washington':'WA','Pennsylvania':'PA',
              'New York':'NY','New Jersey':'NJ','Nebraska':'NE','North Dakota':'ND','Nevada':'NV'}


def cooling_family(x):
    """Group the EIA 860 cooling-type codes into four physical families."""
    x = str(x)
    if x.startswith(('(ON', '(OC')):               return 'once-through'
    if x.startswith(('(RI', '(RN', '(RF', '(RC')): return 'recirculating'
    if x.startswith('(DC'):                        return 'dry'
    if x.startswith('(H'):                         return 'hybrid'
    return 'other'


def load_eia923():
    """Read EIA-923 Schedule 8D and de-duplicate water (per cooling system) and
    generation (per generator); both are repeated across association rows."""
    f = os.path.join(DATA, 'Cooling_Boiler_Generator_Data_Detail_2024.xlsx')
    df = pd.read_excel(f, sheet_name='Detail', header=2, thousands=',')
    df.columns = [str(c).replace(chr(10), ' ').strip() for c in df.columns]
    for c in [WC, WW] + NG:
        df[c] = pd.to_numeric(df[c], errors='coerce')
    df['fam'] = df['860 Cooling Type 1'].map(cooling_family)
    df['k']   = df['Generator Primary Technology'].map(TECHMAP)
    w = df.drop_duplicates(['Plant Code', 'Cooling ID', 'Year', 'Month'])
    g = df.drop_duplicates(['Plant Code', 'Generator ID', 'Year', 'Month']).copy()
    g['ng'] = g[NG].sum(axis=1)
    return df, w, g


def build_state_generation(g):
    """State x technology net generation, MWh (used for the gas-steam split)."""
    st = g.dropna(subset=['k']).groupby(['State', 'k'])['ng'].sum().unstack(fill_value=0)
    st = st.reindex(DC_STATES).fillna(0)
    out = os.path.join(DERIVED, 'state_thermal_gen_2024_from_EIA923.csv')
    st.to_csv(out); print('  wrote', out)
    return st


def build_cooling_factors(w, g):
    """Consumptive water factors by technology x cooling family, L/kWh."""
    W = w.dropna(subset=['k']).groupby(['k', 'fam'])[WC].sum()
    G = g.dropna(subset=['k']).groupby(['k', 'fam'])['ng'].sum()
    F = (W*1e6*GAL_TO_L/(G*1e3)).dropna().rename('L_per_kWh')
    out = os.path.join(DERIVED, 'factors_by_tech_and_cooling.csv')
    F.to_csv(out); print('  wrote', out)
    return F


def build_state_validation(w, g):
    """Measured state thermoelectric water against the national-factor reconstruction.

    (a) direct  = sum of reported consumption for the state
    (b) factor  = sum over technologies of (state generation x national factor)
    Units: million m3.
    """
    Wk = w.dropna(subset=['k']).groupby('k')[WC].sum()
    Gk = g.dropna(subset=['k']).groupby('k')['ng'].sum()
    nat_factor = (Wk*1e6*GAL_TO_L/(Gk*1e3))                    # L/kWh, national, per technology
    direct = w.groupby('State')[WC].sum()*1e6*GAL_TO_L/1e9     # -> million m3
    gs = g.dropna(subset=['k']).groupby(['State', 'k'])['ng'].sum()
    rows = []
    for s in DC_STATES:
        if s not in direct.index or s not in gs.index.get_level_values(0):
            continue
        d = direct[s]
        f = sum(gen*nat_factor.get(k, 0.0) for (st, k), gen in gs.items() if st == s)*1e3/1e9
        rows.append(dict(state=s, direct_Mm3=round(d, 4), factor_Mm3=round(f, 4),
                         dev_pct=round(100*(f-d)/d, 2) if d else np.nan))
    # all-state measured thermoelectric water, needed for the regional import intensity
    pd.DataFrame({'state': direct.index, 'direct_Mm3': direct.round(4).values}).to_csv(
        os.path.join(DERIVED, 'state_thermal_measured_all.csv'), index=False)
    print('  wrote', os.path.join(DERIVED, 'state_thermal_measured_all.csv'))
    df = pd.DataFrame(rows)
    out = os.path.join(DERIVED, 'state_validation_direct_vs_factor.csv')
    df.to_csv(out, index=False); print('  wrote', out)
    print(f'    aggregate deviation over the fifteen states: '
          f'{100*(df.factor_Mm3.sum()-df.direct_Mm3.sum())/df.direct_Mm3.sum():+.1f}%')
    print(f'    median absolute state deviation: {df.dev_pct.abs().median():.1f}%')
    return df


def build_state_intensity(val):
    """State grid water intensity on both bases, L/kWh, 2024.

    Imported here (not at module scope) so that the model can be re-imported after this
    script regenerates the files it depends on.
    """
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import lifecycle_water_model as M
    rows = []
    for s in DC_STATES:
        m = M.STATE_MIX[s]
        nonthermal = sum(m.get(k, 0.0)*M.WF[k] for k in ('hydro', 'solar', 'wind', 'geo'))*GROSSUP
        tw = float(val.loc[val.state == s, 'direct_Mm3'].iloc[0])
        thermal = tw*1e9/(STATE_GEN_TWH[s]*1e9)*GROSSUP        # million m3 -> L, / kWh
        rows.append(dict(state=s, weight=M.DC_WEIGHTS[s],
                         I_factor=round(M._state_intensity(m, 1.0), 4),
                         I_measured=round(thermal + nonthermal, 4)))
    df = pd.DataFrame(rows)
    out = os.path.join(DERIVED, 'state_intensity_direct.csv')
    df.to_csv(out, index=False); print('  wrote', out)
    return df


def open_data_csv(name):
    """Open data/<name> as text; if it is absent, read it from data/<name>.zip."""
    p = os.path.join(DATA, name)
    if os.path.exists(p):
        return open(p, encoding='utf-8-sig')
    return io.TextIOWrapper(zipfile.ZipFile(p + '.zip').open(name), encoding='utf-8-sig')


def build_aqueduct():
    """State water-stress scores, area-weighted from HydroBASINS level-6 sub-basins.

    The baseline file carries the sub-basin to state mapping; the future file is keyed on
    pfaf_id only and is joined back through that mapping.
    """
    base = collections.defaultdict(lambda: collections.defaultdict(lambda: [0.0, 0.0]))
    links = collections.defaultdict(list)
    with open_data_csv('Aqueduct40_baseline_annual_y2023m07d05.csv') as f:
        for row in csv.DictReader(f):
            if row.get('name_0') != 'United States':
                continue
            st = STATE_NAME.get(row.get('name_1', ''))
            if not st:
                continue
            try:    a = float(row['area_km2'])
            except (TypeError, ValueError): continue
            links[row['pfaf_id']].append((st, a))
            for c in ('bws_score', 'w_awr_elp_tot_score'):
                try:    v = float(row[c])
                except (TypeError, ValueError): continue
                if v < 0: continue
                base[st][c][0] += v*a; base[st][c][1] += a
    FUT = {'bau30_ws_x_s':'ws_bau2030', 'bau50_ws_x_s':'ws_bau2050',
           'opt50_ws_x_s':'ws_opt2050', 'pes50_ws_x_s':'ws_pes2050'}
    fut = collections.defaultdict(lambda: collections.defaultdict(lambda: [0.0, 0.0]))
    with open_data_csv('Aqueduct40_future_annual_y2023m07d05.csv') as f:
        for row in csv.DictReader(f):
            pid = row.get('pfaf_id')
            if pid not in links: continue
            for c, k in FUT.items():
                try:    v = float(row[c])
                except (TypeError, ValueError): continue
                if v < 0: continue
                for st, a in links[pid]:
                    fut[st][k][0] += v*a; fut[st][k][1] += a
    rows = []
    for st in DC_STATES:
        d = {'state': st}
        for c, k in (('bws_score', 'bws_2023'), ('w_awr_elp_tot_score', 'power_risk_2023')):
            n, dn = base[st][c]; d[k] = round(n/dn, 4) if dn else ''
        for k in FUT.values():
            n, dn = fut[st][k]; d[k] = round(n/dn, 4) if dn else ''
        rows.append(d)
    out = os.path.join(DERIVED, 'aqueduct_state_scarcity.csv')
    with open(out, 'w', newline='', encoding='utf-8') as f:
        wtr = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wtr.writeheader(); wtr.writerows(rows)
    print('  wrote', out)


if __name__ == '__main__':
    print('STEP 00 | building derived datasets from', DATA)
    print(' reading EIA-923 ...')
    df, w, g = load_eia923()
    print(f'   {len(w):,} cooling-system-months, {len(g):,} generator-months after de-duplication')
    build_state_generation(g)
    build_cooling_factors(w, g)
    val = build_state_validation(w, g)
    build_aqueduct()
    build_state_intensity(val)      # last: needs the model, which reads the files above
    print('done.')
