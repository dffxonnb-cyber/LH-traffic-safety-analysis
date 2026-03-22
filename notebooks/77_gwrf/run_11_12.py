# -*- coding: utf-8 -*-
"""11, 12 노트북 실행 (셀 코드 추출 후 exec)"""
import json
import sys
from pathlib import Path

def run_notebook(nb_path: Path) -> bool:
    with open(nb_path, encoding='utf-8') as f:
        nb = json.load(f)
    
    cells = [c for c in nb.get('cells', []) if c.get('cell_type') == 'code']
    g = {'__name__': '__main__', '__builtins__': __builtins__}
    for i, cell in enumerate(cells):
        src = ''.join(cell.get('source', []))
        if not src.strip() or src.strip().startswith('%'):
            continue
        try:
            exec(src, g)
        except Exception as e:
            print(f"[Cell {i+1}] Error: {e}", file=sys.stderr)
            return False
    return True

if __name__ == '__main__':
    base = Path(__file__).resolve().parent
    for name in ['11_blended_weight_analysis.ipynb', '12_proxy_blended_risk.ipynb']:
        path = base / name
        if path.exists():
            print(f"\n=== Running {name} ===")
            ok = run_notebook(path)
            print(f"Done: {name} {'OK' if ok else 'FAILED'}")
            if not ok:
                sys.exit(1)
        else:
            print(f"Skip (not found): {name}")
    print("\nAll done.")
