# -*- coding: utf-8 -*-
"""Move GWRF-related files into notebooks/gwrf/. Run from repo root or: python -c \"exec(open('1최종_LH/notebooks/move_gwrf.py', encoding='utf-8').read())\" """
import os
import shutil

# Support both direct run and exec(open(...).read())
try:
    _file = __file__
except NameError:
    _file = os.path.join(os.getcwd(), "1최종_LH", "notebooks", "move_gwrf.py")
here = os.path.dirname(os.path.abspath(_file))
gwrf_dir = os.path.join(here, "gwrf")
os.makedirs(gwrf_dir, exist_ok=True)

files = [
    "06_grf_shap_100x100.ipynb",
    "06_shap_100x100.ipynb",
    "10_GWRF_vs_Greedy_Algorithm_Comparison.ipynb",
    "GWRF_vs_Priority_Comparison.csv",
]
for name in files:
    src = os.path.join(here, name)
    dst = os.path.join(gwrf_dir, name)
    if os.path.isfile(src):
        shutil.move(src, dst)
        print("Moved:", name)
    else:
        print("Not found:", src)
