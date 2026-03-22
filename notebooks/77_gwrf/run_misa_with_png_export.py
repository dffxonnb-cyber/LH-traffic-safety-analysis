from pathlib import Path
import subprocess
import json
import base64
from datetime import datetime
import sys


def main():
    base_dir = Path(__file__).resolve().parent
    nb = base_dir / "06_grf_shap_100x100_misa.ipynb"
    if not nb.exists():
        raise SystemExit(f"Notebook not found: {nb}")

    tag = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = base_dir / f"run_misa_png_{tag}"
    run_dir.mkdir(parents=True, exist_ok=True)

    exec_nb = base_dir / f"06_grf_shap_100x100_misa_executed_{tag}.ipynb"
    log_path = run_dir / "run.log"

    cmd = [
        sys.executable, "-m", "nbconvert",
        "--to", "notebook",
        "--execute", str(nb),
        "--output", exec_nb.name,
        "--ExecutePreprocessor.timeout=-1",
    ]

    with log_path.open("w", encoding="utf-8") as log:
        log.write(f"[START] notebook={nb}\n")
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
            log.flush()

        rc = proc.wait()
        log.write(f"\n[NBEXEC_EXIT] code={rc}\n")
        log.flush()

        if rc != 0:
            print(f"FAILED: notebook execution rc={rc}")
            print(f"LOG={log_path}")
            return

        # Extract all image/png outputs from executed notebook
        obj = json.loads(exec_nb.read_text(encoding="utf-8"))
        png_dir = run_dir / "png_exports"
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

        manifest_path = run_dir / "png_manifest.json"
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

        log.write(f"[PNG_EXPORTED] count={png_count} dir={png_dir}\n")
        log.write(f"[MANIFEST] {manifest_path}\n")
        log.write(f"[EXEC_NOTEBOOK] {exec_nb}\n")
        log.write("[DONE]\n")

    print(f"RUN_DIR={run_dir}")
    print(f"EXEC_NOTEBOOK={exec_nb}")
    print(f"LOG={log_path}")


if __name__ == "__main__":
    main()
