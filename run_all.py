#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run the full pipeline, from the raw files in data/ to every table and figure.

    python run_all.py               # all steps
    python run_all.py --no-figures  # skip the two figure scripts

Each step is a stand-alone script in code/ and can also be run on its own, in this order.
"""
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
STEPS = [
    ('00_prepare_derived.py',       'derived datasets from EIA-923 and WRI Aqueduct  -> derived/'),
    ('01_extract_parameters.py',    'model parameters with provenance                -> extracted_parameters.csv, derived/model_parameters.json'),
    ('02_build_results_by_year.py', 'scenario results, 81 combinations x 2023-2050    -> results_by_year_FINAL.xlsx'),
    ('03_make_main_tables.py',      'main-text Tables 1-2                            -> manuscript/main_tables.tex'),
    ('make_si_tables.py',           'Supplementary Tables S1-S11                     -> supplementary/si_tables.tex'),
    ('make_figures_publication.py', 'main-text Figs 1-4                              -> figures/'),
    ('make_figures_si.py',          'Supplementary Figs S1-S9                        -> figures/'),
]


def main():
    skip_figures = '--no-figures' in sys.argv[1:]
    root = os.environ.get('PROJECT_ROOT', ROOT)     # folder with data/ and the outputs (default: this repository)
    env = dict(os.environ, PROJECT_ROOT=root)
    t_all = time.time()
    for script, what in STEPS:
        if skip_figures and script.startswith('make_figures'):
            continue
        print(f'\n=== {script}: {what}', flush=True)
        t = time.time()
        subprocess.run([sys.executable, os.path.join(ROOT, 'code', script)], cwd=root, env=env, check=True)
        print(f'=== {script} finished in {time.time() - t:.0f} s', flush=True)
    print(f'\nAll steps finished in {time.time() - t_all:.0f} s.')


if __name__ == '__main__':
    main()
