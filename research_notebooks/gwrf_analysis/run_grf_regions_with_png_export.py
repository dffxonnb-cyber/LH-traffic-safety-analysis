from __future__ import annotations

import argparse
import base64
import json
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Dict, List


REGION_SPECS: Dict[str, dict] = {
    "misa": {"gbn_regex": "\ud558\ub0a8|\ubbf8\uc0ac", "zone_regex": "\ud558\ub0a8\ubbf8\uc0ac|\ubbf8\uc0ac"},
    "dongtan": {"gbn_regex": "\ud654\uc131", "zone_regex": "\ud654\uc131\ub3d9\ud0c4|\ub3d9\ud0c4"},
    "songpa": {"gbn_regex": "\uc1a1\ud30c", "zone_regex": None},
    "pangyo": {"gbn_regex": "\uc131\ub0a8", "zone_regex": "\uc131\ub0a8\ud310\uad50|\ud310\uad50"},
}


def _to_source(code: str) -> List[str]:
    return [line + "\n" for line in code.rstrip("\n").split("\n")]


def _set_region_params(nb_obj: dict, region: str, gbn_regex: str, zone_regex: str | None) -> None:
    updated = False
    for cell in nb_obj.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        src = "".join(cell.get("source", []))
        if "REGION_NAME" in src and "REGION_FILTER_REGEX" in src and "TARGET_REG" in src:
            src, n1 = re.subn(r"^REGION_NAME\s*=.*$", f"REGION_NAME = '{region}'", src, flags=re.MULTILINE)
            src, n2 = re.subn(
                r"^REGION_FILTER_REGEX\s*=.*$",
                lambda _m: f"REGION_FILTER_REGEX = {gbn_regex!r}  # auto-generated",
                src,
                flags=re.MULTILINE,
            )
            zone_expr = "None" if zone_regex is None else repr(zone_regex)
            src, n3 = re.subn(
                r"^REGION_ZONE_NAME_REGEX\s*=.*$",
                lambda _m: f"REGION_ZONE_NAME_REGEX = {zone_expr}  # auto-generated",
                src,
                flags=re.MULTILINE,
            )
            if n1 != 1 or n2 != 1 or n3 != 1:
                raise RuntimeError(f"Failed to set region parameters in config cell: region={region}")
            cell["source"] = _to_source(src)
            updated = True
            break

    if not updated:
        raise RuntimeError("Config cell with REGION_NAME/REGION_FILTER_REGEX not found")


def _export_pngs(exec_nb: Path, png_dir: Path, manifest_path: Path) -> int:
    obj = json.loads(exec_nb.read_text(encoding="utf-8"))
    png_dir.mkdir(parents=True, exist_ok=True)

    png_count = 0
    manifest = []
    for ci, cell in enumerate(obj.get("cells", [])):
        for oi, out in enumerate(cell.get("outputs", [])):
            data = out.get("data", {}) if isinstance(out, dict) else {}
            img = data.get("image/png")
            if not img:
                continue
            if isinstance(img, list):
                img = "".join(img)
            try:
                raw = base64.b64decode(img)
            except Exception:
                continue
            fn = png_dir / f"cell_{ci:03d}_out_{oi:02d}.png"
            fn.write_bytes(raw)
            png_count += 1
            manifest.append({"cell": ci, "output": oi, "file": fn.name})

    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return png_count


def _run_region(base_dir: Path, template_nb: Path, region: str, gbn_regex: str, zone_regex: str | None, batch_tag: str) -> dict:
    run_dir = base_dir / f"run_{region}_png_{batch_tag}"
    run_dir.mkdir(parents=True, exist_ok=True)

    region_nb = base_dir / f"06_grf_shap_100x100_{region}.ipynb"
    exec_nb = base_dir / f"06_grf_shap_100x100_{region}_executed_{batch_tag}.ipynb"
    log_path = run_dir / "run.log"

    nb_obj = json.loads(template_nb.read_text(encoding="utf-8"))
    _set_region_params(nb_obj, region=region, gbn_regex=gbn_regex, zone_regex=zone_regex)
    region_nb.write_text(json.dumps(nb_obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    cmd = [
        sys.executable,
        "-m",
        "nbconvert",
        "--to",
        "notebook",
        "--execute",
        str(region_nb),
        "--output",
        exec_nb.name,
        "--ExecutePreprocessor.timeout=-1",
    ]

    result = {
        "region": region,
        "gbn_regex": gbn_regex,
        "zone_regex": zone_regex,
        "region_notebook": str(region_nb),
        "executed_notebook": str(exec_nb),
        "run_dir": str(run_dir),
        "log": str(log_path),
        "status": "failed",
        "png_count": 0,
    }

    with log_path.open("w", encoding="utf-8") as log:
        log.write(f"[REGION] {region}\n")
        log.write(f"[GBN_REGEX] {gbn_regex}\n")
        log.write(f"[ZONE_REGEX] {zone_regex}\n")
        log.write(f"[NOTEBOOK] {region_nb}\n")
        log.write("[CMD] " + " ".join(cmd) + "\n")
        log.flush()

        proc = subprocess.Popen(
            cmd,
            cwd=str(base_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            log.write(line)
        rc = proc.wait()
        log.write(f"\n[NBEXEC_EXIT] code={rc}\n")

        if rc != 0:
            result["status"] = "failed"
            return result

        png_dir = run_dir / "png_exports"
        manifest_path = run_dir / "png_manifest.json"
        png_count = _export_pngs(exec_nb, png_dir, manifest_path)

        log.write(f"[PNG_EXPORTED] count={png_count} dir={png_dir}\n")
        log.write(f"[MANIFEST] {manifest_path}\n")
        log.write(f"[EXEC_NOTEBOOK] {exec_nb}\n")
        log.write("[DONE]\n")

    result["status"] = "ok"
    result["png_count"] = png_count
    result["png_manifest"] = str(run_dir / "png_manifest.json")
    result["png_dir"] = str(run_dir / "png_exports")
    result["feature_map_dir"] = str(base_dir.parent / "1\ud53c\ucc98\ubcc0\uc218\ubcc4png" / region)
    return result


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run GRF/SHAP notebooks by region and export PNG outputs")
    p.add_argument(
        "--regions",
        type=str,
        default="dongtan,songpa,pangyo",
        help="Comma-separated regions. Available: misa,dongtan,songpa,pangyo",
    )
    p.add_argument("--max-workers", type=int, default=3, help="Parallel workers")
    p.add_argument("--template", type=str, default="06_grf_shap_100x100_misa.ipynb")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    base_dir = Path(__file__).resolve().parent
    template_nb = base_dir / args.template
    if not template_nb.exists():
        raise SystemExit(f"Template notebook not found: {template_nb}")

    regions = [r.strip().lower() for r in args.regions.split(",") if r.strip()]
    bad = [r for r in regions if r not in REGION_SPECS]
    if bad:
        raise SystemExit(f"Unknown regions: {bad}. Available={sorted(REGION_SPECS)}")

    batch_tag = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_path = base_dir / f"run_regions_batch_summary_{batch_tag}.json"

    print(f"[BATCH] regions={regions} workers={args.max_workers}")
    results: List[dict] = []

    with ThreadPoolExecutor(max_workers=max(1, args.max_workers)) as ex:
        futures = {
            ex.submit(
                _run_region,
                base_dir,
                template_nb,
                region,
                REGION_SPECS[region]["gbn_regex"],
                REGION_SPECS[region]["zone_regex"],
                batch_tag,
            ): region
            for region in regions
        }
        for fut in as_completed(futures):
            region = futures[fut]
            try:
                res = fut.result()
            except Exception as e:
                res = {
                    "region": region,
                    "status": "failed",
                    "error": str(e),
                }
            results.append(res)
            print(f"[DONE] region={region} status={res.get('status')} png={res.get('png_count', 0)}")

    results = sorted(results, key=lambda x: x.get("region", ""))
    summary_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[SUMMARY] {summary_path}")


if __name__ == "__main__":
    main()
