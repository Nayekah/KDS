from __future__ import annotations

from src.comparative import run_comparative_analysis
from src.figures import write_figures_and_tables
from src.simulation_exports import write_simulation_artifacts


def main() -> None:
    results = run_comparative_analysis()
    simulation_rows = write_simulation_artifacts()
    write_figures_and_tables()
    summary = {row["metric"]: row["value"] for row in results["summary"]}
    print(f"Analyzed {summary['n_species']} mammal species")
    print(f"log10(body mass) slope vs log10(CMR): {summary['slope_log_mass_log_cmr']:.3f}")
    print(f"exposure proxy slope vs log10(CMR): {summary['slope_log_exposure_log_cmr']:.3f}")
    print(f"Generated simulation summary for {len(simulation_rows)} scenarios")
