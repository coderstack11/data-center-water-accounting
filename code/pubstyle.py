#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Shared publication style for the manuscript figures.

Nature sizing: double column 183 mm (7.205 in), single 89 mm (3.504 in).
The typography follows the serif reference supplied for the manuscript.  Times
New Roman is used when it is installed (the normal case on Windows), with
metric-compatible serif fallbacks for Linux and macOS.  The colour system is
colour-blind-safe and is shared by all four main figures.
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np

import os as _os
for _d in (
    'C:/Windows/Fonts',
    _os.path.expanduser('~/AppData/Local/Microsoft/Windows/Fonts'),
    '/usr/share/fonts',
    '/Library/Fonts',
    '/System/Library/Fonts',
    _os.path.expanduser('~/Library/Fonts'),
):
    if _os.path.isdir(_d):
        for _f in fm.findSystemFonts([_d]):
            try:
                fm.fontManager.addfont(_f)
            except Exception:
                pass


def configure_publication_style():
    """Apply the same serif typography and line styling to every figure."""
    plt.rcParams.update({
        'font.family': 'serif',
        'font.serif': [
            'Times New Roman',
            'Times',
            'Nimbus Roman',
            'Liberation Serif',
            'DejaVu Serif',
        ],
        'font.size': 7.2,
        'font.weight': 'normal',
        'mathtext.fontset': 'stix',
        'mathtext.default': 'regular',
        'axes.titlesize': 7.6,
        'axes.titleweight': 'normal',
        'axes.labelsize': 7.2,
        'axes.labelweight': 'normal',
        'axes.linewidth': 0.6,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.grid': False,
        'axes.unicode_minus': True,
        'xtick.labelsize': 6.7,
        'ytick.labelsize': 6.7,
        'xtick.major.width': 0.6,
        'ytick.major.width': 0.6,
        'xtick.major.size': 2.4,
        'ytick.major.size': 2.4,
        'legend.fontsize': 6.3,
        'legend.frameon': False,
        'legend.handlelength': 1.6,
        'legend.handletextpad': 0.5,
        'legend.borderaxespad': 0.35,
        'pdf.fonttype': 42,
        'ps.fonttype': 42,
        'svg.fonttype': 'none',
        'figure.dpi': 110,
        'savefig.dpi': 1200,
        'savefig.facecolor': 'white',
        'savefig.bbox': 'tight',
        'savefig.pad_inches': 0.07,
    })


configure_publication_style()

MM = 1/25.4
FULLW, HALFW = 183*MM, 89*MM

# ---- palette ---------------------------------------------------------------
C_GRID, C_SITE, C_FAB = '#2F5F8A', '#3FA37B', '#E8A64A'      # lifecycle components
T_GRID, T_SITE, T_FAB = '#E1EAF2', '#E2F2EA', '#FAEEDB'      # light tints (boxes)
S_SLOW, S_REF, S_ACC  = '#B8622F', '#2F5F8A', '#3FA37B'      # grid-decarbonisation paths
INK, SOFT, LINEC      = '#1A1A1A', '#5A5A5A', '#D9D9D9'
COOLC = {'evap': '#C75146', 'hybrid': '#E8A64A', 'dlc': '#B5A642',
         'warm': '#2F5F8A', 'imm': '#6B5B95', 'dry': '#8C8C8C'}

def panel(ax, letter, dx=-0.105, dy=0.026, fs=8.6):
    """Bold lowercase panel letter at the top-left, Nature style."""
    ax.text(dx, 1.0 + dy, letter, transform=ax.transAxes, fontsize=fs,
            fontweight='bold', va='bottom', ha='right', color=INK)


def ptitle(ax, s, fs=7.4, pad=4):
    ax.set_title(s, fontsize=fs, loc='left', color=INK, pad=pad)


def ygrid(ax, alpha=0.55):
    ax.grid(axis='y', color=LINEC, lw=0.5, alpha=alpha, zorder=0)
    ax.set_axisbelow(True)


def despine_all(ax):
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)


def save(fig, path_noext, dpi=1200):
    fig.savefig(path_noext + '.png', dpi=dpi)
    fig.savefig(path_noext + '.pdf', dpi=dpi)
    plt.close(fig)
    print('  wrote', path_noext + '.{png,pdf}')


def configure_stacked_style(scale=1.0):
    """Typography for the stacked full-width main figures.

    configure_publication_style() sizes text for an 89 mm single-column panel.  The main
    figures now stack full-width panels, so a panel is roughly twice as wide while the
    point sizes stay fixed, which makes the text look half as large.  This profile scales
    the type and line weights so that text occupies the same fraction of the panel as in
    the original single-column design.
    """
    configure_publication_style()
    plt.rcParams.update({
        'font.size':        7.2*scale,
        'axes.titlesize':   7.6*scale,
        'axes.labelsize':   7.2*scale,
        'xtick.labelsize':  6.7*scale,
        'ytick.labelsize':  6.7*scale,
        'legend.fontsize':  6.3*scale,
        'axes.linewidth':   0.6*scale,
        'lines.linewidth':  1.4*scale/1.15,
        'xtick.major.width': 0.6*scale,
        'ytick.major.width': 0.6*scale,
        'xtick.major.size':  2.4*scale,
        'ytick.major.size':  2.4*scale,
        'savefig.pad_inches': 0.04,
    })


def legend_below(fig, ax, handles, gap=0.010, **kw):
    """Place a legend under an axes, clear of its tick labels and axis title.

    ax.get_position() returns the axes box only; tick labels and the x-axis label extend
    below it, so anchoring to that box puts the legend on top of them.  Drawing once and
    measuring the tight bounding box gives the true lower edge.
    """
    fig.canvas.draw()
    bb = ax.get_tightbbox(fig.canvas.get_renderer()).transformed(fig.transFigure.inverted())
    kw.setdefault('loc', 'upper center')
    kw.setdefault('frameon', False)
    return fig.legend(handles=handles, bbox_to_anchor=(bb.x0 + bb.width/2, bb.y0 - gap), **kw)
