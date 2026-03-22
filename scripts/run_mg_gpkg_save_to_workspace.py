# -*- coding: utf-8 -*-
"""CascadeProjects의 mg_*.png 4개를 mg_gpkg_시각화결과 폴더로 복사"""
import shutil
from pathlib import Path

src_dir = Path(r"C:/Users/a0109/CascadeProjects")
# 이 스크립트 기준: 1최종_LH/scripts/ → 1최종_LH/mg_gpkg_시각화결과
dst_dir = Path(__file__).resolve().parent.parent / "mg_gpkg_시각화결과"
dst_dir.mkdir(parents=True, exist_ok=True)

copied = []
for f in src_dir.glob("mg_*.png"):
    dest = dst_dir / f.name
    shutil.copy2(f, dest)
    copied.append(dest)

print("복사 완료:", len(copied), "개")
for p in copied:
    print(" ", p)
