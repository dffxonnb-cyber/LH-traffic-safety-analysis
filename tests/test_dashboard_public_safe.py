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


if __name__ == "__main__":
    unittest.main()
