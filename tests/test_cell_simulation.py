from __future__ import annotations

import unittest

from src.cell_simulation import CellSimulation, SimulationParameters, scenario_presets


class CellSimulationTests(unittest.TestCase):
    def test_simulation_respects_capacity_and_lifespan(self) -> None:
        parameters = SimulationParameters(
            initial_cells=30,
            max_cells=80,
            lifespan_steps=60,
            division_rate=0.2,
            mutation_rate=0.08,
            seed=12,
        )
        simulation = CellSimulation(parameters)
        history = simulation.run_until_end()

        self.assertEqual(history[-1].step, parameters.lifespan_steps)
        self.assertLessEqual(history[-1].total_cells, parameters.max_cells)
        self.assertEqual(len(history), parameters.lifespan_steps + 1)

    def test_seeded_runs_are_deterministic(self) -> None:
        parameters = SimulationParameters(seed=42, lifespan_steps=80)

        first = CellSimulation(parameters).run_until_end()[-1]
        second = CellSimulation(parameters).run_until_end()[-1]

        self.assertEqual(first, second)

    def test_all_presets_run_to_completion(self) -> None:
        for name, parameters in scenario_presets().items():
            with self.subTest(name=name):
                final = CellSimulation(parameters).run_until_end()[-1]

                self.assertEqual(final.step, parameters.lifespan_steps)
                self.assertLessEqual(final.total_cells, parameters.max_cells)
                self.assertGreaterEqual(final.immune_strength, 0.0)

    def test_run_trials_returns_valid_summary(self) -> None:
        summary = CellSimulation.run_trials(
            scenario_presets()["small_short_lived"],
            n_trials=5,
            seed=7,
        )

        self.assertEqual(summary["n_trials"], 5)
        self.assertGreaterEqual(summary["escape_probability"], 0.0)
        self.assertLessEqual(summary["escape_probability"], 1.0)
        self.assertIsNotNone(summary["mean_final_cancer_cells"])
        self.assertIsNotNone(summary["mean_final_total_cells"])

    def test_naive_large_scenario_has_more_escape_than_protective_presets(self) -> None:
        presets = scenario_presets()
        naive = CellSimulation.run_trials(
            presets["large_long_lived_naive"],
            n_trials=30,
            seed=21,
        )
        protective_names = (
            "large_slower_division",
            "large_better_repair",
            "large_extra_required_hits",
            "large_stronger_immune_control",
        )

        for name in protective_names:
            with self.subTest(name=name):
                protective = CellSimulation.run_trials(presets[name], n_trials=30, seed=21)
                self.assertGreaterEqual(
                    naive["escape_probability"],
                    protective["escape_probability"],
                )

    def test_parameter_changes_follow_expected_direction(self) -> None:
        baseline = SimulationParameters(
            initial_cells=120,
            max_cells=500,
            lifespan_steps=350,
            division_rate=0.09,
            mutation_rate=0.06,
            repair_rate=0.02,
            required_mutations=4,
            immune_strength=8.0,
            immune_kill_rate=0.02,
            immune_aging_rate=0.02,
        )
        lower_mutation = SimulationParameters(
            initial_cells=120,
            max_cells=500,
            lifespan_steps=350,
            division_rate=0.09,
            mutation_rate=0.02,
            repair_rate=0.02,
            required_mutations=4,
            immune_strength=8.0,
            immune_kill_rate=0.02,
            immune_aging_rate=0.02,
        )
        more_required_hits = SimulationParameters(
            initial_cells=120,
            max_cells=500,
            lifespan_steps=350,
            division_rate=0.09,
            mutation_rate=0.06,
            repair_rate=0.02,
            required_mutations=6,
            immune_strength=8.0,
            immune_kill_rate=0.02,
            immune_aging_rate=0.02,
        )

        baseline_summary = CellSimulation.run_trials(baseline, n_trials=40, seed=31)
        lower_mutation_summary = CellSimulation.run_trials(lower_mutation, n_trials=40, seed=31)
        more_hits_summary = CellSimulation.run_trials(more_required_hits, n_trials=40, seed=31)

        self.assertGreaterEqual(
            baseline_summary["escape_probability"],
            lower_mutation_summary["escape_probability"],
        )
        self.assertGreaterEqual(
            baseline_summary["escape_probability"],
            more_hits_summary["escape_probability"],
        )


if __name__ == "__main__":
    unittest.main()
