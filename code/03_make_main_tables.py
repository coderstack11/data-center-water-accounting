#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""STEP 03 - Generate main-text Tables 1 and 2 (LaTeX) from ONE internally consistent model run.
Every value is read from the same run_case() output, so the identities
E_dc = PUE x E_IT, W_grid = E_dc x I and Total = site + grid + fab are auditable.
Output: manuscript/main_tables.tex  (uses the \lkwh{} and \bmc{} unit macros of the manuscript)
Run (from the repository root):  python code/03_make_main_tables.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lifecycle_water_model as M

# Project root = the directory that holds code/, data/ and derived/ (override with PROJECT_ROOT).
BASE = os.environ.get('PROJECT_ROOT', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT  = os.path.join(BASE, 'manuscript', 'main_tables.tex')
Y = list(M.YEARS)


def big(x, nd=1):
    """Fixed-point number with a LaTeX thousands separator, e.g. 1{,}087.3."""
    return f'{x:,.{nd}f}'.replace(',', '{,}')


r  = M.run_case('mid', 'adaptive_warm', 'ref')                                  # reference case
lo = M.run_case('mid', 'adaptive_warm', 'ref', hydro_alloc=0.0)                  # hydropower excluded
hi = M.run_case('mid', 'adaptive_warm', 'ref', hydro_alloc=17.0/M.WF['hydro'])   # Macknick, 17 L/kWh
L = []

# ---------------- Table 1: reference-case trajectory ----------------
CAPTION_1 = r"""\textbf{Modeled water use under the reference case.} The reference case combines mid demand, warm-liquid adoption, the reference grid pathway, location-based load-serving electricity attribution and the central hydropower treatment (the Grubert--Sanders economic allocation). $E_{dc}^{\mathrm{proj}}$ is projected total facility electricity; $E_{IT}=E_{dc}^{\mathrm{proj}}/\mathrm{PUE}_{\mathrm{ref}}$ is the IT load held fixed across cooling comparisons; and $E_{dc}=\mathrm{PUE}_{\mathrm{fleet}}E_{IT}$ is facility electricity under the modeled cooling stock. Every row satisfies $W_{\mathrm{grid}}=E_{dc}I$ and Total $=W_{\mathrm{site}}+W_{\mathrm{grid}}+W_{\mathrm{fab}}$. WUE, water usage effectiveness; PUE, power usage effectiveness; Gen., electricity generation; Site, on-site cooling. The hydropower band ranges from excluding reservoir evaporation to using the Macknick factor of 17~\lkwh{}."""
L += [r'\begin{table}[!t]', r'\centering', r'\scriptsize', r'\renewcommand{\arraystretch}{1.08}',
      r'\setlength{\tabcolsep}{1.6pt}', r'\caption{' + CAPTION_1 + '}', r'\label{tab1}',
      r'\begin{tabular*}{0.985\textwidth}{@{\extracolsep{\fill}}lrrrrrrrrrr@{}}', r'\toprule',
      r'Year & $E_{dc}^{\mathrm{proj}}$ & $E_{IT}$ & PUE & $E_{dc}$ & Fleet WUE & $I$ & Total & Hydro band & Gen. & Site \\',
      r' & (TWh) & (TWh) & & (TWh) & (\lkwh{}) & (\lkwh{}) & (\bmc{}) & (\bmc{}) & (\%) & (\%) \\',
      r'\midrule']
for y in (2027, 2030, 2035, 2040, 2045, 2050):
    i = Y.index(y); z = r.iloc[i]
    L.append(f'{y} & {big(z.E_dc_proj_TWh)} & {big(z.E_IT_TWh)} & {z.PUE:.3f} & {big(z.E_dc_TWh)} & '
             f'{z.WUE:.3f} & {z.I_grid_LkWh:.3f} & {z.W_total_ML/1e6:.3f} & '
             f'{lo.W_total_ML.iloc[i]/1e6:.3f}--{hi.W_total_ML.iloc[i]/1e6:.3f} & '
             f'{z.theta_grid*100:.1f} & {z.theta_site*100:.1f} \\\\')
m = r.year >= 2027
L += [r'\midrule',
      f'\\multicolumn{{7}}{{l}}{{Cumulative 2027--2050}} & {r.W_total_ML[m].sum()/1e6:.2f} & '
      f'{lo.W_total_ML[m].sum()/1e6:.2f}--{hi.W_total_ML[m].sum()/1e6:.2f} & & \\\\',
      r'\bottomrule', r'\end{tabular*}', r'\end{table}']

# ---------------- Table 2: water factors ----------------
CAPTION_2 = r"""\textbf{Water factors used in the electricity-generation module.} Measured thermal values are consumption- or withdrawal-weighted factors from reporting plants in the 2024 U.S. Energy Information Administration Form EIA-923 data. Non-thermal values are taken from the cited literature. The national grid rows use measured 2024 anchors. The data center-weighted row is the consumption-basis, load-serving intensity across the fifteen EPRI states. PV, photovoltaic; DC-weighted, data center-weighted. The reference hydropower value uses the Grubert--Sanders allocation; sensitivity cases exclude hydropower evaporation or use the Macknick median."""
L += ['', r'\begin{table}[!t]', r'\centering', r'\footnotesize', r'\renewcommand{\arraystretch}{1.05}',
      r'\setlength{\tabcolsep}{4pt}', r'\caption{' + CAPTION_2 + '}', r'\label{tab2}',
      r'\begin{tabularx}{\textwidth}{@{}>{\raggedright\arraybackslash}p{0.22\textwidth}'
      r'>{\centering\arraybackslash}p{0.18\textwidth}>{\centering\arraybackslash}p{0.18\textwidth}'
      r'>{\raggedright\arraybackslash}X@{}}',
      r'\toprule', r'Technology & Consumption (\lkwh{}) & Withdrawal (\lkwh{}) & Basis \\', r'\midrule']
SIM0 = r'${\sim}0$'
ROWS = [('Gas combined cycle', 'gas_cc',    'Measured, EIA-923 2024'),
        ('Nuclear',            'nuclear',   'Measured, EIA-923 2024'),
        ('Coal steam',         'coal',      'Measured, EIA-923 2024'),
        ('Gas steam / other',  'gas_other', 'Measured, EIA-923 2024'),
        ('Biomass',            'bio',       'Measured, EIA-923 2024'),
        ('Geothermal',         'geo',       'Literature'),
        ('Hydropower',         'hydro',     'Grubert--Sanders allocation'),
        ('Solar PV',           'solar',     'Literature (panel washing)'),
        ('Wind',               'wind',      'Literature')]
for nm, k, basis in ROWS:
    c = M.WF[k]; w = M.WF_WITH.get(k)
    if k == 'hydro':        # sensitivity bounds 0 and 17; withdrawal = consumption (evaporation)
        cs, ws = f'{c:.2f} (0--17)', f'{w:.2f}'
    else:
        cs = SIM0 if c < 0.005 else f'{c:.2f}'
        ws = SIM0 if (w is None or w < 0.005) else f'{w:.1f}'
    L.append(f'{nm} & {cs} & {ws} & {basis} \\\\')
i24  = Y.index(2024)
I24  = M.grid_intensity('ref', 1.0)[i24]                          # national, measured anchor
Iw24 = M.grid_intensity('ref', 1.0, basis='withdrawal')[i24]
Idc  = M.grid_intensity_dcweighted('ref', 1.0, 2024)              # DC-weighted, consumption basis
L += [r'\midrule',
      f'Grid, 2024 (national) & {I24:.2f} & {Iw24:.1f} & Measured anchor, $+${M.TD_LOSS*100:.1f}\\% losses \\\\',
      f'Grid, 2024 (DC-weighted) & {Idc:.2f} & -- & Consumption basis, EPRI 15-state loads \\\\',
      r'\bottomrule', r'\end{tabularx}', r'\end{table}']

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as fh:
    fh.write('\n'.join(L) + '\n')
print('wrote', OUT)
