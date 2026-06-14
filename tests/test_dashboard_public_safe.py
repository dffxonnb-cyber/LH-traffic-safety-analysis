from __future__ import annotations

import sys
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DASHBOARD_ROOT = PROJECT_ROOT / "dashboard"
if str(DASHBOARD_ROOT) not in sys.path:
    sys.path.insert(0, str(DASHBOARD_ROOT))


import app  # noqa: E402


class DashboardPublicSafeTests(unittest.TestCase):
    def test_public_safe_mode_is_used_without_private_data(self) -> None:
        self.assertFalse(app.dashboard_data_available())
        self.assertGreaterEqual(len(app.missing_dashboard_paths()), 1)

    def test_public_safe_visuals_exist(self) -> None:
        missing = [path for path in app.PUBLIC_SAFE_VISUALS.values() if not path.exists()]
        self.assertEqual(missing, [])

    def test_portfolio_evidence_assets_exist(self) -> None:
        expected = [
            PROJECT_ROOT / "docs" / "images" / "portfolio-performance-summary.svg",
            PROJECT_ROOT / "docs" / "images" / "portfolio-validation-summary.svg",
            PROJECT_ROOT / "docs" / "images" / "public-top20-priority-preview.svg",
            PROJECT_ROOT / "docs" / "data" / "public_top20_priority.csv",
        ]
        self.assertEqual([path for path in expected if not path.exists()], [])

    def test_public_top20_is_limited_and_marks_non_public_fields(self) -> None:
        import csv

        path = PROJECT_ROOT / "docs" / "data" / "public_top20_priority.csv"
        with path.open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))

        self.assertEqual(len(rows), 20)
        self.assertEqual([int(row["rank"]) for row in rows], list(range(1, 21)))
        self.assertTrue(
            all("needs confirmation" in row["facility_package_public_status"] for row in rows)
        )


if __name__ == "__main__":
    unittest.main()
