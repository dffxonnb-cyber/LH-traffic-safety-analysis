# -*- coding: utf-8 -*-
"""Create 06_grf_shap_100x100_hanam_gyosan.ipynb from dongtan notebook with region config changed."""
from pathlib import Path

base = Path(__file__).resolve().parent
src = base / "06_grf_shap_100x100_dongtan.ipynb"
dest = base / "06_grf_shap_100x100_hanam_gyosan.ipynb"

text = src.read_text(encoding="utf-8")

# Region config for 하남교산
replacements = [
    ("REGION_NAME = 'dongtan'", "REGION_NAME = 'hanam_gyosan'"),
    ("REGION_FILTER_REGEX = '화성'  # auto-generated", "REGION_FILTER_REGEX = '하남'  # 하남시 (교산·미사 포함)"),
    (
        "REGION_ZONE_GEOJSON_PATH = None  # None이면 동탄용 4개신도시 토지이용계획도 경로 자동 사용",
        "REGION_ZONE_GEOJSON_PATH = None  # None이면 하남교산 토지이용계획도(23번) 경로 자동 사용",
    ),
    (
        "REGION_ZONE_NAME_REGEX = '화성동탄|동탄'  # 화성 중 동탄 구역만 사용 (화성과 분리)",
        "REGION_ZONE_NAME_REGEX = '하남교산|교산|감일'  # 하남 중 교산·감일 지구만 사용 (미사와 분리)",
    ),
]

for old, new in replacements:
    text = text.replace(old, new)

# When zone_path is None, use 23번 for hanam_gyosan (default zone file)
old_default_zone = "_default_zone = BASE_DIR / 'data' / '토지_데이터' / '22._토지이용계획도_(4개_신도시).geojson'"
new_default_zone = "_default_zone = BASE_DIR / 'data' / '토지_데이터' / ('23._토지이용계획도_(하남교산).geojson' if region_name == 'hanam_gyosan' else '22._토지이용계획도_(4개_신도시).geojson')"
text = text.replace(old_default_zone, new_default_zone)

dest.write_text(text, encoding="utf-8")
print("Written:", dest)
