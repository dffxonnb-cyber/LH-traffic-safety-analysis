from __future__ import annotations

import csv
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
            PROJECT_ROOT / "docs" / "canonical_project_scope.md",
            PROJECT_ROOT / "docs" / "field-review-handoff.md",
            PROJECT_ROOT / "docs" / "images" / "portfolio-performance-summary.svg",
            PROJECT_ROOT / "docs" / "images" / "portfolio-validation-summary.svg",
            PROJECT_ROOT / "docs" / "images" / "portfolio-score-comparison-note.svg",
            PROJECT_ROOT / "docs" / "images" / "public-top20-priority-preview.svg",
            PROJECT_ROOT / "docs" / "data" / "gyosan_effect_reduction_by_gid.csv",
            PROJECT_ROOT / "docs" / "data" / "public_top20_priority.csv",
            PROJECT_ROOT / "docs" / "data" / "public_evidence_status.csv",
        ]
        self.assertEqual([path for path in expected if not path.exists()], [])

    def test_public_top20_schema_order_and_claim_boundary(self) -> None:
        path = PROJECT_ROOT / "docs" / "data" / "public_top20_priority.csv"
        with path.open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))

        self.assertEqual(len(rows), 20)
        self.assertEqual([int(row["rank"]) for row in rows], list(range(1, 21)))

        grid_ids = [row["grid_id"] for row in rows]
        self.assertEqual(len(grid_ids), len(set(grid_ids)))

        scores = [float(row["normalized_risk_score"]) for row in rows]
        self.assertEqual(scores, sorted(scores, reverse=True))
        self.assertTrue(all(0.0 <= score <= 1.0 for score in scores))

        expected_boundary = "inspection-priority signal only; not field-validated impact"
        self.assertTrue(all(row["claim_boundary"] == expected_boundary for row in rows))
        self.assertTrue(
            all("needs confirmation" in row["facility_package_public_status"] for row in rows)
        )
        self.assertTrue(
            all("needs confirmation" in row["recommendation_reason_public_status"] for row in rows)
        )

    def test_public_top20_matches_tracked_canonical_source(self) -> None:
        source_path = PROJECT_ROOT / "docs" / "data" / "gyosan_effect_reduction_by_gid.csv"
        public_path = PROJECT_ROOT / "docs" / "data" / "public_top20_priority.csv"

        with source_path.open(encoding="utf-8-sig", newline="") as handle:
            source_rows = sorted(
                csv.DictReader(handle),
                key=lambda row: int(row["grid_rank"]),
            )[:20]
        with public_path.open(encoding="utf-8-sig", newline="") as handle:
            public_rows = list(csv.DictReader(handle))

        self.assertEqual(
            [row["gid"] for row in source_rows],
            [row["grid_id"] for row in public_rows],
        )
        self.assertEqual(
            [f'{float(row["RiskScore_A_norm_grid"]):.4f}' for row in source_rows],
            [row["normalized_risk_score"] for row in public_rows],
        )

    def test_public_evidence_status_keeps_unverified_results_explicit(self) -> None:
        path = PROJECT_ROOT / "docs" / "data" / "public_evidence_status.csv"
        with path.open(encoding="utf-8-sig", newline="") as handle:
            rows = {row["evidence"]: row for row in csv.DictReader(handle)}

        self.assertEqual(rows["dashboard deployment URL"]["status"], "needs confirmation")
        self.assertEqual(
            rows["facility package and recommendation reason"]["status"],
            "needs confirmation",
        )
        self.assertEqual(rows["field inspection and accident reduction"]["status"], "not available")

    def test_handoff_uses_existing_audit_link_and_canonical_score(self) -> None:
        handoff = (PROJECT_ROOT / "docs" / "field-review-handoff.md").read_text(encoding="utf-8")
        self.assertIn("RiskScore_A_norm_grid", handoff)
        self.assertIn("canonical_project_scope.md", handoff)
        self.assertIn("evidence_audit.md", handoff)
        self.assertNotIn("public_evidence_audit.json", handoff)

    def test_canonical_scope_freezes_legacy_paths(self) -> None:
        scope = (PROJECT_ROOT / "docs" / "canonical_project_scope.md").read_text(encoding="utf-8")
        self.assertIn("공간 좌표 포함 Random Forest", scope)
        self.assertIn("RiskScore_A_norm_grid", scope)
        self.assertIn("우선순위_점수", scope)
        self.assertIn("needs confirmation", scope)
        self.assertIn("새 모델 추가", scope)


if __name__ == "__main__":
    unittest.main()
