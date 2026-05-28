from __future__ import annotations

import random
from dataclasses import dataclass, replace


HEALTHY = "healthy"
MUTATED = "mutated"
PRECANCER = "precancer"
CANCER = "cancer"


@dataclass
class Cell:
    state: str = HEALTHY
    mutation_count: int = 0
    age: int = 0


@dataclass(frozen=True)
class SimulationParameters:
    initial_cells: int = 80
    max_cells: int = 240
    lifespan_steps: int = 300
    division_rate: float = 0.08
    mutation_rate: float = 0.04
    repair_rate: float = 0.03
    apoptosis_rate: float = 0.01
    required_mutations: int = 4
    cancer_division_rate: float = 0.16
    immune_strength: float = 18.0
    immune_kill_rate: float = 0.04
    immune_aging_rate: float = 0.01
    immune_depletion_rate: float = 0.002
    seed: int | None = None


@dataclass(frozen=True)
class SimulationSnapshot:
    step: int
    healthy_cells: int
    mutated_cells: int
    precancer_cells: int
    cancer_cells: int
    dead_removed_cells: int
    total_cells: int
    immune_strength: float
    immune_escape: bool
    escape_time: int | None

    @property
    def relative_escape_fraction(self) -> float:
        if self.escape_time is None:
            return 0.0
        if self.step <= 0:
            return 1.0
        return max(0.0, 1.0 - self.escape_time / self.step)


class CellSimulation:
    def __init__(self, parameters: SimulationParameters | None = None) -> None:
        self.parameters = parameters or SimulationParameters()
        self._validate_parameters(self.parameters)
        self.rng = random.Random(self.parameters.seed)
        self.cells: list[Cell] = []
        self.step_number = 0
        self.dead_removed_cells = 0
        self.current_immune_strength = self.parameters.immune_strength
        self.immune_escape = False
        self.escape_time: int | None = None
        self.history: list[SimulationSnapshot] = []
        self.reset()

    def reset(self) -> None:
        self.rng = random.Random(self.parameters.seed)
        self.cells = [Cell() for _ in range(self.parameters.initial_cells)]
        self.step_number = 0
        self.dead_removed_cells = 0
        self.current_immune_strength = self.parameters.immune_strength
        self.immune_escape = False
        self.escape_time = None
        self.history = [self.snapshot()]

    def step(self) -> SimulationSnapshot:
        if self.step_number >= self.parameters.lifespan_steps:
            return self.snapshot()

        self.step_number += 1
        new_cells: list[Cell] = []
        survivors: list[Cell] = []

        for cell in self.cells:
            cell.age += 1
            if cell.state != CANCER:
                self._repair_cell(cell)
                if self._apoptosis_removes(cell):
                    self.dead_removed_cells += 1
                    continue

            survivors.append(cell)
            daughter = self._maybe_divide(
                cell,
                can_add_cell=len(self.cells) + len(new_cells) < self.parameters.max_cells,
            )
            if daughter is not None:
                new_cells.append(daughter)

        self.cells = survivors + new_cells
        self._apply_immune_control()
        self._age_immune_control()
        self._update_escape_status()

        snapshot = self.snapshot()
        self.history.append(snapshot)
        return snapshot

    def snapshot(self) -> SimulationSnapshot:
        healthy = sum(1 for cell in self.cells if cell.state == HEALTHY)
        mutated = sum(1 for cell in self.cells if cell.state == MUTATED)
        precancer = sum(1 for cell in self.cells if cell.state == PRECANCER)
        cancer = sum(1 for cell in self.cells if cell.state == CANCER)
        return SimulationSnapshot(
            step=self.step_number,
            healthy_cells=healthy,
            mutated_cells=mutated,
            precancer_cells=precancer,
            cancer_cells=cancer,
            dead_removed_cells=self.dead_removed_cells,
            total_cells=len(self.cells),
            immune_strength=self.current_immune_strength,
            immune_escape=self.immune_escape,
            escape_time=self.escape_time,
        )

    def run_until_end(self) -> list[SimulationSnapshot]:
        while self.step_number < self.parameters.lifespan_steps:
            self.step()
        return self.history

    @classmethod
    def run_trials(
        cls,
        parameters: SimulationParameters,
        n_trials: int,
        seed: int | None = None,
    ) -> dict[str, float | int | None]:
        if n_trials <= 0:
            raise ValueError("n_trials must be positive")

        trial_seed_rng = random.Random(seed if seed is not None else parameters.seed)
        final_snapshots: list[SimulationSnapshot] = []
        for _ in range(n_trials):
            trial_parameters = replace(parameters, seed=trial_seed_rng.randrange(2**32))
            simulation = cls(trial_parameters)
            final_snapshots.append(simulation.run_until_end()[-1])

        escaped = [snapshot for snapshot in final_snapshots if snapshot.immune_escape]
        escape_times = [snapshot.escape_time for snapshot in escaped if snapshot.escape_time is not None]
        return {
            "n_trials": n_trials,
            "escape_probability": len(escaped) / n_trials,
            "mean_escape_time": _mean(escape_times),
            "mean_final_cancer_cells": _mean([snapshot.cancer_cells for snapshot in final_snapshots]),
            "mean_final_total_cells": _mean([snapshot.total_cells for snapshot in final_snapshots]),
            "mean_final_cancer_fraction": _mean([
                snapshot.cancer_cells / max(1, snapshot.total_cells)
                for snapshot in final_snapshots
            ]),
        }

    def _maybe_divide(self, cell: Cell, can_add_cell: bool) -> Cell | None:
        rate = self.parameters.cancer_division_rate if cell.state == CANCER else self.parameters.division_rate
        if self.rng.random() >= rate:
            return None

        if cell.state != CANCER and self.rng.random() < self.parameters.mutation_rate:
            cell.mutation_count += 1
            self._classify_cell(cell)

        if not can_add_cell:
            return None

        daughter = Cell(state=cell.state, mutation_count=cell.mutation_count)
        return daughter

    def _repair_cell(self, cell: Cell) -> None:
        if cell.mutation_count > 0 and self.rng.random() < self.parameters.repair_rate:
            cell.mutation_count -= 1
            self._classify_cell(cell)

    def _apoptosis_removes(self, cell: Cell) -> bool:
        if cell.mutation_count <= 0:
            return False
        damage_fraction = cell.mutation_count / max(1, self.parameters.required_mutations)
        removal_rate = min(1.0, self.parameters.apoptosis_rate * (1.0 + damage_fraction))
        return self.rng.random() < removal_rate

    def _classify_cell(self, cell: Cell) -> None:
        if cell.mutation_count >= self.parameters.required_mutations:
            cell.state = CANCER
        elif cell.mutation_count >= max(1, self.parameters.required_mutations - 1):
            cell.state = PRECANCER
        elif cell.mutation_count > 0:
            cell.state = MUTATED
        else:
            cell.state = HEALTHY

    def _apply_immune_control(self) -> None:
        if self.current_immune_strength <= 0:
            return

        survivors: list[Cell] = []
        cancer_count = sum(1 for cell in self.cells if cell.state == CANCER)
        kill_rate = min(
            1.0,
            self.parameters.immune_kill_rate
            * self.current_immune_strength
            / max(1.0, float(cancer_count)),
        )
        for cell in self.cells:
            if cell.state == CANCER and self.rng.random() < kill_rate:
                self.dead_removed_cells += 1
                continue
            survivors.append(cell)
        self.cells = survivors

    def _age_immune_control(self) -> None:
        cancer_count = sum(1 for cell in self.cells if cell.state == CANCER)
        decline = self.parameters.immune_aging_rate + self.parameters.immune_depletion_rate * cancer_count
        self.current_immune_strength = max(0.0, self.current_immune_strength - decline)

    def _update_escape_status(self) -> None:
        if self.immune_escape:
            return
        cancer_count = sum(1 for cell in self.cells if cell.state == CANCER)
        if cancer_count > self.current_immune_strength:
            self.immune_escape = True
            self.escape_time = self.step_number

    @staticmethod
    def _validate_parameters(parameters: SimulationParameters) -> None:
        if parameters.initial_cells <= 0:
            raise ValueError("initial_cells must be positive")
        if parameters.max_cells < parameters.initial_cells:
            raise ValueError("max_cells must be at least initial_cells")
        if parameters.lifespan_steps <= 0:
            raise ValueError("lifespan_steps must be positive")
        if parameters.required_mutations <= 0:
            raise ValueError("required_mutations must be positive")
        for field_name in (
            "division_rate",
            "mutation_rate",
            "repair_rate",
            "apoptosis_rate",
            "cancer_division_rate",
            "immune_kill_rate",
        ):
            value = getattr(parameters, field_name)
            if value < 0.0 or value > 1.0:
                raise ValueError(f"{field_name} must be between 0 and 1")
        for field_name in ("immune_strength", "immune_aging_rate", "immune_depletion_rate"):
            value = getattr(parameters, field_name)
            if value < 0.0:
                raise ValueError(f"{field_name} must be non-negative")


def scenario_presets() -> dict[str, SimulationParameters]:
    return {
        "small_short_lived": SimulationParameters(
            initial_cells=50,
            max_cells=140,
            lifespan_steps=180,
            division_rate=0.07,
            mutation_rate=0.035,
            required_mutations=4,
            immune_strength=16.0,
        ),
        "large_long_lived_naive": SimulationParameters(
            initial_cells=140,
            max_cells=520,
            lifespan_steps=520,
            division_rate=0.09,
            mutation_rate=0.07,
            required_mutations=4,
            immune_strength=8.0,
            immune_kill_rate=0.02,
            immune_aging_rate=0.02,
        ),
        "large_slower_division": SimulationParameters(
            initial_cells=140,
            max_cells=520,
            lifespan_steps=520,
            division_rate=0.045,
            mutation_rate=0.07,
            required_mutations=4,
            immune_strength=8.0,
            immune_kill_rate=0.02,
            immune_aging_rate=0.02,
        ),
        "large_better_repair": SimulationParameters(
            initial_cells=140,
            max_cells=520,
            lifespan_steps=520,
            division_rate=0.09,
            mutation_rate=0.07,
            repair_rate=0.12,
            required_mutations=4,
            immune_strength=8.0,
            immune_kill_rate=0.02,
            immune_aging_rate=0.02,
        ),
        "large_extra_required_hits": SimulationParameters(
            initial_cells=140,
            max_cells=520,
            lifespan_steps=520,
            division_rate=0.09,
            mutation_rate=0.07,
            required_mutations=6,
            immune_strength=8.0,
            immune_kill_rate=0.02,
            immune_aging_rate=0.02,
        ),
        "large_stronger_immune_control": SimulationParameters(
            initial_cells=140,
            max_cells=520,
            lifespan_steps=520,
            division_rate=0.09,
            mutation_rate=0.07,
            required_mutations=4,
            immune_strength=40.0,
            immune_kill_rate=0.08,
            immune_aging_rate=0.006,
        ),
    }


def _mean(values: list[int | float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)
