from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"
FIGURES_DIR = ROOT / "figures"
TEX_DIR = ROOT / "doc" / "tex"
TEX_FIGURES_DIR = TEX_DIR / "figures"
GENERATED_TEX = TEX_DIR / "contents" / "generated-results.tex"

VINCZE_CSV = DATA_DIR / "VinczeEtal2021_Data.csv"


@dataclass(frozen=True)
class SpeciesRecord:
    species: str
    order: str
    body_mass_kg: float
    adult_life_expectancy_days: float
    cmr: float
    icm: float
    n_individuals: int
    n_dead: int
    n_neoplasia: int
    n_postmortem: int

    @property
    def adult_life_expectancy_years(self) -> float:
        return self.adult_life_expectancy_days / 365.25

    @property
    def exposure_proxy(self) -> float:
        return self.body_mass_kg * self.adult_life_expectancy_years


def _float(value: str) -> float | None:
    value = value.strip()
    if not value:
        return None
    return float(value)


def _int(value: str) -> int:
    value = value.strip()
    return int(float(value)) if value else 0


def load_vincze_records(path: Path = VINCZE_CSV) -> list[SpeciesRecord]:
    records: list[SpeciesRecord] = []
    with path.open(newline="", encoding="cp1252") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            mass = _float(row["Species body mass (kg)"])
            life = _float(row["Adult life expectancy"])
            cmr = _float(row["CMR"])
            icm = _float(row["ICM"])
            if mass is None or life is None or cmr is None or icm is None:
                continue
            if mass <= 0 or life <= 0:
                continue
            records.append(
                SpeciesRecord(
                    species=row["Species"].replace("_", " "),
                    order=row["Order"],
                    body_mass_kg=mass,
                    adult_life_expectancy_days=life,
                    cmr=cmr,
                    icm=icm,
                    n_individuals=_int(row["No.individuals"]),
                    n_dead=_int(row["No.dead individuals"]),
                    n_neoplasia=_int(row["No. neoplasia cases"]),
                    n_postmortem=_int(row["No. individuals with available postmortem pathological records"]),
                )
            )
    return records


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
