from __future__ import annotations

import math
import random

from src.data import RESULTS_DIR, SpeciesRecord, load_vincze_records, write_csv
from src.statistics import clamp_probability, median, pearson, simple_regression, spearman


def calibrated_lambda(records: list[SpeciesRecord]) -> float:
    exposure = [r.exposure_proxy for r in records if r.cmr > 0]
    observed = [r.cmr for r in records if r.cmr > 0]
    return -math.log(1 - median(observed)) / median(exposure)


def naive_risk(exposure: float, lam: float) -> float:
    return 1 - math.exp(-lam * exposure)


def suppression_index(observed: float, exposure: float, lam: float) -> float:
    if observed <= 0:
        return 1.0
    observed_hazard = -math.log(1 - clamp_probability(observed))
    naive_hazard = lam * exposure
    if naive_hazard <= 0:
        return 0.0
    return 1 - observed_hazard / naive_hazard


def species_rows(records: list[SpeciesRecord]) -> list[dict[str, object]]:
    lam = calibrated_lambda(records)
    rows: list[dict[str, object]] = []
    for r in records:
        expected = naive_risk(r.exposure_proxy, lam)
        rows.append({
            "species": r.species,
            "order": r.order,
            "body_mass_kg": r.body_mass_kg,
            "adult_life_expectancy_years": r.adult_life_expectancy_years,
            "exposure_proxy": r.exposure_proxy,
            "cmr": r.cmr,
            "icm": r.icm,
            "naive_risk": expected,
            "suppression_index": suppression_index(r.cmr, r.exposure_proxy, lam),
            "n_postmortem": r.n_postmortem,
            "n_neoplasia": r.n_neoplasia,
        })
    return rows


def summary_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    nonzero = [r for r in rows if float(r["cmr"]) > 0]
    x_mass = [math.log10(float(r["body_mass_kg"])) for r in nonzero]
    x_life = [math.log10(float(r["adult_life_expectancy_years"])) for r in nonzero]
    x_exposure = [math.log10(float(r["exposure_proxy"])) for r in nonzero]
    y = [math.log10(float(r["cmr"])) for r in nonzero]

    _, slope_mass, r2_mass = simple_regression(x_mass, y)
    _, slope_life, r2_life = simple_regression(x_life, y)
    _, slope_exp, r2_exp = simple_regression(x_exposure, y)

    return [
        {"metric": "n_species", "value": len(rows)},
        {"metric": "n_species_nonzero_cmr", "value": len(nonzero)},
        {"metric": "median_cmr", "value": median([float(r["cmr"]) for r in rows])},
        {"metric": "median_body_mass_kg", "value": median([float(r["body_mass_kg"]) for r in rows])},
        {"metric": "median_life_expectancy_years", "value": median([float(r["adult_life_expectancy_years"]) for r in rows])},
        {"metric": "pearson_log_mass_log_cmr", "value": pearson(x_mass, y)},
        {"metric": "spearman_mass_cmr", "value": spearman([float(r["body_mass_kg"]) for r in nonzero], [float(r["cmr"]) for r in nonzero])},
        {"metric": "slope_log_mass_log_cmr", "value": slope_mass},
        {"metric": "r2_log_mass_log_cmr", "value": r2_mass},
        {"metric": "slope_log_life_log_cmr", "value": slope_life},
        {"metric": "r2_log_life_log_cmr", "value": r2_life},
        {"metric": "slope_log_exposure_log_cmr", "value": slope_exp},
        {"metric": "r2_log_exposure_log_cmr", "value": r2_exp},
    ]


def top_residual_rows(rows: list[dict[str, object]], n: int = 12) -> list[dict[str, object]]:
    ranked = sorted(rows, key=lambda r: float(r["suppression_index"]), reverse=True)
    return ranked[:n]


def order_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        grouped.setdefault(str(row["order"]), []).append(row)
    out = []
    for order, group in grouped.items():
        if len(group) < 3:
            continue
        out.append({
            "order": order,
            "n_species": len(group),
            "median_cmr": median([float(r["cmr"]) for r in group]),
            "median_body_mass_kg": median([float(r["body_mass_kg"]) for r in group]),
            "median_life_expectancy_years": median([float(r["adult_life_expectancy_years"]) for r in group]),
        })
    return sorted(out, key=lambda r: float(r["median_cmr"]), reverse=True)


def bootstrap_slope_rows(rows: list[dict[str, object]], n_bootstrap: int = 1000) -> list[dict[str, object]]:
    nonzero = [r for r in rows if float(r["cmr"]) > 0]
    predictors = {
        "body_mass": lambda r: math.log10(float(r["body_mass_kg"])),
        "adult_life_expectancy": lambda r: math.log10(float(r["adult_life_expectancy_years"])),
        "exposure_proxy": lambda r: math.log10(float(r["exposure_proxy"])),
    }
    rng = random.Random(13523090)
    out = []
    for name, fn in predictors.items():
        slopes = []
        for _ in range(n_bootstrap):
            sample = [nonzero[rng.randrange(len(nonzero))] for _ in range(len(nonzero))]
            x = [fn(r) for r in sample]
            y = [math.log10(float(r["cmr"])) for r in sample]
            _, slope, _ = simple_regression(x, y)
            slopes.append(slope)
        slopes.sort()
        out.append({
            "predictor": name,
            "slope_mean": sum(slopes) / len(slopes),
            "ci_2_5": slopes[int(0.025 * len(slopes))],
            "ci_97_5": slopes[int(0.975 * len(slopes))],
        })
    return out


def postmortem_threshold_rows(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    out = []
    for threshold in [0, 20, 50, 100]:
        subset = [
            r for r in rows
            if int(float(r["n_postmortem"])) >= threshold and float(r["cmr"]) > 0
        ]
        if len(subset) < 10:
            continue
        x = [math.log10(float(r["body_mass_kg"])) for r in subset]
        y = [math.log10(float(r["cmr"])) for r in subset]
        _, slope, r2 = simple_regression(x, y)
        out.append({
            "postmortem_threshold": threshold,
            "n_species": len(subset),
            "slope_log_mass_log_cmr": slope,
            "r2_log_mass_log_cmr": r2,
            "median_cmr": median([float(r["cmr"]) for r in subset]),
        })
    return out


def run_comparative_analysis() -> dict[str, list[dict[str, object]]]:
    records = load_vincze_records()
    rows = species_rows(records)
    summary = summary_rows(rows)
    top = top_residual_rows(rows)
    orders = order_rows(rows)
    bootstrap = bootstrap_slope_rows(rows)
    thresholds = postmortem_threshold_rows(rows)

    RESULTS_DIR.mkdir(exist_ok=True)
    write_csv(RESULTS_DIR / "species_cancer_risk.csv", rows)
    write_csv(RESULTS_DIR / "analysis_summary.csv", summary)
    write_csv(RESULTS_DIR / "top_suppression_residuals.csv", top)
    write_csv(RESULTS_DIR / "order_summary.csv", orders)
    write_csv(RESULTS_DIR / "bootstrap_slopes.csv", bootstrap)
    write_csv(RESULTS_DIR / "postmortem_thresholds.csv", thresholds)
    return {
        "species": rows,
        "summary": summary,
        "top": top,
        "orders": orders,
        "bootstrap": bootstrap,
        "thresholds": thresholds,
    }
