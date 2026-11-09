#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Main-text figures (Figs 1-4).
Each figure is exported as a standalone PNG and PDF.  Every number is computed live from
lifecycle_water_model.py (which loads derived/model_parameters.json, extracted from the raw
files by 01_extract_parameters.py), so figures, tables and text share one source.
Output: figures/  (override with FIGOUT; raw data are read from data/, override with DATADIR)
Run (from the repository root):  python code/make_figures_publication.py
"""
import os
import struct
import sys
import warnings
import zipfile
from collections import defaultdict

import matplotlib.cm as cm
import matplotlib.colors as mcolors
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from matplotlib.ticker import FixedFormatter, FixedLocator, NullLocator, NullFormatter

warnings.filterwarnings('ignore')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pubstyle import *
import lifecycle_water_model as M

configure_stacked_style()

FIG1_FONT_SCALE = 1.2
FIG1_PANEL_DX = -0.062


def configure_figure1_style():
    """Increase Figure 1 typography while leaving Figures 2--4 unchanged."""
    configure_stacked_style()
    for key in (
        'font.size', 'axes.titlesize', 'axes.labelsize',
        'xtick.labelsize', 'ytick.labelsize', 'legend.fontsize',
    ):
        plt.rcParams[key] = float(plt.rcParams[key]) * FIG1_FONT_SCALE

# Project root = the directory that holds code/, data/ and derived/ (override with PROJECT_ROOT).
ROOT = os.environ.get('PROJECT_ROOT', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.environ.get('FIGOUT', os.path.join(ROOT, 'figures'))
DATA = os.environ.get('DATADIR', os.path.join(ROOT, 'data'))
os.makedirs(OUT, exist_ok=True)
Y = M.YEARS
W0 = list(Y).index(2027)                      # reporting-window start index
MACK = 17.0/M.WF['hydro']                     # exact Macknick-17 multiplier

MAP_XLIM = (-2.56, 2.44)   # tightened: data spans -2.24..2.13, margin for state labels
MAP_YLIM = (-1.80, 1.42)   # data spans -1.70..1.32

base   = M.run_case('mid', 'adaptive_warm', 'ref')
b_lo   = M.run_case('mid', 'adaptive_warm', 'ref', hydro_alloc=0.0)
b_hi   = M.run_case('mid', 'adaptive_warm', 'ref', hydro_alloc=MACK)
yv     = base.year.values

def at(df, yr, col): return df[df.year == yr][col].iloc[0]

# =====================================================================
# FIGURE 1 | framework + headline trajectory + composition
# =====================================================================
def figure1():
    global FIG, GS
    configure_figure1_style()
    FIG = plt.figure(figsize=(FULLW, 168*MM))
    GS = FIG.add_gridspec(3, 1, height_ratios=[1.05, 1.0, 1.0], hspace=0.22,
                          left=0.095, right=0.985, top=0.985, bottom=0.05)
    # ---------------- (a) framework schematic ----------------
    a = FIG.add_subplot(GS[0])
    panel(a, 'a', dx=FIG1_PANEL_DX, dy=0.015, fs=9.0*FIG1_FONT_SCALE)
    a.set_xlim(0, 100); a.set_ylim(0, 30)
    a.axis('off')
    # Use one line spacing and one vertical inset for every box.  Box height is
    # derived from its row count so three- and four-line boxes have the same
    # text-to-border distance rather than the same outer height.
    BOX_LINE_STEP = 1.72
    BOX_VPAD = 1.25
    BOX_PATCH_PAD = 0.55
    ARROW_GAP = BOX_PATCH_PAD + 0.05
    def box(x, y, w, txt, fc, ec=INK, fs=6.1*FIG1_FONT_SCALE, lw=0.8, bold_first=True):
        lines = txt.split('\n')
        box_h = (len(lines) - 1)*BOX_LINE_STEP + 2*BOX_VPAD
        a.add_patch(FancyBboxPatch((x, y), w, box_h,
                                   boxstyle=f'round,pad={BOX_PATCH_PAD},rounding_size=1.1',
                                   fc=fc, ec=ec, lw=lw, zorder=2, clip_on=False))
        top_y = y + box_h - BOX_VPAD
        for i, line in enumerate(lines):
            a.text(x + w/2, top_y - i*BOX_LINE_STEP, line,
                   ha='center', va='center', fontsize=fs,
                   fontweight='bold' if (i == 0 and bold_first) else 'normal',
                   color=INK if i == 0 else SOFT, zorder=3)
        return box_h
    def arr(x1, y1, x2, y2, ls='-', c=SOFT, lw=1.0):
        a.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle='-|>',
                    mutation_scale=7, ls=ls, color=c, lw=lw, zorder=1))
    x_a, y_a, w_a = -2, 11.4, 18
    x_modules, w_modules = 24, 21
    x_total, w_total = 52, 25
    x_products, w_products = 83, 15.5
    h_a = box(x_a, y_a, w_a, 'Module A: Demand\n$E_{dc}(t)$, 2023\u20132050\nLBNL\u00b7EPRI anchors\nScenarios: low, mid, high', '#F2F2F2')
    y_b = 20.0
    h_b = box(x_modules, y_b, w_modules, 'Module B: On-site cooling\nstock-turnover model\nWUE and PUE\n(LBNL-calibrated)', T_SITE)
    y_c = 9.3
    h_c = box(x_modules, y_c, w_modules, 'Module C: Generation water\nmeasured EIA-923 factors\n\u00d7 AEO2026 mix\u00f7 (1\u2212loss)', T_GRID)
    y_d = 1.2
    h_d = box(x_modules, y_d, w_modules, 'Module D | Chip fabrication\nshipments \u2192 wafers\nultrapure water (TSMC)', T_FAB)
    h_total = (5 - 1)*BOX_LINE_STEP + 2*BOX_VPAD
    total_cy = 15.2
    box(x_total, total_cy - h_total/2, w_total, '$W_{\\mathrm{total}}$\nwater within the accounting boundary\n(2027\u20132050 window)\non-site cooling + generation\n+ chip fabrication', 'white', lw=1.1, fs=5.9*FIG1_FONT_SCALE)
    box(x_products, y_a, w_products, 'Decision products\nshares \u03b8, backfire $I^{*}$\nattribution lens\nsiting weights', '#F7F7F7', fs=5.9*FIG1_FONT_SCALE)
    module_y = (y_b + h_b/2, y_c + h_c/2, y_d + h_d/2)
    for source_y, ym in zip((17.4, 15.2, 13.0), module_y):
        arr(x_a + w_a + ARROW_GAP, source_y, x_modules - ARROW_GAP, ym)
    for ym in module_y:
        arr(x_modules + w_modules + ARROW_GAP, ym,
            x_total - ARROW_GAP, total_cy)
    arr(x_total + w_total + ARROW_GAP, total_cy,
        x_products - ARROW_GAP, total_cy)
    # PUE coupling: B -> C, dashed
    coupling_top = y_b - BOX_PATCH_PAD
    coupling_bottom = y_c + h_c + BOX_PATCH_PAD
    coupling_x = x_modules + 2.0
    a.add_patch(FancyArrowPatch((coupling_x, coupling_top), (coupling_x, coupling_bottom), arrowstyle='-|>', mutation_scale=6,
                ls=(0, (2.5, 2)), color=COOLC['evap'], lw=1.1,
                connectionstyle='arc3,rad=0.0', zorder=4))
    a.text(coupling_x + 0.7, (coupling_top + coupling_bottom)/2,
           'PUE coupling: dry heat rejection raises PUE \n and shifts water upstream '
           '($I^{*}$; Fig. 3c).',
           fontsize=4.4*FIG1_FONT_SCALE, color=COOLC['evap'], ha='left', va='center',
           linespacing=1.0, fontweight='bold', zorder=5,
           bbox=dict(boxstyle='square,pad=0.05', fc='white', ec='none', alpha=0.88))

    # ---------------- (b) stacked trajectory ----------------
    b = FIG.add_subplot(GS[1])
    panel(b, 'b', dx=FIG1_PANEL_DX, dy=0.015, fs=9.0*FIG1_FONT_SCALE)
    ygrid(b)
    yy, g, s, f = yv[W0:], base.W_grid_ML.values[W0:]/1e6, base.W_site_ML.values[W0:]/1e6, base.W_fab_ML.values[W0:]/1e6
    tot = g + s + f
    lo = (b_lo.W_grid_ML+b_lo.W_site_ML+b_lo.W_fab_ML).values[W0:]/1e6
    hi = (b_hi.W_grid_ML+b_hi.W_site_ML+b_hi.W_fab_ML).values[W0:]/1e6
    range_color = '#D7E0E8'
    lo_color, hi_color = '#91A3B2', '#536F86'
    b.fill_between(yy, lo, hi, color=range_color, alpha=0.72, lw=0, zorder=1)
    th_f_max = float(np.max(f/tot)*100)   # fabrication share of the total
    # The fabrication band is genuinely thin; edge-free layers keep its fill
    # visible without inflating its magnitude.
    component_colors = ['#315F88', '#3FA37B', '#E3A33B']
    stacks = b.stackplot(yy, g, s, f, colors=component_colors, alpha=0.97,
                edgecolor='none', lw=0, zorder=2,
                labels=['Generation, $g$', 'On-site cooling, $s$',
                        f'Chip fabrication, $f$ ({th_f_max:.1f}%)'])
    # A dashed red total preserves the chip-fabrication fill, while the orange
    # lower boundary makes the very thin fabrication band legible.
    b.plot(yy, g + s, color=component_colors[2], lw=0.65, zorder=3)
    central_line, = b.plot(yy, tot, color='#B33A3A', lw=0.8,
                           ls=(0, (3.2, 1.8)), zorder=4,
                           label='Central total, $g+s+f$ (hydro 9.5)')
    hi_line, = b.plot(yy, hi, color=hi_color, lw=0.9, ls=(0, (2.2, 1.6)), zorder=3,
                      label='Upper bound, $hi$ (hydro 17)')
    lo_line, = b.plot(yy, lo, color=lo_color, lw=0.9, ls=(0, (1.2, 1.7)), zorder=3,
                      label='Lower bound, $lo$ (hydro 0)')
    b.set_xlim(2027, 2050); b.set_ylim(0, 2.0)
    b.set_xlabel('Years')
    b.set_ylabel('Water consumption $W_{\\mathrm{total}}$ (billion m\u00b3·yr$^{-1}$)',
                 labelpad=-2)
    for yr in (2027, 2040, 2050):
        v = tot[list(yy).index(yr)]
        x_offset = 2 if yr == 2027 else (-2 if yr == 2050 else 0)
        alignment = 'left' if yr == 2027 else ('right' if yr == 2050 else 'center')
        b.annotate(f'{yr}: {v:.2f}', (yr, v), xytext=(x_offset, 11),
                   textcoords='offset points', ha=alignment, fontsize=6.4*FIG1_FONT_SCALE,
                   fontweight='bold', color=INK)
    # b.annotate('hydro-factor range\n(0 \u2192 17 L kWh$^{-1}$)',
    #            (2048, hi[list(yy).index(2048)]), xytext=(2043.9, 1.87), fontsize=5.6,
    #            color='#5C7186', ha='center',
    #            arrowprops=dict(arrowstyle='-', lw=0.6, color='#7C93A8'))
    cum = tot.sum()
    # b.text(0.03, 0.965, f'mid demand \u00b7 warm-liquid adoption \u00b7 reference grid\ncumulative 2027\u20132050 = {cum:.1f} billion m\u00b3',
    #        transform=b.transAxes, fontsize=6.0, va='top', color=SOFT)
    all_legend_handles = [
        *stacks,
        central_line,
        lo_line,
        hi_line,
        mpatches.Patch(fc=range_color, ec='none', alpha=0.72,
                       label='Hydro sensitivity, $lo$\u2013$hi$'),
    ]
    b.legend(handles=all_legend_handles, loc='lower right', ncol=2, fontsize=4.45*FIG1_FONT_SCALE,
             columnspacing=0.75, labelspacing=0.14, handlelength=1.55,
             handletextpad=0.35, borderaxespad=0.35,
             frameon=True, framealpha=0.86, facecolor='white', edgecolor='none')

    # ---------------- (c) composition ----------------
    c = FIG.add_subplot(GS[2])
    panel(c, 'c', dx=FIG1_PANEL_DX, dy=0.015, fs=9.0*FIG1_FONT_SCALE)
    ygrid(c)
    th_g, th_s, th_f = 100*base.theta_grid.values[W0:], 100*base.theta_site.values[W0:], 100*base.theta_fab.values[W0:]
    c.stackplot(yy, th_g, th_s, th_f, colors=[C_GRID, C_SITE, C_FAB], alpha=0.92,
                edgecolor='none', lw=0)
    # Chip fabrication is only 0.2--0.4% of the total.  Avoid a white polygon
    # edge that would cover the thin band, and reinforce its true upper edge.
    c.plot(yy, th_g + th_s + th_f, color=C_FAB, lw=0.8,
           zorder=3, clip_on=False)
    c.set_xlim(2027, 2050); c.set_ylim(0, 100)
    c.set_xlabel('Years')
    c.set_ylabel('Share of $W_{\\mathrm{total}}$ (%)')
    c.text(2038.5, 45, f'electricity generation, {th_g[0]:.0f}% \u2192 {th_g[-1]:.0f}%', color='white', fontsize=7.0*FIG1_FONT_SCALE,
           fontweight='bold', ha='center')
    c.annotate(f'{th_g[0]:.0f}%', (2027.3, th_g[0]-6), color='white', fontsize=6.4*FIG1_FONT_SCALE, fontweight='bold')
    c.annotate(f'{th_g[-1]:.0f}%', (2049.7, th_g[-1]-6), color='white', fontsize=6.4*FIG1_FONT_SCALE,
               fontweight='bold', ha='right')
    c.annotate(f'on-site cooling  {th_s[0]:.0f}% \u2192 {th_s[-1]:.0f}%', (2037, 96.0), fontsize=6.2*FIG1_FONT_SCALE, color='white',
               fontweight='bold', ha='center')
    c.text(0.99, 1.012, f'chip fabrication  {th_f[0]:.1f}% \u2192 {th_f[-1]:.1f}%',
           transform=c.transAxes, fontsize=6.0*FIG1_FONT_SCALE, color='#E3A33B',
           ha='right', va='bottom', clip_on=False)
    save(FIG, f'{OUT}/fig1_framework_and_trajectory', dpi=1200)
    configure_stacked_style()

# =====================================================================
# FIGURE 2 | measured factors, decarbonisation, siting, hydropower swing
# =====================================================================
def _polygon_records(shp):
    """Read polygon parts from a shapefile without an optional GIS dependency."""
    records, pos, n = [], 100, len(shp)
    while pos < n:
        rec_len = struct.unpack('>i', shp[pos+4:pos+8])[0]*2; s = pos+8
        rings = []
        if struct.unpack('<i', shp[s:s+4])[0] == 5:
            nparts = struct.unpack('<i', shp[s+36:s+40])[0]
            npts = struct.unpack('<i', shp[s+40:s+44])[0]; p0 = s+44
            parts = list(struct.unpack(f'<{nparts}i', shp[p0:p0+4*nparts]))+[npts]
            xy = struct.unpack(f'<{2*npts}d', shp[p0+4*nparts:p0+4*nparts+16*npts])
            pts = list(zip(xy[0::2], xy[1::2]))
            for i in range(nparts): rings.append(pts[parts[i]:parts[i+1]])
        records.append(rings)
        pos = s+rec_len
    return records

def _dbf_records(dbf):
    """Return DBF rows as dictionaries, preserving shapefile record order."""
    nrec = struct.unpack('<I', dbf[4:8])[0]
    header_len = struct.unpack('<H', dbf[8:10])[0]
    record_len = struct.unpack('<H', dbf[10:12])[0]
    fields, pos = [], 32
    while dbf[pos] != 0x0D:
        desc = dbf[pos:pos+32]
        name = desc[:11].split(b'\0', 1)[0].decode('ascii')
        fields.append((name, desc[16]))
        pos += 32
    rows = []
    for i in range(nrec):
        raw = dbf[header_len+i*record_len:header_len+(i+1)*record_len]
        row, start = {}, 1
        for name, width in fields:
            row[name] = raw[start:start+width].decode('latin1').strip()
            start += width
        rows.append(row)
    return rows

def load_state_shapes():
    """Contiguous-US state polygons keyed by two-letter postal abbreviation."""
    path = f'{DATA}/cb_2024_us_state_20m.zip'
    with zipfile.ZipFile(path) as z:
        shp = z.read('cb_2024_us_state_20m.shp')
        dbf = z.read('cb_2024_us_state_20m.dbf')
    shapes = _polygon_records(shp)
    rows = _dbf_records(dbf)
    return {row['STUSPS']: rings for row, rings in zip(rows, shapes)}

def albers(lon, lat):
    lon, lat = np.asarray(lon), np.asarray(lat)
    a_ = 6378137.0; f_ = 1/298.257222101; e2 = 2*f_-f_*f_; e = np.sqrt(e2)
    lat0, lon0, lat1, lat2 = 40.0, -96.0, 20.0, 60.0
    def q(phi):
        s = np.sin(phi); return (1-e2)*(s/(1-e2*s*s)-(1/(2*e))*np.log((1-e*s)/(1+e*s)))
    def mm_(phi):
        s = np.sin(phi); return np.cos(phi)/np.sqrt(1-e2*s*s)
    p0, p1, p2 = np.radians(lat0), np.radians(lat1), np.radians(lat2)
    n = (mm_(p1)**2-mm_(p2)**2)/(q(p2)-q(p1)); C = mm_(p1)**2+n*q(p1)
    rho0 = a_*np.sqrt(C-n*q(p0))/n
    ph = np.radians(lat); th = n*np.radians(lon-lon0); rho = a_*np.sqrt(C-n*q(ph))/n
    return rho*np.sin(th), rho0-rho*np.cos(th)

def eia_state_top(k=12):
    import openpyxl
    wb = openpyxl.load_workbook(f'{DATA}/Cooling_Boiler_Generator_Data_Detail_2024.xlsx', read_only=True)
    ws = wb['Detail']; seen = {}
    def num(x):
        try: return float(x)
        except Exception: return 0.0
    for r in ws.iter_rows(min_row=4, values_only=True):
        state, plant, cool, month = r[1], r[2], r[8], r[5]
        if not state or cool is None: continue
        key = (plant, cool, month)
        if key not in seen: seen[key] = (state, num(r[30]))
    st = defaultdict(float)
    for state, v in seen.values(): st[state] += v
    return set(s for s, _ in sorted(st.items(), key=lambda x: -x[1])[:k])

def figure2():
    global FIG, GS
    # The map is drawn with set_aspect(1.0) over a 5.6 x 3.2 unit extent, so at full
    # column width it needs a height of 0.568 x width.  The panel-c row is sized to that
    # ratio (plus a legend strip) so the map fills the page width instead of being
    # letterboxed; the other panels keep a readable height.
    # The map is drawn at a locked aspect, so at full column width it needs a height of
    # 0.644 x width.  Stacking all five panels at full width would make the figure ~370 mm
    # tall; because a submitted figure is scaled to the page height, that would leave the
    # printed map SMALLER than a compact layout.  The four chart panels are therefore
    # paired two-up and the map keeps the full width.
    _pw = FULLW*(0.965-0.085)
    _map_h = _pw*0.644*1.10                        # map plus a thin legend strip
    _pair_h = 50*MM
    _hr = [_pair_h, _map_h, _pair_h]
    _total = sum(_hr)/(0.975-0.045) + 2*0.20*_pair_h
    FIG = plt.figure(figsize=(FULLW, _total))
    GS_OUTER = FIG.add_gridspec(3, 1, height_ratios=_hr, hspace=0.20,
                                left=0.095, right=0.99, top=0.985, bottom=0.05)
    _top = GS_OUTER[0].subgridspec(1, 2, wspace=0.26)
    _bot = GS_OUTER[2].subgridspec(1, 2, wspace=0.26)
    GS = [_top[0], _top[1], GS_OUTER[1], _bot[0], _bot[1]]
    # ---------------- (a) measured water factors ----------------
    a = FIG.add_subplot(GS[0])
    panel(a, 'a', dx=-0.062, dy=0.015, fs=9.0)
    rows = [('Hydropower', M.WF['hydro'], 'lit', (5.4, 68.0, 17.0)),
            ('Geothermal', M.WF['geo'], 'lit', None),
            ('Biomass', M.WF['bio'], 'meas', None),
            ('Gas steam', M.WF['gas_other'], 'meas', None),
            ('Coal steam', M.WF['coal'], 'meas', None),
            ('Nuclear', M.WF['nuclear'], 'meas', None),
            ('Gas combined cycle', M.WF['gas_cc'], 'meas', None),
            ('Solar PV', M.WF['solar'], 'lit', None),
            ('Wind', 0.001, 'lit', None)]
    ypos = np.arange(len(rows))[::-1]
    a.set_xscale('log'); a.set_xlim(8e-4, 100)
    a.grid(axis='x', color=LINEC, lw=0.5, alpha=0.55); a.set_axisbelow(True)
    for (nm, v, kind, rng), yp in zip(rows, ypos):
        col = C_GRID if kind == 'meas' else '#8C8C8C'
        marker = 'o' if kind == 'meas' else '^'
        if rng:
            a.plot([rng[0], rng[1]], [yp, yp], color='#B9C6D2', lw=3.2, solid_capstyle='round', zorder=1)
            a.plot([rng[2]], [yp], marker='|', ms=7, mew=1.4, color='#5C7186', zorder=3)
            a.annotate('Published range 5.4\u201368', (rng[1], yp), xytext=(-2, 6),
                       textcoords='offset points', fontsize=5.4, color='#5C7186', ha='right')
            a.annotate('Macknick median 17', (17, yp), xytext=(4, -11),
                       textcoords='offset points', fontsize=5.4, color='#5C7186', ha='left')
            col = '#2A6F97'
            marker = 's'
        a.plot([v], [yp], marker=marker, ls='', ms=4.6, color=col,
               mec='white', mew=0.5, zorder=4)
        if not rng:
            is_wind = nm == 'Wind'
            a.annotate(f'{v:.2f}' if v >= 0.01 else '\u22480', (v, yp),
                       xytext=(2, 0) if is_wind else (0, 5.5),
                       textcoords='offset points',
                       ha='left' if is_wind else 'center',
                       va='center' if is_wind else 'baseline',
                       fontsize=5.8, color=INK)
    a.set_yticks(ypos)
    a.set_yticklabels([r[0] for r in rows], fontsize=6.2)
    a.set_ylim(-0.6, 8.85)
    a.set_xlabel('Consumptive water factor (L·kWh$^{-1}$, log scale)')
    h1 = plt.Line2D([], [], marker='o', ls='', color=C_GRID, ms=4.4, label='Measured, EIA-923 2024')
    h2 = plt.Line2D([], [], marker='^', ls='', color='#8C8C8C', ms=4.4, label='Literature factor')
    h3 = plt.Line2D([], [], marker='s', ls='', color='#2A6F97', ms=4.4, label='Grubert & Sanders central')
    a.legend(
        handles=[h1, h2, h3],
        loc='lower right',
        fontsize=5.5,
        handletextpad=0.25,
        labelspacing=0.3,
    )

    # ---------------- (b) grid intensity trajectories ----------------
    b = FIG.add_subplot(GS[1])
    panel(b, 'b', dx=-0.062, dy=0.015, fs=9.0)
    ygrid(b)
    for scn, col, lab in [('slow', S_SLOW, 'Slow grid'), ('ref', S_REF, 'Reference (AEO2026)'),
                          ('accel', S_ACC, 'Accelerated grid')]:
        I = M.grid_intensity(scn, 1.0); In = M.grid_intensity(scn, 0.0)
        b.plot(Y[1:], I[1:], color=col, lw=1.5, label=lab)
        b.plot(Y[1:], In[1:], color=col, lw=0.9, ls='--',
               label=f'{lab} (hydropower excluded)')
    Iref = M.grid_intensity('ref', 1.0)
    # b.annotate(f'{Iref[1]:.2f}', (2024, Iref[1]), xytext=(-2, 6), textcoords='offset points',
    #            fontsize=6.2, fontweight='bold', color=S_REF)
    # b.annotate(f'{Iref[-1]:.2f}', (2050, Iref[-1]), xytext=(2, 4), textcoords='offset points',
    #            fontsize=6.2, fontweight='bold', color=S_REF, ha='right')
    b.set_xlim(2024, 2050); b.set_ylim(0, 1.9)
    b.set_xlabel('Years')
    b.set_ylabel('Grid water intensity (L·kWh$^{-1}$)')
    b.legend(loc='lower left', fontsize=5.15, labelspacing=0.22)

    # ---------------- (c) siting map ----------------
    # Keep the map and its key in separate axes. This prevents the bubble key
    # from covering Texas and gives the projected map a true 1:1 data aspect.
    map_gs = GS[2].subgridspec(2, 2, height_ratios=[1.0, 0.10],
                               width_ratios=[1.0, 0.030], hspace=0.01, wspace=0.012)
    c = FIG.add_subplot(map_gs[0, 0])
    panel(c, 'c', dx=-0.062, dy=0.015, fs=9.0)
    cbar_slot = FIG.add_subplot(map_gs[0, 1])
    key = FIG.add_subplot(map_gs[1, :])
    c.axis('off')
    cbar_slot.axis('off')
    key.axis('off')
    state_shapes = load_state_shapes(); topw = eia_state_top(12)
    cent = {'VA': (-78.6, 37.6), 'TX': (-99.3, 31.3), 'CA': (-119.6, 37.0), 'IL': (-89.2, 40.1),
            'OR': (-120.6, 43.9), 'AZ': (-111.7, 34.2), 'IA': (-93.5, 42.0), 'GA': (-83.4, 32.7),
            'WA': (-120.5, 47.4), 'PA': (-77.6, 41.0), 'NY': (-75.3, 42.9), 'NJ': (-74.5, 40.1),
            'NE': (-99.8, 41.5), 'ND': (-100.3, 47.5), 'NV': (-116.9, 39.3)}
    tw_cent = {'FL': (-81.7, 28.0), 'IN': (-86.3, 40.0), 'MI': (-84.7, 43.6), 'AL': (-86.8, 32.8),
               'OH': (-82.8, 40.3), 'LA': (-92.3, 31.1), 'OK': (-97.5, 35.5)}
    label_offsets = {
        'VA': (18, -10), 'PA': (8, 13), 'NY': (10, 20), 'NJ': (22, 0),
        'IL': (-21, 8), 'IA': (-11, 16), 'NE': (-18, 0), 'ND': (0, 14),
        'GA': (15, -12), 'AZ': (-17, -11), 'NV': (-16, 8), 'CA': (-18, 1),
        'OR': (-16, 9), 'WA': (-15, 12), 'TX': (0, -18),
        'MI': (0, 13), 'OH': (18, 3), 'IN': (4, -12), 'AL': (-9, -11),
        'FL': (12, -11), 'LA': (-13, -8), 'OK': (0, -12),
    }
    norm = mcolors.LogNorm(vmin=0.20, vmax=7.5)     # measured state range 0.25-6.96
    sm = cm.ScalarMappable(norm=norm, cmap='GnBu'); sm.set_array([])
    def put(lon, lat):
        x, y = albers(lon, lat); return x/1e6, y/1e6

    # Neutral state polygons keep geography readable without competing with
    # the multivariate state glyphs placed at the state centroids.
    for s, rings in state_shapes.items():
        for ring in rings:
            lon, lat = zip(*ring); x, y = albers(lon, lat)
            c.fill(np.asarray(x)/1e6, np.asarray(y)/1e6, facecolor='#F4F6F8',
                   edgecolor='#C3CDD4', linewidth=0.35, zorder=0)

    # Hexagon area encodes DC load share; fill colour encodes grid-water
    # intensity.  A small red star independently marks the thermoelectric set.
    dc_states = set(M.DC_WEIGHTS)
    glyph_scale = 2350
    for s, share in M.DC_WEIGHTS.items():
        x, y = put(*cent[s])
        Iv = M.state_intensity(s)                   # 2024 consumption (load-serving) basis
        c.scatter(x, y, s=share*glyph_scale, marker='h', color=sm.to_rgba(Iv),
                  edgecolors=INK, linewidths=0.65, alpha=0.96, zorder=3)
    for s in topw:
        cc = cent.get(s) or tw_cent.get(s)
        if cc is None:
            continue
        x, y = put(*cc)
        c.scatter(x, y, s=25, marker='o', color='#C75146', edgecolors='white',
                  linewidths=0.35, zorder=4)

    # Label only the states involved in at least one of the three encodings.
    for s in sorted(topw | dc_states):
        cc = cent.get(s) or tw_cent.get(s)
        if cc is None:
            continue
        x, y = put(*cc)
        dx, dy = label_offsets.get(s, (0, 0))
        c.annotate(s, (x, y), xytext=(dx, dy), textcoords='offset points',
                   fontsize=7.2, fontweight='bold', zorder=5,
                   ha='center', va='center',
                   arrowprops=dict(arrowstyle='-', lw=0.45, color='#6F7880', shrinkA=0, shrinkB=2)
                   if (dx, dy) != (0, 0) else None)

    c.set_xlim(*MAP_XLIM)
    c.set_ylim(*MAP_YLIM)
    c.set_aspect(1.0, adjustable='box', anchor='C')

    # Use a dedicated grid cell for the colour bar so it cannot resize the map
    # or collide with panel d.
    cax = cbar_slot.inset_axes([0.10, 0.14, 0.70, 0.72])
    cb = FIG.colorbar(sm, cax=cax)
    cb.set_label('State grid water intensity (L·kWh$^{-1}$)', fontsize=7.4)
    cb.ax.tick_params(labelsize=7.0)
    cb.ax.yaxis.set_major_locator(FixedLocator([0.5, 1, 2, 4, 7]))
    cb.ax.yaxis.set_major_formatter(FixedFormatter(['0.5', '1', '2', '4', '7']))
    cb.ax.yaxis.set_minor_locator(NullLocator())

    # Compact glyph key: shape area, fill colour and the red state marker each
    # have one independent meaning.
    key.set_xlim(0, 1)
    key.set_ylim(0, 1)
    key.scatter(0.045, 0.76, s=25, marker='*', color='#C75146',
                edgecolors='white', linewidths=0.35, clip_on=False)
    key.text(0.10, 0.76, 'Top-12 thermoelectric-water state (EIA-923)',
             fontsize=6.8, va='center')
    for x0, share, lab in [(0.045, 0.05, 'DC load share 5%'),
                           (0.58, 0.235, 'DC load share 23.5% (VA)')]:
        key.scatter(x0, 0.25, s=share*glyph_scale, marker='h',
                    facecolor='#D5DDE3', edgecolor=INK, lw=0.6, clip_on=False)
        key.text(x0 + 0.085, 0.25, lab, fontsize=6.8, va='center')

    # ---------------- (d) national vs DC-weighted, three hydro treatments ----------------
    d = FIG.add_subplot(GS[3])
    panel(d, 'd', dx=-0.062, dy=0.015, fs=9.0)
    ygrid(d)
    treatments = [('excluded', 0.0, '#B9C6D2'), ('Grubert 9.5', 1.0, '#2A6F97'),
                  ('Macknick 17', MACK, '#123E5C')]
    xn, xd = np.arange(3)*0.9, np.arange(3)*0.9 + 3.4
    for i, (lab, ha, col) in enumerate(treatments):
        vn = M.grid_intensity('ref', ha)[1]
        vd = M.grid_intensity_dcweighted('ref', ha, 2024)
        d.bar(xn[i], vn, 0.72, color=col, edgecolor='white', lw=0.5)
        d.bar(xd[i], vd, 0.72, color=col, edgecolor='white', lw=0.5,
              label=f'Hydropower {lab}')
        for x, v in ((xn[i], vn), (xd[i], vd)):
            d.annotate(f'{v:.2f}', (x, v), xytext=(0, 3), textcoords='offset points',
                       ha='center', fontsize=6.2, fontweight='bold')
    dcw, dc0 = M.grid_intensity_dcweighted('ref', 1.0, 2024), M.grid_intensity_dcweighted('ref', 0.0, 2024)
    hshare = (dcw-dc0)/dcw*100
    arrow_x = (xd[0] + xd[1])/2
    d.annotate('', xy=(arrow_x, dcw), xytext=(arrow_x, dc0),
               arrowprops=dict(arrowstyle='<->', lw=0.8, color='#C75146'))
    d.text(arrow_x + 0.12, (dcw+dc0)/2,
           f'Hydropower\n{hshare:.0f}% of the\nweighted term',
           fontsize=5.6, color='#C75146', va='center', ha='left',
           bbox=dict(boxstyle='square,pad=0.08', fc='white', ec='none', alpha=0.84))
    d.set_xticks([xn.mean(), xd.mean()])
    d.set_xticklabels(
        ['National average', 'Data-center-weighted\n(EPRI 15-state loads)'],
        fontsize=6.0,
    )
    d.set_ylim(0, 2.75)
    d.set_xlim(-0.7, xd[-1] + 2.35)
    d.set_ylabel('Grid water intensity, 2024 (L·kWh$^{-1}$)')
    d.legend(loc='upper left', fontsize=5.9)
    # --- panel e | volumetric intensity against Aqueduct water stress -------------
    e = FIG.add_subplot(GS[4])
    ygrid(e)
    """Volumetric intensity vs water stress across the fifteen data-centre states."""
    fig, a = plt.subplots(figsize=(HALFW*1.5, 74*MM))
    panel(e, 'e', dx=-0.205, dy=0.030, fs=9.0); ygrid(e)
    sts = sorted(M.DC_WEIGHTS, key=lambda s: -M.DC_WEIGHTS[s])
    required_scarcity_fields = ('bws_2023', 'ws_bau2050')
    missing_scarcity = [
        s for s in sts
        if s not in M.SCARCITY
        or any(M.SCARCITY[s].get(field) is None for field in required_scarcity_fields)
    ]
    if missing_scarcity:
        raise ValueError(
            'Missing Aqueduct scarcity data for DC states: '
            + ', '.join(missing_scarcity)
        )
    xs = [M.state_intensity(s) for s in sts]            # consumption basis, matches panel c
    ys = [M.SCARCITY[s]['bws_2023'] for s in sts]
    sz = [3000*M.DC_WEIGHTS[s] for s in sts]
    sc = e.scatter(xs, ys, s=sz, c=[M.SCARCITY[s]['ws_bau2050'] - M.SCARCITY[s]['bws_2023'] for s in sts],
                   cmap='RdYlBu_r', vmin=-0.2, vmax=0.5, edgecolor=INK, lw=0.4, zorder=3, alpha=0.92)
    # NJ sits inside the much larger VA bubble and NE abuts NV, so both are given a
    # short leader line instead of an in-bubble label.
    LEADER = {'NJ': (16, -14), 'NE': (-26, 10), 'NV': (0, -20), 'ND': (20, -12)}
    for s, x, y in zip(sts, xs, ys):
        if s in LEADER:
            e.annotate(s, (x, y), xytext=LEADER[s], textcoords='offset points',
                       fontsize=5.6, ha='center', va='center', color=INK, zorder=6,
                       arrowprops=dict(arrowstyle='-', lw=0.5, color=INK,
                                       shrinkA=1.0, shrinkB=1.5))
        else:
            e.annotate(s, (x, y), xytext=(0, -1), textcoords='offset points',
                       fontsize=5.6, ha='center', va='center', color=INK, zorder=5)
    e.axvline(M.grid_intensity_dcweighted('ref', 1.0, 2024), color=SOFT, lw=0.7, ls=(0, (3, 2)), zorder=1)
    e.axhline(M.scarcity_weight(2023), color=SOFT, lw=0.7, ls=(0, (3, 2)), zorder=1)
    e.annotate('load-weighted intensity', (M.grid_intensity_dcweighted('ref', 1.0, 2024), 4.7),
               xytext=(4, 0), textcoords='offset points', fontsize=5.6, color=SOFT, va='top')
    e.annotate('load-weighted stress', (7.0, M.scarcity_weight(2023)), xytext=(0, 3),
               textcoords='offset points', fontsize=5.6, color=SOFT, ha='right')
    e.set_xscale('log'); e.set_xlim(0.35, 8)
    e.set_xticks([0.5, 1, 2, 4, 8]); e.set_xticklabels(['0.5', '1', '2', '4', '8'])
    e.xaxis.set_minor_formatter(NullFormatter())
    e.set_ylim(0, 5)
    e.set_xlabel('State grid water intensity, 2024 (L kWh$^{-1}$)')
    e.set_ylabel('Aqueduct baseline water stress (0\u20135)')
    cb = FIG.colorbar(sc, ax=e, pad=0.02, fraction=0.045)
    cb.set_label('Change in stress to 2050 (BAU)', fontsize=6.4)
    cb.ax.tick_params(labelsize=6.0)
    ptitle(a, 'Volumetric intensity and water stress rank states differently')

    save(FIG, f'{OUT}/fig2_generation_and_geography')

# =====================================================================
# FIGURE 3 | cooling adoption, tradeoff plane, backfire, 2050 outcomes
# =====================================================================
def figure3():
    global FIG, GS
    FIG = plt.figure(figsize=(FULLW, 196*MM))
    GS = FIG.add_gridspec(4, 1, height_ratios=[1.0, 1.0, 1.0, 1.0], hspace=0.26,
                          left=0.095, right=0.985, top=0.985, bottom=0.05)
    _I_nat = M.grid_intensity('ref', 1.0)[list(M.YEARS).index(2024)]
    _I_dc  = M.grid_intensity_dcweighted('ref', 1.0, 2024)
    _dpue_warm = M.climate_weighted_aidry('mid')[1] - M.COOL_C['aievap'][1]
    I_dc24 = M.grid_intensity_dcweighted('ref', 1.0, 2024)
    # ---------------- (a) WUE-PUE plane with iso-water contours ----------------
    a = FIG.add_subplot(GS[0])
    panel(a, 'a', dx=-0.062, dy=0.015, fs=9.0)
    wgrid = np.linspace(0, 0.70, 120); pgrid = np.linspace(1.02, 1.32, 120)
    Wm, Pm = np.meshgrid(wgrid, pgrid)
    S = Wm + Pm*I_dc24
    levels = [2.05, 2.2, 2.35, 2.5, 2.65]
    cs = a.contour(Wm, Pm, S, levels=levels, colors='#C4CED6', linewidths=0.65,
                   linestyles='--', zorder=0)
    man = []
    for L in levels:
        x_at_bottom = L - 1.035*I_dc24
        if 0.02 < x_at_bottom < 0.66: man.append((x_at_bottom, 1.035))
        else: man.append((0.685, (L-0.685)/I_dc24))
    a.clabel(cs, fmt='%.2f', fontsize=5.2, colors='#98A6B1', manual=man)
    pts = [
        # label, WUE, PUE, colour, label offset (points), alignment
        ('Evaporative /\ntower-assisted', M.COOL_C['aievap'][0], M.COOL_C['aievap'][1],
         COOLC['evap'], (-4, 13), 'right'),
        # 'Hybrid fleet' removed: it was a fleet aggregate on a technology plane and is
        # inconsistent with the LBNL-calibrated fleet PUE (1.45 in 2024).
        ('Closed-loop,\nevap reject', 0.15, 1.13, COOLC['dlc'], (4, 5), 'left'),
        ('Legacy dry chiller\n(PUE penalty)', 0.02, 1.26, COOLC['dry'], (4, 11), 'left'),
        ('Warm-liquid 45\u00b0C\n(ASHRAE W45)', *M.climate_weighted_aidry('mid'),
         COOLC['warm'], (4, -5), 'left'),
        ('Two-phase immersion\n(Ferveret)', 0.00, 1.05, COOLC['imm'], (4, -4), 'left'),
    ]
    a.plot([M.COOL_C['aievap'][0], M.COOL_C['drychiller'][0]],
           [M.COOL_C['aievap'][1], M.COOL_C['drychiller'][1]],
           ls='-', color='#919191', lw=1.15, zorder=1)
    for nm, w, p, col, label_offset, align in pts:
        a.plot([w], [p], 'o', ms=6.2, color=col, mec='white', mew=0.7, zorder=4)
        a.annotate(nm, (w, p), xytext=label_offset, textcoords='offset points',
                   fontsize=5.5, color=col, fontweight='bold', va='center', ha=align,
                   zorder=5)
    # A visually near-45-degree conceptual vector points from the closed-loop
    # region toward warm-liquid operation: WUE and PUE both decline.
    direction_arrow = FancyArrowPatch(
        (0.135, 1.127), (0.055, 1.082), arrowstyle='-|>', mutation_scale=8,
        lw=1.45, color='#1D6B4E', shrinkA=5, shrinkB=5, zorder=3,
    )
    a.add_patch(direction_arrow)
    a.set_xlim(-0.03, 0.72); a.set_ylim(1.02, 1.32)
    a.set_xlabel('Site water use, WUE (L·kWh$^{-1}$ IT)')
    a.set_ylabel('Facility energy overhead, PUE')
    contour_h = plt.Line2D([], [], color='#AEBAC3', lw=0.9, ls=(0, (3.0, 2.0)),
                           label=f'Iso-water contours: site + generation ($I$ = {I_dc24:.2f})')
    tradeoff_h = plt.Line2D([], [], color='#919191', lw=1.15, ls='-',
                            label='Wet\u2192dry trade-off: lower WUE, higher PUE')
    temp_h = plt.Line2D([], [], color='#1D6B4E', lw=1.25, marker='<', ms=4,
                        label='Higher coolant temperature: lower WUE and PUE')
    a.legend(handles=[contour_h, tradeoff_h, temp_h], loc='upper right',
             fontsize=4.75, labelspacing=0.25, handlelength=1.8,
             frameon=True, framealpha=0.88, facecolor='white', edgecolor='none')

    # ---------------- (b) fleet WUE under stock turnover ----------------
    b = FIG.add_subplot(GS[1])
    panel(b, 'b', dx=-0.062, dy=0.015, fs=9.0)
    ygrid(b)
    b.axvspan(2023, 2027, color='#F2F2F2', zorder=0)
    b.text(2025, 0.575, 'Calibration\nwindow', fontsize=5.6, color=SOFT, ha='center')
    paths = [('slow', '#9DB9CE', 'Slow turnover (L=6 yr)', (0, (1.2, 1.5))),
             ('base', C_GRID, 'Base (L=5 yr, headline)', '-'),
             ('fast', '#123E5C', 'Fast (L=4 yr)', (0, (5.0, 2.0)))]
    for ds, col, lab, line_style in paths:
        w, p = M.cooling_series('adaptive_warm', ds)
        b.plot(Y, w, color=col, ls=line_style,
               lw=1.6 if ds == 'base' else 1.2, label=lab)
    w_b, _ = M.cooling_series('adaptive_warm', 'base')
    pk = int(np.argmax(w_b))
    b.plot([Y[pk]], [w_b[pk]], marker='o', ms=3.2, color=C_GRID, zorder=5)
    b.annotate(f'Peak {w_b[pk]:.2f} ({Y[pk]})', (Y[pk], w_b[pk]), xytext=(0, 8),
               textcoords='offset points', ha='center', fontsize=5.7, color=SOFT)
    # The diamond is LBNL's 2023 calibration anchor; the modelled curve starts slightly
    # above it because the AI share was re-anchored to the 2025 Update.  Marking the anchor
    # on the curve would misrepresent it, so it is drawn at its own value with a connector.
    b.plot([2023], [0.36], marker='D', ms=4, color=INK, zorder=5)
    b.annotate('LBNL fleet\n0.36 (2023)', (2023, 0.36), xytext=(10, -22),
               textcoords='offset points', fontsize=5.5, color=INK, va='top',
               arrowprops=dict(arrowstyle='-', lw=0.4, color=SOFT))
    # LBNL reports a vertical 0.45--0.48 interval for 2028 under unchanged
    # cooling technology. Use a capped interval without a central marker so it
    # reads as a range rather than as an additional measured data point.
    b.errorbar([2028], [0.465], yerr=[[0.015], [0.015]], fmt='none', ecolor=INK,
               elinewidth=1.05, capsize=3.0, capthick=1.05, zorder=5)
    b.annotate('LBNL projection assuming no\nimprovement in current cooling\n0.45\u20130.48 (2028)',
               (2028, 0.465), xytext=(8, 8),
               textcoords='offset points', fontsize=5.35, color=INK, va='bottom',
               arrowprops=dict(arrowstyle='-', lw=0.4, color=SOFT))
    end_values = [M.cooling_series('adaptive_warm', ds)[0][-1]
                  for ds in ('slow', 'base', 'fast')]
    end_lo, end_hi = min(end_values), max(end_values)
    bracket_x, bracket_cap = 2050.35, 0.28
    b.plot([bracket_x, bracket_x], [end_lo, end_hi], color=SOFT, lw=0.8,
           clip_on=False, zorder=6)
    b.plot([bracket_x-bracket_cap, bracket_x], [end_lo, end_lo], color=SOFT,
           lw=0.8, clip_on=False, zorder=6)
    b.plot([bracket_x-bracket_cap, bracket_x], [end_hi, end_hi], color=SOFT,
           lw=0.8, clip_on=False, zorder=6)
    b.text(bracket_x + 0.18, (end_lo + end_hi)/2,
           f'2050: {end_lo:.2f}\u2013{end_hi:.2f}', fontsize=5.8,
           color=SOFT, ha='left', va='center')
    b.set_xlim(2022.6, 2053.0)
    b.set_ylim(0, 0.62)
    b.set_xlabel('Years')
    b.set_ylabel('Fleet site WUE (L·kWh$^{-1}$ IT)')
    b.legend(loc='upper right', fontsize=5.9)

    # ---------------- (c) backfire threshold ----------------
    c = FIG.add_subplot(GS[2])
    panel(c, 'c', dx=-0.062, dy=0.015, fs=9.0)
    ygrid(c)
    Ig = np.linspace(0, 8, 300)
    wue_w, pue_w = M.COOL_C['aievap']; wue_d, pue_d = M.COOL_C['drychiller']
    wue_n, pue_n = M.COOL_C['aidry']
    net_dry = -(wue_w-wue_d) + (pue_d-pue_w)*Ig
    net_warm = -(wue_w-wue_n) + (pue_n-pue_w)*Ig
    thr = (wue_w-wue_d)/(pue_d-pue_w)
    c.axhline(0, color=INK, lw=0.7)
    c.fill_between(Ig, net_dry, 0, where=net_dry < 0, color=C_SITE, alpha=0.14, lw=0)
    c.fill_between(Ig, net_dry, 0, where=net_dry > 0, color='#C75146', alpha=0.16, lw=0)
    c.plot(Ig, net_dry, color=COOLC['dry'], lw=1.7, ls=(0, (5, 2)),
           label='Legacy dry chiller (\u0394PUE = +0.12)')
    c.plot(Ig, net_warm, color=COOLC['warm'], lw=1.7, ls='-',
           label=f'Warm-liquid 45\u00b0C (\u0394PUE = {_dpue_warm:+.3f})')
    c.axvline(thr, color='#C75146', ls=(0, (4, 2)), lw=0.9)
    c.annotate(f'Backfire threshold\n$I^{{*}}$ = {thr:.1f} L·kWh$^{{-1}}$', (thr, 0.31),
               xytext=(6, 0), textcoords='offset points', fontsize=6.2,
               color='#C75146', ha='left', fontweight='bold')
    c.text(7.3, 0.09, 'Legacy dry ADDS water', fontsize=6.0,
           color='#9E3B32', ha='center', fontweight='bold')
    c.text(1.35, -0.235, 'Legacy dry saves water', fontsize=6.0,
           color='#1D6B4E', fontweight='bold')
    marks = [(f'US avg / DC-weighted\n2024 ({_I_nat:.2f} / {_I_dc:.2f})', 0.5*(_I_nat+_I_dc)),
             (f'Oregon\n({M.state_intensity("OR"):.1f})', M.state_intensity('OR')),
             (f'Washington\n({M.state_intensity("WA"):.1f})', M.state_intensity('WA'))]
    for nm, x in marks:
        c.vlines(x, -0.88, 0, color='#BFC7CD', lw=0.55,
                 ls=(0, (1.4, 1.6)), zorder=1)
        c.plot([x], [-0.90], marker='^', ms=4.4, color=INK, zorder=6)
        c.annotate(nm, (x, -0.90), xytext=(0, 5), textcoords='offset points',
                   ha='center', fontsize=5.5, color=INK)
    c.set_xlim(0, 8); c.set_ylim(-0.95, 0.45)
    c.set_xlabel('Grid water intensity serving the load (L·kWh$^{-1}$)')
    c.set_ylabel('\u0394$W_{\\mathrm{total}}$, dry \u2212 evaporative\n(L·kWh$^{-1}$ IT)')
    c.legend(loc='upper left', fontsize=5.7, labelspacing=0.35)

    # ---------------- (d) 2050 outcomes by cooling pathway ----------------
    d = FIG.add_subplot(GS[3])
    panel(d, 'd', dx=-0.062, dy=0.015, fs=9.0)
    ygrid(d)
    cases = [('No adoption\n(evaporative)', ('current_evap', 'base'), COOLC['evap']),
             ('Legacy-dry\nadoption', ('adaptive_drychiller', 'base'), COOLC['dry']),
             ('Warm-liquid\nadoption', ('adaptive_warm', 'base'), COOLC['warm']),
             ('Immersion\nadoption', ('adaptive_ferveret', 'base'), COOLC['imm']),
             ('Immersion\nwhole fleet', ('ferveret', 'base'), '#4A3F6B')]
    xs = np.arange(len(cases))
    totals = []
    for i, (lab, (cool, ds), col) in enumerate(cases):
        r = M.run_case('mid', cool, 'ref', dry_scn=ds)
        z = r[r.year == 2050].iloc[0]
        g, s, f = z.W_grid_ML/1e6, z.W_site_ML/1e6, z.W_fab_ML/1e6
        d.bar(xs[i], g, 0.62, color=C_GRID, edgecolor='none', lw=0)
        d.bar(xs[i], s, 0.62, bottom=g, color=C_SITE, edgecolor='none', lw=0)
        d.bar(xs[i], f, 0.62, bottom=g+s, color=C_FAB, edgecolor='none', lw=0)
        tot = g+s+f
        d.hlines(g, xs[i]-0.31, xs[i]+0.31, color='white', lw=0.4, zorder=4)
        d.hlines(g+s, xs[i]-0.31, xs[i]+0.31, color=C_FAB, lw=0.45, zorder=4)
        d.hlines(tot, xs[i]-0.31, xs[i]+0.31, color=C_FAB, lw=0.9, zorder=5)
        totals.append(tot)
        d.annotate(f'{tot:.2f}', (xs[i], tot), xytext=(0, 3.5), textcoords='offset points',
                   ha='center', fontsize=6.4, fontweight='bold')
        if i == 0:
            d.text(xs[i], g + s/2, f'On-site\n{z.theta_site*100:.1f}%',
                   fontsize=5.5, color='white', fontweight='bold',
                   ha='center', va='center', zorder=6)
        if i == len(cases)-1:
            d.text(xs[i], g*0.56, f'Generation\n{z.theta_grid*100:.1f}%',
                   fontsize=5.5, color='white', fontweight='bold',
                   ha='center', va='center', zorder=6)
    d.set_xticks(xs)
    d.set_xticklabels([cl[0] for cl in cases], fontsize=5.6)
    d.set_ylim(0, 2.35)
    d.set_ylabel('2050 $W_{\\mathrm{total}}$ (billion m\u00b3·yr$^{-1}$)')
    hnd = [mpatches.Patch(fc=C_GRID, label='Generation'), mpatches.Patch(fc=C_SITE, label='On-site'),
           mpatches.Patch(fc=C_FAB, label='Chip fab')]
    d.legend(handles=hnd, loc='upper center', ncol=3, fontsize=5.8,
             columnspacing=0.9, handletextpad=0.35, labelspacing=0.30)
    save(FIG, f'{OUT}/fig3_cooling_technology')


# =====================================================================
# FIGURE 4 | attribution, scenario matrix, tornado
# =====================================================================
def figure4():
    _gs = [M.run_case(d, 'adaptive_warm', g).theta_grid.iloc[list(M.YEARS).index(2050)]*100
           for d in ('low', 'mid', 'high') for g in ('slow', 'ref', 'accel')]
    _gmin, _gmax = min(_gs), max(_gs)
    global FIG, GS
    FIG = plt.figure(figsize=(FULLW, 212*MM))
    # panels b and d carry legends anchored below their axes (bbox y = -0.20), so their
    # rows need extra height and spacing or the legend collides with the next panel.
    # Panels b and d need a colour key.  Rather than anchoring a legend to an axes -- which
    # lands either on the bars, on the tick labels, or on the next panel -- each key gets its
    # own thin GridSpec row, so its position is determined by the layout.
    # The key row sits ABOVE its panel: the space under a panel is taken by tick labels and
    # the x-axis title, which a thin row cannot clear, whereas the space above these panels
    # is empty because they carry no titles.
    # Row 6 is an empty spacer: panel d's x-axis title would otherwise run into the e/f row,
    # because a single hspace cannot clear a two-line label on one row only.
    # Each key row is tall enough to clear the x-axis title of the panel above it, and the
    # legend is anchored to the BOTTOM of that row so it reads as a header for the panel
    # below rather than as a footnote to the panel above.
    GS_ALL = FIG.add_gridspec(8, 1,
                              height_ratios=[1.0, 0.34, 1.05, 1.10, 0.34, 1.10, 0.16, 1.12],
                              hspace=0.30, left=0.125, right=0.985, top=0.950, bottom=0.042)
    GS = [GS_ALL[0], GS_ALL[2], GS_ALL[3], GS_ALL[5], GS_ALL[7]]
    LEG_B, LEG_D = GS_ALL[1], GS_ALL[4]

    ATT = [('Location-based\naverage', 'average', C_GRID),
           ('Marginal\ngas CC', 'marginal_gas', '#8FA5B3'),
           ('Marginal\ncoal', 'marginal_coal', '#4E5357'),
           ('Market-based\nRE PPA', 'market', C_SITE)]
    runs = {att: M.run_case('mid', 'adaptive_warm', 'ref', attribution=att)
            for _, att, _ in ATT}
    # ---------------- (a) attributed intensity ----------------
    a = FIG.add_subplot(GS[0])
    # Panel a carries a two-line y-label, which occupies the space where the letter
    # normally sits; the letter is therefore placed just inside the axes.
    panel(a, 'a', dx=0.012, dy=0.015, fs=9.0)
    ygrid(a)
    xs = np.arange(4)
    intensities = [at(runs[att], 2050, 'I_grid_LkWh') for _, att, _ in ATT]
    primary = intensities[0]
    a.axhline(primary, color='#91A6B5', lw=0.75, ls=(0, (2.2, 1.8)), zorder=0)
    for i, (lab, att, col) in enumerate(ATT):
        v = intensities[i]
        a.bar(xs[i], v, 0.62, color=col, edgecolor='none', lw=0, zorder=2)
        a.annotate(f'{v:.2f}', (xs[i], v), xytext=(0, 3.5),
                   textcoords='offset points', ha='center', fontsize=6.4,
                   color=INK, fontweight='bold')
    a.text(3.48, primary + 0.025, 'Location-based baseline', fontsize=5.2,
           color='#6D8495', ha='right', va='bottom')
    a.set_xticks(xs)
    a.set_xticklabels([t[0] for t in ATT], fontsize=5.7)
    a.set_ylim(0, 2.06)
    a.set_ylabel('Assigned grid-water intensity,\n2050 (L·kWh$^{-1}$)', labelpad=3)

    # ---------------- (b) composition inversion ----------------
    b = FIG.add_subplot(GS[1])
    panel(b, 'b', dx=-0.062, dy=0.015, fs=9.0)
    b.grid(axis='x', color=LINEC, lw=0.5, alpha=0.55); b.set_axisbelow(True)
    ypos = np.arange(4)[::-1]
    for i, (lab, att, _) in enumerate(ATT):
        z = runs[att]; z = z[z.year == 2050].iloc[0]
        th = np.array([z.theta_grid, z.theta_site, z.theta_fab])*100
        left = 0
        names = ['Generation', 'On-site', 'Chip fab']
        for v, col, name in zip(th, [C_GRID, C_SITE, C_FAB], names):
            b.barh(ypos[i], v, 0.62, left=left, color=col,
                   edgecolor='none', lw=0)
            if v >= 14:
                b.text(left + v/2, ypos[i], f'{name} {v:.0f}%',
                       ha='center', va='center', fontsize=5.25,
                       color='white', fontweight='bold')
            left += v
        b.text(102.0, ypos[i], f'{z.W_total_ML/1e6:.2f} Bm\u00b3',
               fontsize=5.7, va='center', color=INK, fontweight='bold')
    b.set_yticks(ypos)
    b.set_yticklabels([t[0] for t in ATT], fontsize=5.5)
    b.set_xlim(0, 120)
    b.set_xticks(np.arange(0, 101, 20))
    b.set_xlabel('Share of 2050 $W_{\\mathrm{total}}$ (%)')
    hnd = [mpatches.Patch(fc=C_GRID, label='Generation'), mpatches.Patch(fc=C_SITE, label='On-site'),
           mpatches.Patch(fc=C_FAB, label='Chip fab')]
    # Legends anchored below the axes collide with the next panel in a stacked layout,
    # so they sit inside the axes instead.
    # In a stacked layout a legend has nowhere to sit: inside the axes it covers the bars,
    # below or above them it runs into the neighbouring panel.  It is therefore attached to
    # the FIGURE at the vertical gap that hspace already reserves under this panel.
    # A legend has nowhere to sit in a stacked layout: inside the axes it covers the bars,
    # and anchoring to the axes box puts it on the tick labels, which extend below that box.
    # legend_below() measures the drawn extent and places it in the gap hspace reserves.
    _lb = FIG.add_subplot(LEG_B); _lb.axis('off')
    _lb.legend(handles=hnd, loc='lower center', bbox_to_anchor=(0.5, -0.62), ncol=3, fontsize=6.3,
               columnspacing=1.8, handletextpad=0.5, frameon=False)

    # ---------------- (c) demand x grid heatmap ----------------
    c = FIG.add_subplot(GS[2])
    panel(c, 'c', dx=-0.062, dy=0.015, fs=9.0)
    Mx = np.zeros((3, 3))
    dd = ['low', 'mid', 'high']; gg = ['slow', 'ref', 'accel']
    for i, dsc in enumerate(dd):
        for j, gsc in enumerate(gg):
            r = M.run_case(dsc, 'adaptive_warm', gsc)
            Mx[i, j] = at(r, 2050, 'W_total_ML')/1e6
    im = c.imshow(Mx, cmap='Blues', norm=mcolors.Normalize(0.4, 3.0),
                  aspect='auto', interpolation='nearest')
    for i in range(3):
        for j in range(3):
            is_headline = i == 1 and j == 1
            c.text(j, i - (0.08 if is_headline else 0), f'{Mx[i, j]:.2f}',
                   ha='center', va='center', fontsize=7.2, fontweight='bold',
                   color='white' if Mx[i, j] > 1.7 else INK)
            if is_headline:
                c.text(j, i + 0.22, 'Headline', ha='center', va='center',
                       fontsize=5.2, color='#9E3B32', fontweight='bold')
    c.add_patch(mpatches.Rectangle(
        (0.5, 0.5), 1, 1, fill=False, ec='#C75146', lw=1.5, zorder=5
    ))
    c.set_xticks(range(3))
    c.set_xticklabels(['Slow', 'Reference', 'Accelerated'], fontsize=6.0)
    c.set_yticks(range(3))
    _i50d = list(M.YEARS).index(2050)
    c.set_yticklabels([f'{lb}\n({M.demand_path(k)[_i50d]:,.0f} TWh)'
                       for lb, k in (('Low', 'low'), ('Mid', 'mid'), ('High', 'high'))],
                      fontsize=6.0)
    c.set_xlabel('Grid decarbonisation'); c.set_ylabel('Data-center demand, 2050')
    despine_all(c)
    c.text(1.0, -0.23,
           f'Cell values: billion m\u00b3·yr$^{{-1}}$; generation share: {_gmin:.1f}\u2013{_gmax:.1f}%',
           transform=c.transAxes, fontsize=5.35, color=SOFT, ha='right')

    # ---------------- (d) tornado ----------------
    d = FIG.add_subplot(GS[3])
    panel(d, 'd', dx=-0.062, dy=0.015, fs=9.0)
    d.grid(axis='x', color=LINEC, lw=0.5, alpha=0.55); d.set_axisbelow(True)
    def tot(**kw):
        r = M.run_case(kw.get('demand', 'mid'), kw.get('cooling', 'adaptive_warm'),
                       kw.get('re', 'ref'), hydro_alloc=kw.get('hydro', 1.0),
                       dry_scn=kw.get('dry', 'base'), attribution=kw.get('att', 'average'))
        v = at(r, 2050, 'W_total_ML')/1e6
        fs = kw.get('fabscale')
        if fs is not None:
            f = at(r, 2050, 'W_fab_ML')/1e6
            v = v - f + fs*f
        return v
    B = tot()
    bars = [('Electricity attribution\n(Market \u2194 marginal coal)', tot(att='market'), tot(att='marginal_coal')),
            ('Demand scenario\n(Low \u2194 high)', tot(demand='low'), tot(demand='high')),
            ('Hydropower factor\n(Excluded \u2194 Macknick 17)', tot(hydro=0.0), tot(hydro=MACK)),
            ('Grid decarbonisation\n(Accelerated \u2194 slow)', tot(re='accel'), tot(re='slow')),
            ('Cooling turnover\n(Fast \u2194 slow)', tot(dry='fast'), tot(dry='slow')),
            ('Chip-fab water\n(\u00d70 \u2194 \u00d710)', tot(fabscale=0.0), tot(fabscale=10.0))]
    bars = sorted(bars, key=lambda r: abs(r[2]-r[1]), reverse=True)
    ypos = np.arange(len(bars))[::-1]
    below_col, above_col = '#86B7A6', '#D79A78'
    for (lab, lo, hi), yp in zip(bars, ypos):
        l, h = min(lo, hi), max(lo, hi)
        if l < B:
            d.barh(yp, min(B, h)-l, left=l, height=0.52,
                   color=below_col, edgecolor='none', lw=0, zorder=2)
        if h > B:
            d.barh(yp, h-max(B, l), left=max(B, l), height=0.52,
                   color=above_col, edgecolor='none', lw=0, zorder=2)
        d.plot([l], [yp], marker='o', ms=2.8, color='#39735F', zorder=4)
        d.plot([h], [yp], marker='o', ms=2.8, color='#A6523E', zorder=4)
        d.annotate(f'{lo:.2f}', (min(lo, hi), yp), xytext=(-3, 0), textcoords='offset points',
                   ha='right', va='center', fontsize=5.6, color='#39735F')
        d.annotate(f'{hi:.2f}', (max(lo, hi), yp), xytext=(3, 0), textcoords='offset points',
                   ha='left', va='center', fontsize=5.6, color='#A6523E')
    d.axvline(B, color=INK, lw=1.0, zorder=5)
    d.annotate(f'Headline {B:.2f}', (B, len(bars)-0.38), xytext=(0, 5),
               textcoords='offset points', ha='center', fontsize=5.9,
               fontweight='bold', annotation_clip=False)
    d.set_yticks(ypos)
    d.set_yticklabels([b_[0] for b_ in bars], fontsize=5.4)
    d.set_xlim(0, 2.78)
    d.set_ylim(-0.55, len(bars)-0.05)
    d.set_xlabel('2050 $W_{\\mathrm{total}}$ (billion m\u00b3·yr$^{-1}$)')
    _ld = FIG.add_subplot(LEG_D); _ld.axis('off')
    _ld.legend(handles=[mpatches.Patch(fc=below_col, label='Below headline'),
                        mpatches.Patch(fc=above_col, label='Above headline')],
               loc='lower center', bbox_to_anchor=(0.5, -0.05), ncol=2, fontsize=6.3,
               columnspacing=1.8, handletextpad=0.5, frameon=False)

    # --- panels e-f | structural alternatives to perpetual-CAGR demand ------------
    i50 = list(M.YEARS).index(2050)
    sub = GS[4].subgridspec(1, 2, wspace=0.40)
    e = FIG.add_subplot(sub[0]); f = FIG.add_subplot(sub[1])
    """Perpetual-CAGR family vs structural post-2030 alternatives."""
    fig, (a, b) = plt.subplots(1, 2, figsize=(FULLW, 74*MM))
    panel(e, 'e', dx=-0.205, dy=0.030, fs=9.0); ygrid(e)
    for s, col, ls, lab in [('low', '#7FA8C9', (0, (3, 2)), 'CAGR 2.0%'),
                            ('mid', C_GRID, '-', 'CAGR 3.5% (reference)'),
                            ('high', '#1F4E79', (0, (3, 2)), 'CAGR 5.0%')]:
        e.plot(M.YEARS, M.demand_path(s), color=col, ls=ls, lw=1.5 if s == 'mid' else 1.1, label=lab)
    for s, col, lab in [('share', C_SITE, 'share held at 2030 level'),
                        ('satur', S_SLOW, 'logistic saturation'),
                        ('declin', COOLC['imm'], 'declining growth rate'),
                        ('capped', C_FAB, 'interconnection capped')]:
        e.plot(M.YEARS, M.demand_path(s), color=col, lw=1.2, label=lab)
    e.plot([2024, 2028, 2030], [192, 464, 649], 'D', ms=3.4, color=INK, zorder=6)
    e.annotate('LBNL 2025 Update anchors', (2028, 464), xytext=(6, -4),
               textcoords='offset points', fontsize=5.8, ha='left', va='top', color=INK)
    e.set_xlim(2023, 2050); a.set_ylim(0, 2400)
    e.set_ylabel('Data center electricity (TWh yr$^{-1}$)')
    e.legend(loc='upper left', bbox_to_anchor=(0.0, 1.04), fontsize=5.6, labelspacing=0.26)
    ptitle(a, 'Demand pathways')

    panel(f, 'f', dx=-0.205, dy=0.030, fs=9.0); ygrid(f)
    names = ['low', 'share', 'satur', 'declin', 'mid', 'capped', 'high']
    NAMES_LABEL = ['CAGR 2.0%', 'share held', 'saturation', 'declining', 'CAGR 3.5%',
                   'capped', 'CAGR 5.0%']
    tot = [M.run_case(s, 'adaptive_warm', 'ref').W_total_ML.iloc[i50]/1e6 for s in names]
    gen = [M.run_case(s, 'adaptive_warm', 'ref').theta_grid.iloc[i50]*100 for s in names]
    cols = ['#7FA8C9', C_SITE, S_SLOW, COOLC['imm'], C_GRID, C_FAB, '#1F4E79']
    xs = np.arange(len(names))
    f.bar(xs, tot, 0.62, color=cols, edgecolor='white', lw=0.4)
    for x, t, g in zip(xs, tot, gen):
        f.annotate(f'{t:.2f}', (x, t), xytext=(0, 3), textcoords='offset points',
                   ha='center', fontsize=6.2, fontweight='bold')
        f.annotate(f'{g:.0f}%', (x, t*0.5), ha='center', va='center', fontsize=5.8,
                   color=(INK if x in (0,) else 'white'), fontweight='bold')
    f.set_xticks(xs)
    f.set_xticklabels(NAMES_LABEL, fontsize=5.8, rotation=30, ha='right')
    f.set_ylim(0, 3.1)
    f.set_ylabel('2050 water use (billion m$^3$ yr$^{-1}$)')
    ptitle(b, 'Totals differ; the generation share does not')

    save(FIG, f'{OUT}/fig4_uncertainty_and_conventions')


if __name__ == '__main__':
    print('Building main figures ->', OUT)
    figure1(); figure2(); figure3(); figure4()
    print('done.')
