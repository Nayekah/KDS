from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from src.simulation_exports import simulation_summary_rows, write_simulation_artifacts


class SimulationExportTests(unittest.TestCase):
    def test_summary_rows_include_all_report_fields(self) -> None:
        rows = simulation_summary_rows(n_trials=2, seed=101)

        self.assertEqual(len(rows), 6)
        for row in rows:
            self.assertIn("scenario", row)
            self.assertIn("label", row)
            self.assertIn("mechanism", row)
            self.assertIn("n_trials", row)
            self.assertIn("escape_probability", row)
            self.assertIn("mean_escape_time", row)
            self.assertIn("mean_escape_step", row)
            self.assertIn("mean_final_cancer_cells", row)
            self.assertIn("mean_final_total_cells", row)
            self.assertIn("mean_final_cancer_fraction", row)

    def test_write_simulation_artifacts_creates_csv_and_latex_table(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            csv_path = root / "simulation_summary.csv"
            tex_path = root / "generated-simulation-results.tex"

            rows = write_simulation_artifacts(
                n_trials=2,
                seed=101,
                csv_path=csv_path,
                tex_path=tex_path,
            )

            self.assertTrue(csv_path.exists())
            self.assertTrue(tex_path.exists())
            with csv_path.open(newline="", encoding="utf-8") as handle:
                csv_rows = list(csv.DictReader(handle))
            self.assertEqual(len(csv_rows), len(rows))

            tex = tex_path.read_text(encoding="utf-8")
            self.assertIn("\\label{tab:simulation-summary}", tex)
            self.assertNotIn("\\label{tab:simulation-scenarios}", tex)
            self.assertIn("\\SimulationTrialCount", tex)
            self.assertIn("Large long-lived naive", tex)
            self.assertIn("Mean escape step", tex)
            self.assertIn("Mean final cancer fraction", tex)


if __name__ == "__main__":
    unittest.main()
