from __future__ import annotations

import math

from src.data import FIGURES_DIR, GENERATED_TEX, RESULTS_DIR, TEX_FIGURES_DIR, write_csv
from src.statistics import median


def _read_csv(path):
    import csv
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _scale(value: float, lo: float, hi: float, size: float) -> float:
    if hi == lo:
        return 0
    return (value - lo) / (hi - lo) * size


def _scatter_tex(rows: list[dict[str, str]]) -> str:
    xs = [math.log10(float(r["body_mass_kg"])) for r in rows if float(r["cmr"]) > 0]
    ys = [100 * float(r["cmr"]) for r in rows if float(r["cmr"]) > 0]
    lx, hx = min(xs), max(xs)
    ly, hy = 0, max(ys)
    lines = [
        "\\begin{tikzpicture}[x=1cm,y=1cm]",
        "\\draw[->] (0,0) -- (7.2,0);",
        "\\draw[->] (0,0) -- (0,4.2);",
        "\\node[font=\\scriptsize] at (3.5,-0.55) {$\\log_{10}$ massa tubuh (kg)};",
        "\\node[font=\\scriptsize,rotate=90] at (-0.7,2) {CMR (\\%)};",
    ]
    for row in rows:
        cmr = float(row["cmr"])
        if cmr <= 0:
            continue
        x = _scale(math.log10(float(row["body_mass_kg"])), lx, hx, 6.8)
        y = _scale(100 * cmr, ly, hy, 3.8)
        size = 0.035 + min(math.log10(float(row["n_postmortem"]) + 1) / 80, 0.035)
        lines.append(f"\\fill[teal!70] ({x+0.2:.3f},{y+0.15:.3f}) circle ({size:.3f});")
    lines.append("\\end{tikzpicture}")
    return "\n".join(lines)


def _residual_bar_tex(rows: list[dict[str, str]]) -> str:
    top = rows[:8]
    values = [100 * float(r["suppression_index"]) for r in top]
    labels = [r["species"].split()[0] for r in top]
    max_v = 100
    lines = [
        "\\begin{tikzpicture}[x=1cm,y=1cm]",
        "\\draw[->] (0,0) -- (7.2,0);",
        "\\draw[->] (0,0) -- (0,4.2);",
        "\\node[font=\\scriptsize] at (3.5,-0.65) {Spesies};",
        "\\node[font=\\scriptsize,rotate=90] at (-0.7,2) {Indeks supresi (\\%)};",
    ]
    step = 6.8 / len(values)
    for i, value in enumerate(values):
        x = 0.25 + i * step
        y = 3.8 * value / max_v
        lines.append(f"\\fill[orange!75] ({x:.3f},0) rectangle ({x+step*0.55:.3f},{y:.3f});")
        lines.append(f"\\node[font=\\tiny,rotate=35,anchor=east] at ({x+step*0.28:.3f},-0.12) {{{labels[i]}}};")
    lines.append("\\end{tikzpicture}")
    return "\n".join(lines)


def _order_bar_tex(rows: list[dict[str, str]]) -> str:
    top = rows[:8]
    values = [100 * float(r["median_cmr"]) for r in top]
    labels = [r["order"] for r in top]
    max_v = max(values) if values else 1
    lines = [
        "\\begin{tikzpicture}[x=1cm,y=1cm]",
        "\\draw[->] (0,0) -- (7.2,0);",
        "\\draw[->] (0,0) -- (0,4.2);",
        "\\node[font=\\scriptsize] at (3.5,-0.65) {Ordo};",
        "\\node[font=\\scriptsize,rotate=90] at (-0.7,2) {Median CMR (\\%)};",
    ]
    step = 6.8 / len(values)
    for i, value in enumerate(values):
        x = 0.25 + i * step
        y = 3.8 * value / max_v
        lines.append(f"\\fill[teal!70] ({x:.3f},0) rectangle ({x+step*0.55:.3f},{y:.3f});")
        lines.append(f"\\node[font=\\tiny,rotate=35,anchor=east] at ({x+step*0.28:.3f},-0.12) {{{labels[i]}}};")
    lines.append("\\end{tikzpicture}")
    return "\n".join(lines)


def _exposure_scatter_tex(rows: list[dict[str, str]]) -> str:
    valid = [r for r in rows if float(r["cmr"]) > 0]
    xs = [math.log10(float(r["exposure_proxy"])) for r in valid]
    ys = [math.log10(float(r["cmr"])) for r in valid]
    lx, hx = min(xs), max(xs)
    ly, hy = min(ys), max(ys)
    lines = [
        "\\begin{tikzpicture}[x=1cm,y=1cm]",
        "\\draw[->] (0,0) -- (7.2,0);",
        "\\draw[->] (0,0) -- (0,4.2);",
        "\\node[font=\\scriptsize] at (3.5,-0.55) {$\\log_{10}$ exposure proxy};",
        "\\node[font=\\scriptsize,rotate=90] at (-0.7,2) {$\\log_{10}$ CMR};",
    ]
    for row in valid:
        x = _scale(math.log10(float(row["exposure_proxy"])), lx, hx, 6.8)
        y = _scale(math.log10(float(row["cmr"])), ly, hy, 3.8)
        color = "orange!70" if float(row["suppression_index"]) > 0.75 else "teal!65"
        lines.append(f"\\fill[{color}] ({x+0.2:.3f},{y+0.15:.3f}) circle (0.035);")
    lines.append("\\end{tikzpicture}")
    return "\n".join(lines)


def _threshold_line_tex(rows: list[dict[str, str]]) -> str:
    thresholds = [float(r["postmortem_threshold"]) for r in rows]
    slopes = [float(r["slope_log_mass_log_cmr"]) for r in rows]
    lx, hx = min(thresholds), max(thresholds)
    ly, hy = min(slopes) - 0.02, max(slopes) + 0.02
    lines = [
        "\\begin{tikzpicture}[x=1cm,y=1cm]",
        "\\draw[->] (0,0) -- (7.2,0);",
        "\\draw[->] (0,0) -- (0,4.2);",
        "\\node[font=\\scriptsize] at (3.5,-0.55) {Minimum catatan postmortem};",
        "\\node[font=\\scriptsize,rotate=90] at (-0.7,2) {Slope log massa vs log CMR};",
    ]
    points = []
    for row in rows:
        x = _scale(float(row["postmortem_threshold"]), lx, hx, 6.8) + 0.2
        y = _scale(float(row["slope_log_mass_log_cmr"]), ly, hy, 3.8) + 0.15
        points.append((x, y))
        lines.append(f"\\fill[teal!70] ({x:.3f},{y:.3f}) circle (0.055);")
        lines.append(f"\\node[font=\\tiny] at ({x:.3f},-0.15) {{{int(float(row['postmortem_threshold']))}}};")
        lines.append(f"\\node[font=\\tiny,anchor=west] at ({x+0.08:.3f},{y:.3f}) {{$n={int(float(row['n_species']))}$}};")
    for (x1, y1), (x2, y2) in zip(points, points[1:]):
        lines.append(f"\\draw[teal!70,thick] ({x1:.3f},{y1:.3f}) -- ({x2:.3f},{y2:.3f});")
    lines.append("\\end{tikzpicture}")
    return "\n".join(lines)


def write_figures_and_tables() -> None:
    TEX_FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(exist_ok=True)
    species = _read_csv(RESULTS_DIR / "species_cancer_risk.csv")
    summary = _read_csv(RESULTS_DIR / "analysis_summary.csv")
    top = _read_csv(RESULTS_DIR / "top_suppression_residuals.csv")
    orders = _read_csv(RESULTS_DIR / "order_summary.csv")
    bootstrap = _read_csv(RESULTS_DIR / "bootstrap_slopes.csv")
    thresholds = _read_csv(RESULTS_DIR / "postmortem_thresholds.csv")

    (TEX_FIGURES_DIR / "F1_mass_cmr.tex").write_text(_scatter_tex(species), encoding="utf-8")
    (TEX_FIGURES_DIR / "F2_suppression_residuals.tex").write_text(_residual_bar_tex(top), encoding="utf-8")
    (TEX_FIGURES_DIR / "F3_order_summary.tex").write_text(_order_bar_tex(orders), encoding="utf-8")
    (TEX_FIGURES_DIR / "F4_exposure_cmr.tex").write_text(_exposure_scatter_tex(species), encoding="utf-8")
    (TEX_FIGURES_DIR / "F5_threshold_slope.tex").write_text(_threshold_line_tex(thresholds), encoding="utf-8")

    metrics = {r["metric"]: float(r["value"]) for r in summary}
    lines = [
        "% Generated by python main.py",
        "\\begin{table}[t]",
        "\\centering",
        "\\caption{Ringkasan dataset Vincze et al. setelah filtering nilai kosong.}",
        "\\label{tab:data-summary}",
        "\\begin{tabular}{lr}",
        "\\toprule",
        "Besaran & Nilai\\\\",
        "\\midrule",
        f"Jumlah spesies & {int(metrics['n_species'])}\\\\",
        f"Spesies dengan CMR $>$ 0 & {int(metrics['n_species_nonzero_cmr'])}\\\\",
        f"Median CMR & {100*metrics['median_cmr']:.2f}\\%\\\\",
        f"Median massa tubuh & {metrics['median_body_mass_kg']:.2f} kg\\\\",
        f"Median adult life expectancy & {metrics['median_life_expectancy_years']:.2f} tahun\\\\",
        "\\bottomrule",
        "\\end{tabular}",
        "\\end{table}",
        "",
        "\\begin{table}[t]",
        "\\centering",
        "\\caption{Bootstrap 95\\% CI untuk slope regresi log CMR.}",
        "\\label{tab:bootstrap-slopes}",
        "\\begin{tabular}{lrrr}",
        "\\toprule",
        "Prediktor & Mean slope & CI bawah & CI atas\\\\",
        "\\midrule",
    ]
    for row in bootstrap:
        predictor = row["predictor"].replace("_", " ")
        lines.append(
            f"{predictor} & {float(row['slope_mean']):.3f} & "
            f"{float(row['ci_2_5']):.3f} & {float(row['ci_97_5']):.3f}\\\\"
        )
    lines += [
        "\\bottomrule",
        "\\end{tabular}",
        "\\end{table}",
        "",
        "\\begin{table}[t]",
        "\\centering",
        "\\caption{Robustness slope massa tubuh setelah filtering jumlah catatan postmortem.}",
        "\\label{tab:postmortem-thresholds}",
        "\\begin{tabular}{rrrr}",
        "\\toprule",
        "Min. postmortem & Spesies & Slope & $R^2$\\\\",
        "\\midrule",
    ]
    for row in thresholds:
        lines.append(
            f"{int(float(row['postmortem_threshold']))} & {int(float(row['n_species']))} & "
            f"{float(row['slope_log_mass_log_cmr']):.3f} & {float(row['r2_log_mass_log_cmr']):.3f}\\\\"
        )
    lines += [
        "\\bottomrule",
        "\\end{tabular}",
        "\\end{table}",
        "",
        "\\begin{table}[t]",
        "\\centering",
        "\\caption{Enam spesies dengan residual supresi tertinggi.}",
        "\\label{tab:top-residuals}",
        "\\begin{tabular}{lrr}",
        "\\toprule",
        "Spesies & CMR (\\%) & Risiko naif (\\%)\\\\",
        "\\midrule",
    ]
    for row in top[:6]:
        species = " ".join(row["species"].split()[:2]).replace("_", " ")
        lines.append(f"{species} & {100*float(row['cmr']):.2f} & {100*float(row['naive_risk']):.2f}\\\\")
    lines += [
        "\\bottomrule",
        "\\end{tabular}",
        "\\end{table}",
        "",
        "\\begin{table}[t]",
        "\\centering",
        "\\caption{Hubungan log CMR dengan prediktor skala tubuh dan umur.}",
        "\\label{tab:regression-summary}",
        "\\begin{tabular}{lrr}",
        "\\toprule",
        "Prediktor & Slope & $R^2$\\\\",
        "\\midrule",
        f"$\\log_{{10}}$ massa tubuh & {metrics['slope_log_mass_log_cmr']:.3f} & {metrics['r2_log_mass_log_cmr']:.3f}\\\\",
        f"$\\log_{{10}}$ life expectancy & {metrics['slope_log_life_log_cmr']:.3f} & {metrics['r2_log_life_log_cmr']:.3f}\\\\",
        f"$\\log_{{10}}$ exposure proxy & {metrics['slope_log_exposure_log_cmr']:.3f} & {metrics['r2_log_exposure_log_cmr']:.3f}\\\\",
        "\\bottomrule",
        "\\end{tabular}",
        "\\end{table}",
        "",
        f"\\newcommand{{\\SpeciesCount}}{{{int(metrics['n_species'])}}}",
        f"\\newcommand{{\\NonzeroSpeciesCount}}{{{int(metrics['n_species_nonzero_cmr'])}}}",
        f"\\newcommand{{\\MassSlope}}{{{metrics['slope_log_mass_log_cmr']:.3f}}}",
        f"\\newcommand{{\\MassRsq}}{{{metrics['r2_log_mass_log_cmr']:.3f}}}",
        f"\\newcommand{{\\ExposureSlope}}{{{metrics['slope_log_exposure_log_cmr']:.3f}}}",
        f"\\newcommand{{\\ExposureRsq}}{{{metrics['r2_log_exposure_log_cmr']:.3f}}}",
    ]
    GENERATED_TEX.write_text("\n".join(lines), encoding="utf-8")
