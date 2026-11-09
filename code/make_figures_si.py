#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Supplementary figures S1-S9.  All values are computed live from the model
(and, for Fig. S2, directly from the raw EIA-923 Schedule 8D workbook).
Output: figures/  (override with FIGOUT; raw data are read from data/, override with DATADIR)
Run (from the repository root):  python code/make_figures_si.py
"""
import os, sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from collections import defaultdict
import warnings; warnings.filterwarnings('ignore')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pubstyle import *
import lifecycle_water_model as M

# Project root = the directory that holds code/, data/ and derived/ (override with PROJECT_ROOT).
ROOT = os.environ.get('PROJECT_ROOT', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.environ.get('FIGOUT', os.path.join(ROOT, 'figures'))
DATA = os.environ.get('DATADIR', os.path.join(ROOT, 'data'))
os.makedirs(OUT, exist_ok=True)
Y = M.YEARS

# ---------------- S1 | demand pathways ----------------
def figS1():
    fig, a = plt.subplots(figsize=(HALFW*1.35, 72*MM)); panel(a, 'a', dx=-0.10); ygrid(a)
    a.axvspan(2030, 2050, color='#F5F5F5', zorder=0)
    a.text(2040, 1930, 'CAGR extrapolation (2.0 / 3.5 / 5.0% yr$^{-1}$)\nbeyond published horizons', fontsize=5.9,
           color=SOFT, ha='center')
    _i30 = list(Y).index(2030)
    for scn, col in [('low', '#9DB9CE'), ('mid', C_GRID), ('high', '#123E5C')]:
        lab = f'{scn} ({M.demand_path(scn)[_i30]:,.0f} TWh in 2030)'
        E = M.demand_path(scn)
        a.plot(Y, E, color=col, lw=1.6 if scn == 'mid' else 1.1, label=lab)
        a.annotate(f'{E[-1]:,.0f}', (2050, E[-1]), xytext=(3, 0), textcoords='offset points',
                   fontsize=6.0, color=col, va='center')
    _d23, _d24 = M.LBNL_2023, M.LBNL_2024
    a.plot([2023, 2024], [_d23, _d24], 'o', ms=3.6, color=INK, zorder=5)
    a.annotate(f'LBNL 2025 Update\n{_d23:.0f} (2023), {_d24:.0f} (2024)',
               (2024, _d24), xytext=(-6, 41), textcoords='offset points',
               fontsize=5.8, color=INK, ha='left',
               arrowprops=dict(arrowstyle='-', lw=0.5, color=INK, shrinkA=0, shrinkB=3))
    _v30 = [M.demand_path(k)[_i30] for k in ('low', 'mid', 'high')]
    for v in _v30: a.plot([2030], [v], 'o', ms=3.6, color=INK, zorder=5)
    a.plot([2028], [M.LBNL_2028_CHECK], 'D', ms=3.4, color=INK, zorder=5)
    a.annotate(f'LBNL 2030 scenarios\n{_v30[0]:,.0f}\u2013{_v30[2]:,.0f} TWh',
               (2030, _v30[2]), xytext=(-6, 40), textcoords='offset points',
               fontsize=5.8, color=INK, ha='right',
               arrowprops=dict(arrowstyle='-', lw=0.5, color=INK, shrinkA=0, shrinkB=3))
    a.set_xlim(2023, 2050); a.set_ylim(0, 2300)
    a.set_ylabel(r'Projected data-centre electricity $E_{dc}^{\mathrm{proj}}$ (TWh yr$^{-1}$)')
    a.legend(loc='upper left', fontsize=6.0)
    save(fig, f'{OUT}/figS1_demand')

# ---------------- S2 | EIA-923 audit ----------------
def _eia_audit():
    import openpyxl
    wb = openpyxl.load_workbook(f'{DATA}/Cooling_Boiler_Generator_Data_Detail_2024.xlsx', read_only=True)
    ws = wb['Detail']; seen = {}
    def num(x):
        try: return float(x)
        except Exception: return 0.0
    for r in ws.iter_rows(min_row=4, values_only=True):
        state, plant, cool, month, tech = r[1], r[2], r[8], r[5], r[9]
        if not state or cool is None: continue
        key = (plant, cool, month)
        if key not in seen: seen[key] = (state, str(tech) if tech else 'Other', num(r[29]), num(r[30]))
    st_c, st_w, tech_c = defaultdict(float), defaultdict(float), defaultdict(float)
    def lab(t):
        t = t.lower()
        if 'nuclear' in t: return 'Nuclear'
        if 'coal' in t: return 'Coal steam'
        if 'combined cycle' in t: return 'Gas combined cycle'
        if 'steam turbine' in t and 'gas' in t: return 'Gas steam turbine'
        if 'petroleum' in t: return 'Petroleum'
        if 'wood' in t or 'biomass' in t: return 'Biomass'
        return 'Other'
    for state, t, wd, cn in seen.values():
        st_c[state] += cn; st_w[state] += wd; tech_c[lab(t)] += cn
    return st_c, st_w, tech_c

def figS2():
    st_c, st_w, tech_c = _eia_audit()
    fig = plt.figure(figsize=(FULLW, 74*MM))
    gs = fig.add_gridspec(1, 3, wspace=0.42, left=0.06, right=0.985, top=0.90, bottom=0.14,
                          width_ratios=[1, 1, 0.9])
    tops_c = sorted(st_c.items(), key=lambda x: -x[1])[:12]
    a = fig.add_subplot(gs[0]); panel(a, 'a', dx=-0.14)
    a.grid(axis='x', color=LINEC, lw=0.5, alpha=0.55); a.set_axisbelow(True)
    yp = np.arange(len(tops_c))[::-1]
    a.barh(yp, [v/1e3 for _, v in tops_c], 0.62, color=C_GRID, edgecolor='white', lw=0.4)
    a.set_yticks(yp); a.set_yticklabels([s for s, _ in tops_c], fontsize=6.2)
    a.set_xlabel('Consumption (billion gallons, 2024)')
    ptitle(a, f'Top states \u00b7 national total {sum(st_c.values())/1e3:.0f} Bgal')
    tops_w = sorted(st_w.items(), key=lambda x: -x[1])[:12]
    b = fig.add_subplot(gs[1]); panel(b, 'b', dx=-0.14)
    b.grid(axis='x', color=LINEC, lw=0.5, alpha=0.55); b.set_axisbelow(True)
    yp = np.arange(len(tops_w))[::-1]
    b.barh(yp, [v/1e3 for _, v in tops_w], 0.62, color='#6A88A5', edgecolor='white', lw=0.4)
    b.set_yticks(yp); b.set_yticklabels([s for s, _ in tops_w], fontsize=6.2)
    b.set_xlabel('Withdrawal (billion gallons, 2024)')
    ptitle(b, f'Withdrawal \u00b7 national {sum(st_w.values())/1e3/1e3:.0f} trillion gal')
    c = fig.add_subplot(gs[2]); panel(c, 'c', dx=-0.16)
    c.grid(axis='x', color=LINEC, lw=0.5, alpha=0.55); c.set_axisbelow(True)
    tt = sorted(tech_c.items(), key=lambda x: -x[1])[:6]
    tot = sum(tech_c.values())
    yp = np.arange(len(tt))[::-1]
    c.barh(yp, [v/tot*100 for _, v in tt], 0.62, color='#3E5F7E', edgecolor='white', lw=0.4)
    for y0, (nm, v) in zip(yp, tt):
        c.annotate(f'{v/tot*100:.0f}%', (v/tot*100, y0), xytext=(3, 0),
                   textcoords='offset points', fontsize=6.0, va='center')
    c.set_yticks(yp); c.set_yticklabels([nm for nm, _ in tt], fontsize=6.2)
    c.set_xlabel('Share of consumption (%)'); c.set_xlim(0, 44)
    ptitle(c, 'By technology')
    save(fig, f'{OUT}/figS2_eia_audit')

# ---------------- S3 | generation mix ----------------
def figS3():
    fig = plt.figure(figsize=(FULLW, 72*MM))
    gs = fig.add_gridspec(1, 2, wspace=0.26, left=0.065, right=0.985, top=0.90, bottom=0.20)
    order = ['coal', 'gas_other', 'gas_cc', 'nuclear', 'other', 'geo', 'bio', 'hydro', 'solar', 'wind']
    cols = {'coal': '#4D4D4D', 'gas_other': '#8A7BA8', 'gas_cc': '#B3A6C9', 'nuclear': '#D98032',
            'other': '#C9C9C9', 'geo': '#B98A52', 'bio': '#8C6D46', 'hydro': '#2A6F97',
            'solar': '#F0C24B', 'wind': '#57A583'}
    labs = {'coal': 'Coal', 'gas_other': 'Gas steam', 'gas_cc': 'Gas CC', 'nuclear': 'Nuclear',
            'other': 'Other', 'geo': 'Geo', 'bio': 'Bio', 'hydro': 'Hydro', 'solar': 'Solar', 'wind': 'Wind'}
    a = fig.add_subplot(gs[0]); panel(a, 'a', dx=-0.09)
    mx = M.mix_path('ref')
    a.stackplot(Y[1:], *[100*np.array(mx[k][1:]) for k in order],
                colors=[cols[k] for k in order], labels=[labs[k] for k in order],
                edgecolor='white', lw=0.25)
    a.set_xlim(2024, 2050); a.set_ylim(0, 100); a.set_ylabel('Generation share (%)')
    a.legend(loc='lower center', bbox_to_anchor=(0.5, -0.32), ncol=5, fontsize=5.3,
             handlelength=0.9, columnspacing=0.8, handletextpad=0.35)
    ptitle(a, 'Reference mix: EIA 2024 actual \u2192 AEO2026 2050')
    b = fig.add_subplot(gs[1]); panel(b, 'b', dx=-0.09); ygrid(b)
    for scn, col, lab in [('slow', S_SLOW, 'slow'), ('ref', S_REF, 'reference'), ('accel', S_ACC, 'accelerated')]:
        mx = M.mix_path(scn)
        re = 100*sum(np.array(mx[k]) for k in ['wind', 'solar', 'hydro', 'bio', 'geo'])
        b.plot(Y[1:], re[1:], color=col, lw=1.4, label=lab)
        b.annotate(f'{re[-1]:.0f}%', (2050, re[-1]), xytext=(3, 0), textcoords='offset points',
                   fontsize=6.0, color=col, va='center')
    b.set_xlim(2024, 2050); b.set_ylim(0, None)
    b.set_ylabel('Renewable share incl. hydro (%)')
    b.legend(loc='upper left', fontsize=6.0)
    ptitle(b, 'Renewable share by grid scenario')
    save(fig, f'{OUT}/figS3_genmix')

# ---------------- S5 | cooling adoption mechanics ----------------
def figS5_cooling_adoption():
    fig = plt.figure(figsize=(FULLW, 72*MM))
    gs = fig.add_gridspec(1, 3, wspace=0.36, left=0.06, right=0.985, top=0.90, bottom=0.14)
    a = fig.add_subplot(gs[0]); panel(a, 'a', dx=-0.14); ygrid(a)
    ai = M.ai_share_path()
    a.plot(Y, 100*ai, color=C_GRID, lw=1.5)
    # Anchors are read from the model rather than hardcoded, so the diamonds sit on the curve.
    _iy = list(M.YEARS)
    anchors = [(2024, 'LBNL 2025 Update'), (2030, 'LBNL-implied 2030')]
    for x, lab in anchors:
        v = 100*ai[_iy.index(x)]
        a.plot([x], [v], 'D', ms=3.8, color=INK, zorder=5)
        _off = (8, -30) if x == 2024 else (0, 16)
        a.annotate(f'{lab}\n{v:.0f}% of IT', (x, v), xytext=_off,
                   textcoords='offset points', fontsize=5.4,
                   ha='left' if x == 2024 else 'center',
                   arrowprops=dict(arrowstyle='-', lw=0.5, color=INK, shrinkA=0, shrinkB=3))
    a.plot(Y[Y >= 2030], 100*ai[Y >= 2030], color=C_GRID, lw=1.5, ls=(0, (3, 2)))
    _ai = M.ai_share_path()
    a.annotate(f'extrapolated\n({_ai[list(M.YEARS).index(2040)]:.2f} by 2040, {_ai[-1]:.2f} by 2050)',
               (2037, 88), fontsize=5.6, color=SOFT)
    a.set_xlim(2023, 2050); a.set_ylim(0, 100)
    a.set_ylabel('AI share of IT electricity (%)')
    ptitle(a, 'Anchored AI-share path')
    b = fig.add_subplot(gs[1]); panel(b, 'b', dx=-0.14); ygrid(b)
    for ds, col, lab in [('slow', '#9DB9CE', r'slow ($a_{\mathrm{new}}(2030)$=0.90, L=6)'),
                         ('base', C_GRID, 'base (0.95, L=5)'),
                         ('fast', '#123E5C', 'fast (1.00, L=4)')]:
        s = M.adv_share_path(ds)
        b.plot(Y, 100*s, color=col, lw=1.6 if ds == 'base' else 1.1, label=lab)
    b.set_xlim(2023, 2050); b.set_ylim(0, 100)
    b.set_ylabel('Advanced-cooling share of AI stock (%)')
    b.legend(loc='lower right', fontsize=5.7)
    ptitle(b, 'Stock turnover of the AI fleet')
    c = fig.add_subplot(gs[2]); panel(c, 'c', dx=-0.14); ygrid(c)
    for ds, col in [('slow', '#9DB9CE'), ('base', C_GRID), ('fast', '#123E5C')]:
        w, p = M.cooling_series('adaptive_warm', ds)
        c.plot(Y, p, color=col, lw=1.6 if ds == 'base' else 1.1)
    c.set_xlim(2023, 2050); c.set_ylim(1.05, 1.50)
    c.set_ylabel('Fleet PUE')
    c.annotate('adoption-weighted fleet PUE falls\nas warm-liquid displaces legacy', (2033, 1.17),
               fontsize=5.8, color=SOFT, ha='center')
    ptitle(c, 'Fleet PUE under turnover')
    save(fig, f'{OUT}/figS5_cooling_adoption')

# ---------------- S6 | chip-fab chain ----------------
def figS6_fab():
    fb = M.fab_water('mid')
    r = M.run_case('mid', 'adaptive_warm', 'ref')
    fig = plt.figure(figsize=(FULLW, 70*MM))
    gs = fig.add_gridspec(1, 3, wspace=0.40, left=0.06, right=0.985, top=0.90, bottom=0.14)
    a = fig.add_subplot(gs[0]); panel(a, 'a', dx=-0.15); ygrid(a)
    a.plot(Y, fb['N_gpu']/1e6, color=C_FAB, lw=1.5)
    a.annotate(f"{fb['N_gpu'][1]/1e6:.1f}M (2024)", (2024, fb['N_gpu'][1]/1e6),
               xytext=(5, 4), textcoords='offset points', fontsize=5.9)
    a.annotate(f"{fb['N_gpu'][-1]/1e6:.1f}M", (2050, fb['N_gpu'][-1]/1e6),
               xytext=(-4, 5), textcoords='offset points', fontsize=5.9, ha='right')
    a.set_xlim(2023, 2050); a.set_ylabel('US-deployed accelerators shipped (M yr$^{-1}$)')
    ptitle(a, 'Shipment chain (mid demand)')
    b = fig.add_subplot(gs[1]); panel(b, 'b', dx=-0.15); ygrid(b)
    b.plot(Y, fb['W_fab']/1e9, color=C_FAB, lw=1.5)
    b.annotate(f"{fb['W_fab'][1]/1e9:.2f} GL (2024)", (2024, fb['W_fab'][1]/1e9),
               xytext=(5, 4), textcoords='offset points', fontsize=5.9)
    b.annotate(f"{fb['W_fab'][-1]/1e9:.2f} GL", (2050, fb['W_fab'][-1]/1e9),
               xytext=(-4, 5), textcoords='offset points', fontsize=5.9, ha='right')
    b.set_xlim(2023, 2050); b.set_ylabel('Fabrication water (GL yr$^{-1}$)')
    ptitle(b, 'Ultrapure water and the generation water behind it')
    c = fig.add_subplot(gs[2]); panel(c, 'c', dx=-0.15); ygrid(c)
    m = r.year >= 2027
    c.plot(r.year[m], 100*r.theta_fab[m], color=C_FAB, lw=1.5)
    _sh = 100*r.theta_fab[m]
    c.set_xlim(2027, 2050); c.set_ylim(0, float(_sh.max())*1.35)
    c.set_ylabel('Chip-fab share of $W_{\\mathrm{total}}$ (%)')
    c.annotate(f'{_sh.iloc[0]:.2f}% (2027) \u2192 {_sh.iloc[-1]:.2f}% (2050)',
               (0.5, 0.10), xycoords='axes fraction',
               fontsize=5.8, color=SOFT, ha='center')
    ptitle(c, 'Share of total')
    save(fig, f'{OUT}/figS6_fab')

# ---------------- S8 | withdrawal basis ----------------
def figS8_withdrawal():
    fig, a = plt.subplots(figsize=(HALFW*1.35, 70*MM)); panel(a, 'a', dx=-0.11); ygrid(a)
    for scn, col, lab in [('slow', S_SLOW, 'slow'), ('ref', S_REF, 'reference'), ('accel', S_ACC, 'accelerated')]:
        Iw = M.grid_intensity(scn, 1.0, basis='withdrawal')
        a.plot(Y[1:], Iw[1:], color=col, lw=1.4, label=lab)
        a.annotate(f'{Iw[-1]:.0f}', (2050, Iw[-1]), xytext=(3, 0), textcoords='offset points',
                   fontsize=6.0, color=col, va='center')
    Iw = M.grid_intensity('ref', 1.0, basis='withdrawal')
    a.annotate(f'{Iw[1]:.0f} L kWh$^{{-1}}$ (2024)', (2024, Iw[1]), xytext=(6, 5),
               textcoords='offset points', fontsize=6.0, color=S_REF)
    a.set_xlim(2024, 2050)
    a.set_ylim(0, float(max(Iw))*1.12)           # headroom so the 2024 callout is not clipped
    a.set_ylabel('Grid water WITHDRAWAL intensity (L kWh$^{-1}$)')
    a.legend(loc='lower left', fontsize=6.0)
    a.text(0.98, 0.95, 'measured 2024 thermoelectric withdrawal:\n\u2248173 billion m\u00b3 (consumption \u22483.55)',
           transform=a.transAxes, fontsize=5.9, color=SOFT, ha='right', va='top')
    save(fig, f'{OUT}/figS8_withdrawal')

# ---------------- S9 | cumulative avoided + boundary shift ----------------
def figS9_boundary():
    fig = plt.figure(figsize=(FULLW, 72*MM))
    gs = fig.add_gridspec(1, 2, wspace=0.26, left=0.065, right=0.985, top=0.90, bottom=0.13)
    runs = [('current_evap', 'ref', '#8C8C8C', (0, (4, 2)), 'no adoption (evaporative) \u00b7 ref grid'),
            ('adaptive_warm', 'ref', COOLC['warm'], '-', 'warm-liquid adoption \u00b7 ref grid (headline)'),
            ('adaptive_warm', 'accel', COOLC['warm'], (0, (1.5, 1.5)), 'warm-liquid \u00b7 accelerated grid'),
            ('ferveret', 'ref', COOLC['imm'], '-', 'immersion whole fleet \u00b7 ref grid')]
    a = fig.add_subplot(gs[0]); panel(a, 'a', dx=-0.09); ygrid(a)
    csum = {}
    for cool, g, col, ls, lab in runs:
        r = M.run_case('mid', cool, g); m = r.year >= 2027
        cs = np.cumsum(r.W_total_ML[m].values)/1e6
        csum[(cool, g)] = cs
        a.plot(r.year[m], cs, color=col, ls=ls, lw=1.6, label=lab)
    yy = np.arange(2027, 2051)
    a.fill_between(yy, csum[('adaptive_warm', 'ref')], csum[('current_evap', 'ref')],
                   color=COOLC['warm'], alpha=0.10, lw=0)
    av = csum[('current_evap', 'ref')][-1]-csum[('adaptive_warm', 'ref')][-1]
    a.annotate(f'avoided by warm-liquid adoption\n\u2248{av:.1f} billion m\u00b3 over 2027\u20132050',
               (2047, (csum[('adaptive_warm', 'ref')][list(M.YEARS).index(2047)-list(M.YEARS).index(2027)]
                       + csum[('current_evap', 'ref')][list(M.YEARS).index(2047)-list(M.YEARS).index(2027)])/2),
               xytext=(2027.6, 30.0), fontsize=5.9, color=COOLC['warm'], ha='left',
               arrowprops=dict(arrowstyle='-', lw=0.6, color=COOLC['warm'],
                               shrinkA=2, shrinkB=2))
    a.set_xlim(2027, 2050); a.set_ylim(0, 36)
    a.set_ylabel('Cumulative $W_{\\mathrm{total}}$ from 2027 (billion m\u00b3)')
    a.legend(loc='lower right', fontsize=5.7)
    ptitle(a, 'Cumulative water use under alternative cooling pathways')
    b = fig.add_subplot(gs[1]); panel(b, 'b', dx=-0.09); ygrid(b)
    for cool, g, col, ls, lab in runs:
        r = M.run_case('mid', cool, g); m = r.year >= 2027
        b.plot(r.year[m], 100*r.theta_site[m], color=col, ls=ls, lw=1.6)
    b.annotate('31% without adoption', (2049.5, 33.0), fontsize=5.9, color='#6E6E6E', ha='right')
    b.annotate('\u22485% warm-liquid', (2049.5, 7.2), fontsize=5.9, color=COOLC['warm'], ha='right')
    b.annotate('0% immersion (zero site water)', (2049.5, 1.6), fontsize=5.9, color=COOLC['imm'], ha='right')
    b.set_xlim(2027, 2050); b.set_ylim(0, 34)
    b.set_ylabel('On-site cooling share of total (%)')
    ptitle(b, 'On-site share of modeled water use')
    save(fig, f'{OUT}/figS9_boundary')


# ---------------- S4 | state accounting bases ----------------
def figS4_state_basis():
    """Production vs consumption basis, and the effect of splitting gas steam out."""
    fig, (a, b) = plt.subplots(1, 2, figsize=(FULLW, 72*MM))
    fig.subplots_adjust(left=0.075, right=0.985, top=0.90, bottom=0.20, wspace=0.28)
    sts = sorted(M.DC_WEIGHTS, key=lambda s: -M.DC_WEIGHTS[s])
    xs = np.arange(len(sts))
    panel(a, 'a', dx=-0.13); ygrid(a)
    prod = [M.state_intensity(s, 1.0, 'production') for s in sts]
    cons = [M.state_intensity(s, 1.0, 'consumption') for s in sts]
    a.bar(xs-0.19, prod, 0.36, color=C_GRID, edgecolor='white', lw=0.3, label='production basis')
    a.bar(xs+0.19, cons, 0.36, color=C_FAB, edgecolor='white', lw=0.3, label='consumption basis')
    for x, s_, p_, c_ in zip(xs, sts, prod, cons):          # flag the states that actually move
        if abs(c_/p_ - 1) > 0.03:
            a.annotate(f'{100*(c_/p_-1):+.0f}%', (x, max(p_, c_)), xytext=(0, 3),
                       textcoords='offset points', ha='center', fontsize=5.4, color=INK)
    a.set_xticks(xs); a.set_xticklabels(sts, fontsize=5.8)
    a.set_yscale('log'); a.set_ylim(0.1, 9)
    a.set_yticks([0.5, 1, 2, 4, 8]); a.set_yticklabels(['0.5', '1', '2', '4', '8'])
    a.yaxis.set_minor_formatter(plt.NullFormatter())
    a.set_ylabel('Grid water intensity (L kWh$^{-1}$)')
    a.legend(loc='upper right', fontsize=5.8)
    ptitle(a, 'Production- and consumption-basis grid water intensity')

    panel(b, 'b', dx=-0.13); ygrid(b)
    share = [100*M.GAS_STEAM_SHARE.get(s, 0) for s in sts]
    b.bar(xs, share, 0.62, color=COOLC['evap'], edgecolor='white', lw=0.3)
    b.set_xticks(xs); b.set_xticklabels(sts, fontsize=5.8)
    b.set_ylabel('Gas steam share of state gas generation (%)')
    b.set_ylim(0, 27)
    b.annotate('gas steam consumes 2.78 L kWh$^{-1}$\nagainst 0.66 for combined cycle',
               (0.03, 0.94), xycoords='axes fraction', ha='left', va='top',
               fontsize=5.8, color=SOFT)
    ptitle(b, 'Gas-steam share of gas generation')
    save(fig, f'{OUT}/figS4_state_basis')


# ---------------- S7 | fabrication chain with electricity ----------------
def figS7_fab_chain():
    i50 = list(M.YEARS).index(2050)
    """Fabrication chain with the electricity-generation component."""
    fig, (a, b) = plt.subplots(1, 2, figsize=(FULLW, 72*MM))
    fig.subplots_adjust(left=0.085, right=0.985, top=0.90, bottom=0.17, wspace=0.30)
    fb = M.fab_water('mid'); r = M.run_case('mid', 'adaptive_warm', 'ref')
    panel(a, 'a', dx=-0.13); ygrid(a)
    a.plot(M.YEARS, fb['N_gpu']/1e6, color=C_FAB, lw=1.6)
    a.plot([2024, 2030], [7.0, 19.0], 'D', ms=3.8, color=INK, zorder=5)
    a.annotate('LBNL 2025 Update anchors\n7.0 M (2024), 19 M (2030)', (2030, 19.0),
               xytext=(8, -2), textcoords='offset points', fontsize=5.7,
               ha='left', va='top', color=INK)
    a.set_xlim(2023, 2050); a.set_ylabel('Accelerator shipments (million yr$^{-1}$)')
    ptitle(a, 'Shipments anchored to reported units')

    panel(b, 'b', dx=-0.13); ygrid(b)
    m = M.YEARS >= 2027
    d = fb['W_fab_direct'][m]/1e9; e = fb['W_fab_elec'][m]/1e9
    b.fill_between(M.YEARS[m], 0, d, color=C_FAB, alpha=0.90, lw=0, label='direct process water')
    b.fill_between(M.YEARS[m], d, d+e, color=C_GRID, alpha=0.90, lw=0,
                   label='electricity generation water')
    b.plot(M.YEARS[m], d, color='white', lw=0.6, zorder=4)
    b.set_xlim(2027, 2050); b.set_ylabel('Fabrication water (GL yr$^{-1}$)')
    b.legend(loc='upper left', fontsize=5.8)
    b.annotate(f'{r.theta_fab.iloc[i50]*100:.2f}% of the 2050 total',
               (0.97, 0.06), xycoords='axes fraction', ha='right', fontsize=5.8, color=SOFT)
    ptitle(b, 'Electricity water brought inside the boundary')
    save(fig, f'{OUT}/figS7_fab_chain')

if __name__ == '__main__':
    print('Building SI figures ->', OUT)
    figS1(); figS2(); figS3(); figS5_cooling_adoption(); figS6_fab(); figS8_withdrawal(); figS9_boundary()
    figS4_state_basis(); figS7_fab_chain()
    print('done.')