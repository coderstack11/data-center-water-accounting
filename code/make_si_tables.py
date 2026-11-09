#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""Generate Supplementary Tables S1-S11 (LaTeX) from the model.
Every number in the table bodies is computed by lifecycle_water_model.py; the descriptive
tables (S1, S9, S11) take their numeric entries from the model parameters.
Output: supplementary/si_tables.tex  (uses the \lkwh{} and \bmc{} unit macros of the SI)
Run (from the repository root):  python code/make_si_tables.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lifecycle_water_model as M

# Project root = the directory that holds code/, data/ and derived/ (override with PROJECT_ROOT).
BASE = os.environ.get('PROJECT_ROOT', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT  = os.path.join(BASE, 'supplementary', 'si_tables.tex')
Y = list(M.YEARS); i50 = Y.index(2050)
T = []                                    # one list of LaTeX lines per table
END = [r'\bottomrule', r'\end{tabular}', r'\end{table}']
END_RESIZED = [r'\bottomrule', r'\end{tabular}%', '}', r'\end{table}']


def big(x, nd=1):
    """Fixed-point number with a LaTeX thousands separator, e.g. 1{,}291."""
    return f'{x:,.{nd}f}'.replace(',', '{,}')


def pue(p):
    """PUE to three decimals, dropping a trailing zero (1.145, 1.26)."""
    s = f'{p:.3f}'
    return s[:-1] if s.endswith('0') else s


def tri(v, nd):
    """(low, central, high) triple."""
    return '(' + ', '.join(f'{x:.{nd}f}' for x in v) + ')'


# Captions as in the Supplementary Information.
CAP = {
    'tabS1': r"""\textbf{Structural alternatives to constant post-2030 demand growth.} The four structural alternatives share the LBNL 2025 Update reference anchor of 649~TWh in 2030 and differ only in their post-2030 functional form. Their modeled demand and water outcomes are shown in main-text Fig.~4e,f.""",
    'tabS2': r"""\textbf{Modeled water use in 2050 across the demand $\times$ grid matrix.} All cases use central warm-liquid cooling deployment, location-based electricity attribution and the central hydropower treatment. Electricity values in the demand labels refer to the projected facility-electricity pathways before adjustment for the modeled cooling stock. This is a scenario range, not a probabilistic confidence interval. Component shares are percentages of the annual modeled total.""",
    'tabS3': r"""\textbf{State data center load weights and 2024 load-serving grid water intensities.} Load weights follow the EPRI fifteen-state distribution, which represents 80\% of national data center load. The weights are renormalized across the fifteen states when calculating weighted averages. Intensities use the consumption basis: measured in-state thermoelectric water plus factor-based non-thermal water, with net imports represented by the state's synchronous-interconnection pool.""",
    'tabS4': r"""\textbf{Load-weighted summary of the bounded water-stress characterization.} Aqueduct water-stress scores range from 0 to 5, with higher values indicating greater stress. Scores are area-weighted from HydroBASINS level-6 sub-basins to states and then weighted by the EPRI fifteen-state data center load distribution. Grid intensity refers to 2024; water stress refers to the Aqueduct baseline. BAU, business as usual.""",
    'tabS5': r"""\textbf{State grid water intensity under two accounting bases.} Production basis combines each state's measured thermoelectric water consumption with factor-based non-thermal water for its in-state generation. Consumption basis combines the resulting in-state intensity with the estimated intensity of imported electricity from the state's synchronous interconnection pool, weighted by the state's self-supply fraction. The factor-based column reports estimates obtained by applying national technology-specific water factors to each state's generation mix.""",
    'tabS6': r"""\textbf{Central cooling technology parameters used in the stock model.} WUE is site water usage effectiveness in \lkwh{} of IT electricity; PUE is power usage effectiveness. The legacy-pool PUE is time varying rather than a fixed class value. Low-to-high ranges and the warm-liquid climate adjustment are given in Supplementary Table~\ref{tabS7}.""",
    'tabS7': r"""\textbf{Cooling technology parameters with uncertainty ranges and climate dependence.} Technology rows report (low, central, high) values. Warm-liquid cooling corresponds to ASHRAE facility water class W45; the WUE/PUE values are modeled parameters. The climate rows show the multipliers/adders applied to the warm-liquid class.""",
    'tabS8': r"""\textbf{Combined accelerator-fabrication water under the reference-demand pathway.} $W_{\mathrm{fab}}$ includes direct process freshwater and generation water associated with fabrication electricity.""",
    'tabS9': r"""\textbf{Fabrication-electricity inputs and accounting boundary.} These inputs define the generation-water term added to direct fabrication freshwater. Annual combined $W_{\mathrm{fab}}$ values are reported in Supplementary Table~\ref{tabS8}, and Supplementary Fig.~S7 shows the modeled direct/electricity split.""",
    'tabS10': r"""\textbf{Electricity-attribution conventions used in the analysis.} Assigned grid-water intensities are the values used for the 2050 comparison in main-text Fig.~4. Marginal coal is treated as an upper-bound consequential convention; the market-based case represents contracted wind/solar procurement.""",
    'tabS11': r"""\textbf{Comparison with Xiao et al. (2025).} The two analyses address related questions but use different horizons, boundaries and accounting treatments.""",
}

ref = M.run_case('mid', 'adaptive_warm', 'ref')            # reference case

# ---- S1: structural post-2030 demand forms ---------------------------------------------
cg = {k: M.DEMAND[k][1]*100 for k in ('low', 'mid', 'high')}
T.append([r'\begin{table}[!t]\centering\footnotesize',
          r'\caption{' + CAP['tabS1'] + '}', r'\label{tabS1}',
          r'\begin{tabular}{p{0.25\textwidth}p{0.65\textwidth}}', r'\toprule',
          r'Pathway & Post-2030 form \\', r'\midrule',
          r'Constant share & Data center share of national electricity is held at its 2030 value. \\',
          r'Logistic saturation & Demand approaches a saturation ceiling rather than continuing exponential growth. \\',
          r'Declining growth & The annual growth rate declines toward the national-grid growth rate. \\',
          r'Interconnection capped & Annual additions are constrained by an interconnection-cap assumption. \\',
          f"Reference CAGR & Demand continues at {cg['mid']:.1f}\\% yr$^{{-1}}$ after 2030. \\\\",
          f"Low / high CAGR & Demand continues at {cg['low']:.1f} / {cg['high']:.1f}\\% yr$^{{-1}}$ after 2030. \\\\"]
         + END)

# ---- S2: 2050 demand x grid matrix -----------------------------------------------------
rows = []
for d, name in (('low', 'Low'), ('mid', 'Reference'), ('high', 'High')):
    e50 = M.demand_path(d)[i50]
    for j, (g, gl) in enumerate((('slow', 'slow'), ('ref', 'reference'), ('accel', 'accelerated'))):
        z = M.run_case(d, 'adaptive_warm', g).iloc[i50]
        lab = (name, f'({big(e50, 0)} TWh)', '')[j]
        rows.append(f'{lab} & {gl} & {z.W_total_ML/1e6:.2f} & {z.theta_grid*100:.1f} & '
                    f'{z.theta_site*100:.1f} & {z.theta_fab*100:.2f} \\\\')
    rows.append(r'\addlinespace')
T.append([r'\begin{table}[!t]\centering\small',
          r'\caption{' + CAP['tabS2'] + '}', r'\label{tabS2}',
          r'\begin{tabular}{llcccc}', r'\toprule',
          r'Demand & Grid & Total (\bmc{} yr$^{-1}$) & Generation (\%) & On-site (\%) & Fabrication (\%) \\',
          r'\midrule'] + rows + END)

# ---- S3: state load weights and 2024 load-serving intensities --------------------------
sts = sorted(M.DC_WEIGHTS.items(), key=lambda x: -x[1]); half = (len(sts)+1)//2
cell = lambda s, w: f'{s} & {w:.3f} & {M.state_intensity(s):.2f}'
rows = [cell(*sts[i]) + ' & ' + (cell(*sts[i+half]) if i+half < len(sts) else ' & & ') + r' \\'
        for i in range(half)]
T.append([r'\begin{table}[!t]\centering\small',
          r'\caption{' + CAP['tabS3'] + '}', r'\label{tabS3}',
          r'\begin{tabular}{lcc|lcc}', r'\toprule',
          r'State & Weight & $I$ (\lkwh{}) & State & Weight & $I$ (\lkwh{}) \\', r'\midrule']
         + rows + END)

# ---- S4: load-weighted water stress ----------------------------------------------------
T.append([r'\begin{table}[!t]\centering\small',
          r'\caption{' + CAP['tabS4'] + '}', r'\label{tabS4}',
          r'\begin{tabular}{lcc}', r'\toprule',
          r'Metric & Baseline / 2024 & 2050 BAU \\', r'\midrule',
          f"Data center-weighted load-serving grid intensity (\\lkwh{{}}) & "
          f"{M.grid_intensity_dcweighted('ref', 1.0, 2024):.2f} & -- \\\\",
          f"Load-weighted Aqueduct water-stress score & {M.scarcity_weight(2023):.2f} & "
          f"{M.scarcity_weight(2050, 'bau'):.2f} \\\\"] + END)

# ---- S5: production, consumption and factor bases --------------------------------------
rows = [f"{s} & {M.self_supply_fraction(s):.3f} & {M.state_intensity(s, 1.0, 'production'):.2f} & "
        f"{M.state_intensity(s, 1.0, 'consumption'):.2f} & {M.state_intensity(s, 1.0, 'factor'):.2f} \\\\"
        for s, _ in sts]
T.append([r'\begin{table}[!t]\centering\footnotesize',
          r'\caption{' + CAP['tabS5'] + '}', r'\label{tabS5}',
          r'\resizebox{\textwidth}{!}{%', r'\begin{tabular}{lrrrr}', r'\toprule',
          r'State & Self-supply fraction & $I$ production (\lkwh{}) & $I$ consumption (\lkwh{}) & $I$ factor (\lkwh{}) \\',
          r'\midrule'] + rows + END_RESIZED)

# ---- S6: central cooling technology parameters -----------------------------------------
rows = []
for nm, k, role in (('Legacy enterprise', 'leg', 'non-AI installed base'),
                    ('AI evaporative liquid-assist', 'aievap', 'AI baseline; bridge technology'),
                    ('Legacy dry chiller', 'drychiller', 'break-even comparator'),
                    (r'Warm-liquid 45$^{\circ}$C', 'aidry', 'headline adoption target'),
                    ('Two-phase immersion', 'ferveret', 'zero-site-water bound')):
    w, p = M.COOL_C3[k][0][1], M.COOL_C3[k][1][1]
    rows.append(f"{nm} & {w:.2f} & {'time varying' if k == 'leg' else pue(p)} & {role} \\\\")
T.append([r'\begin{table}[!t]\centering\small',
          r'\caption{' + CAP['tabS6'] + '}', r'\label{tabS6}',
          r'\begin{tabular}{lccl}', r'\toprule', r'Class & WUE & PUE & Role in model \\', r'\midrule']
         + rows + END)

# ---- S7: parameter ranges and climate adjustment ---------------------------------------
rows = []
for nm, k, nw, npue, role in (('Legacy enterprise', 'leg', 2, None, 'non-AI pool'),
                              ('AI evaporative liquid-assist', 'aievap', 2, 3, 'AI baseline'),
                              ('Legacy dry chiller', 'drychiller', 2, 2, 'break-even comparator'),
                              ('Warm-liquid W45', 'aidry', 3, 2, 'advanced-cooling target'),
                              ('Two-phase immersion', 'ferveret', 3, 2, 'zero-site-water bound')):
    w3, p3 = M.COOL_C3[k]
    ps = (f"calibrated in 2024; {M.LEG_PUE_2050_BAND['mid']:.2f} (2050 central)" if k == 'leg'
          else tri(p3, npue))
    rows.append(f'{nm} & {tri(w3, nw)} & {ps} & {role} \\\\')
rows.append(r'\midrule')
for cz in ('cool', 'temperate', 'hot'):
    mw, dp = M.CLIMATE_ADJ[cz]
    rows.append(f'Warm-liquid, {cz} climate & $\\times {mw:.1f}$ & ${dp:+.3f}$ & climate adjustment \\\\')
wm, pm = M.climate_weighted_aidry('mid')
rows.append(f'Warm-liquid, load weighted & {wm:.3f} & {pm:.3f} & fifteen-state average \\\\')
T.append([r'\begin{table}[!t]\centering\footnotesize',
          r'\caption{' + CAP['tabS7'] + '}', r'\label{tabS7}',
          r'\resizebox{\textwidth}{!}{%', r'\begin{tabular}{lccc}', r'\toprule',
          r'Class / climate case & Site WUE (\lkwh{}) & PUE & Role / adjustment \\', r'\midrule']
         + rows + END_RESIZED)

# ---- S8: combined accelerator-fabrication water, reference demand ----------------------
rows = []
for y in (2024, 2027, 2030, 2040, 2050):
    z = ref.iloc[Y.index(y)]
    rows.append(f'{y} & {z.W_fab_ML/1e6:.4f} & {z.theta_fab*100:.2f} \\\\')
T.append([r'\begin{table}[!t]\centering\small',
          r'\caption{' + CAP['tabS8'] + '}', r'\label{tabS8}',
          r'\begin{tabular}{lcc}', r'\toprule',
          r'Year & $W_{\mathrm{fab}}$ (\bmc{} yr$^{-1}$) & Share of modeled total (\%) \\', r'\midrule']
         + rows + END)

# ---- S9: fabrication-electricity inputs and boundary -----------------------------------
T.append([r'\begin{table}[!t]\centering\small',
          r'\caption{' + CAP['tabS9'] + '}', r'\label{tabS9}',
          r'\begin{tabular}{p{0.32\textwidth}p{0.22\textwidth}p{0.38\textwidth}}', r'\toprule',
          r'Input / boundary & Value & Treatment \\', r'\midrule',
          f"Fabrication electricity & {big(M.KWH_PER_WAFER['mid'], 0)}~kWh per 300-mm-equivalent wafer & "
          r"central model input from TSMC company-level energy and wafer shipments \\",
          f"Taiwan grid water intensity & {M.TW_I['lo']:.2f}--{M.TW_I['hi']:.2f}~\\lkwh{{}} & "
          r"uncertainty band because no measured Taiwanese cooling-water survey is available \\",
          r'U.S./Taiwan allocation & modeled onshore fabrication share & weights generation water between the U.S. and Taiwanese grids \\',
          r'Fabrication water boundary & direct + electricity-generation water & excludes fab construction and other unmodeled process-chain stages \\']
         + END)

# ---- S10: electricity-attribution conventions (2050 assigned intensities) --------------
rows = []
for att, nm, nd, interp in (('average', 'Location-based average', 3, 'load-serving average, reference grid'),
                            ('marginal_gas', 'Marginal gas combined cycle', 3, 'consequential gas-CC factor'),
                            ('marginal_coal', 'Marginal coal', 2, 'consequential upper-bound factor'),
                            ('market', 'Market-based contracted wind/solar', 3, 'procurement-accounting factor')):
    I50 = M.run_case('mid', 'adaptive_warm', 'ref', attribution=att).I_grid_LkWh.iloc[i50]
    rows.append(f'{nm} & {I50:.{nd}f} & {interp} \\\\')
T.append([r'\begin{table}[!t]\centering\footnotesize',
          r'\caption{' + CAP['tabS10'] + '}', r'\label{tabS10}',
          r'\begin{tabular}{lcc}', r'\toprule',
          r'Attribution & Assigned grid intensity (\lkwh{}) & Interpretation \\', r'\midrule']
         + rows + END)

# ---- S11: comparison with Xiao et al. (2025) -------------------------------------------
T.append([r'\begin{table}[!h]\centering\footnotesize',
          r'\caption{' + CAP['tabS11'] + '}', r'\label{tabS11}',
          r'\renewcommand{\arraystretch}{1.8}',
          r'\resizebox{\textwidth}{!}{%',
          r'\begin{tabular}{p{0.18\textwidth}p{0.36\textwidth}p{0.36\textwidth}}', r'\toprule',
          r'Dimension & Xiao et al. (2025) & Present analysis \\', r'\midrule',
          r'Time horizon & Operational AI servers, 2024--2030 & U.S. data center growth, 2023--2050 \\',
          r'Spatial resolution & State-level AI-server allocation with state PUE, WUE and grid factors & National trajectory plus fifteen-state load-serving intensities; production and factor bases retained as robustness checks \\',
          r'Generation-water treatment & State grid water factors projected with ReEDS; hydropower evaporation contributes to grid water footprint & Measured 2024 EIA-923 thermoelectric water plus literature non-thermal factors; AEO2026 pathways; '
          f"hydropower allocation tested at 0, {M.WF['hydro']:.2f} and 17~\\lkwh{{}} \\\\",
          r'WUE / technology evolution & Climate-dependent state WUE with best/base/worst efficiency and advanced-liquid-cooling adoption cases & Explicit cooling-stock turnover across legacy, evaporative and advanced pools; low/central/high WUE and PUE sets with climate adjustment \\',
          r'PUE coupling & State PUE changes facility electricity and the resulting footprints & IT load held fixed; cooling-specific PUE changes facility electricity and generation water, with an explicit break-even test \\',
          r'Water scarcity & State water scarcity used in spatial siting and mitigation analysis & Aqueduct 4.0 sub-basin stress aggregated to states; baseline and future stress used as a bounded characterization \\',
          r'Electricity attribution & Local grid (Scope 2) water factors; no parallel marginal/market accounting cases & Location-based load-serving account plus marginal gas, marginal coal and market-based renewable attribution, separated from physical dispatch \\']
         + END_RESIZED)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as fh:
    fh.write('\n\n'.join('\n'.join(t) for t in T) + '\n')
print('wrote', OUT, f'({len(T)} tables)')
