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


def _simulation_flow_tex() -> str:
    return r"""\begin{figure}[t]
\centering
\resizebox{0.92\columnwidth}{!}{%
\begin{tikzpicture}[
    box/.style={rectangle, rounded corners=2pt, minimum width=1.5cm, minimum height=0.6cm, font=\footnotesize\bfseries, text centered, text=white},
    every edge/.style={draw, ->, >=stealth, font=\tiny},
    node distance=1.5cm and 1.0cm,
]
\node[box, fill=green!55!black] (H) {Sehat};
\node[box, fill=orange!75!black, right=of H] (M) {Termutasi};
\node[box, fill=orange!90!black, right=of M] (P) {Prakanker};
\node[box, fill=red!70!black, right=of P] (C) {Kanker};
\node[box, fill=blue!55!black, right=of C] (E) {Escape};
\node[box, fill=gray!50!black, below=of M] (D1) {Mati};
\node[box, fill=gray!50!black, below=of C] (D2) {Mati};

\draw (H) edge node[above] {div+mut} (M);
\draw (M) edge node[above] {mutasi} (P);
\draw (P) edge node[above] {mutasi} (C);
\draw (C) edge node[above, align=center] {lampaui\\ambang} (E);
\draw (M) edge node[left] {apoptosis} (D1);
\draw (C) edge node[left, align=center] {eliminasi\\imun} (D2);
\draw[->, bend left=45] (M) to node[above] {repair} (H);
\end{tikzpicture}%
}
\caption{Diagram alir state sel dalam simulasi. Sel sehat dapat mengalami mutasi saat pembelahan menjadi termutasi. Sel termutasi dapat kembali ke sehat melalui repair, dihapus melalui apoptosis, atau mengakumulasi mutasi menjadi prakanker lalu kanker. Sel kanker dapat dieliminasi oleh imun atau melampaui ambang kontrol (cancer escape).}
\label{fig:simulation-flow}
\end{figure}"""


def _simulation_loop_tex() -> str:
    return r"""\begin{figure}[t]
\centering
\resizebox{0.65\columnwidth}{!}{%
\begin{tikzpicture}[
    box/.style={rectangle, draw, rounded corners=2pt, minimum width=3.4cm, align=center, font=\footnotesize, inner sep=3pt, fill=white},
    arr/.style={draw, ->, >=stealth, semithick},
    node distance=0.55cm,
]
\node[box, fill=blue!5!white] (s1) {1. Cell division\\${}+$ possible mutation};
\node[box, below=of s1] (s2) {2. DNA repair\\or apoptosis};
\node[box, below=of s2] (s3) {3. Cancer transformation\\if mutations $\ge$ threshold};
\node[box, below=of s3] (s4) {4. Cancer growth\\vs immune elimination};
\node[box, below=of s4] (s5) {5. Immune decline\\due to age and cancer};
\node[box, below=of s5] (s6) {6. Cancer escape if\\cancer exceeds immunity};

\draw[arr] (s1) -- (s2);
\draw[arr] (s2) -- (s3);
\draw[arr] (s3) -- (s4);
\draw[arr] (s4) -- (s5);
\draw[arr] (s5) -- (s6);
\end{tikzpicture}%
}
\caption{Urutan proses simulasi pada setiap langkah waktu: pembelahan sel dengan kemungkinan mutasi, perbaikan DNA atau apoptosis, transformasi kanker jika ambang mutasi tercapai, kompetisi kanker--imun, penurunan kapasitas imun, dan pengecekan cancer escape. Langkah 1--6 diulang hingga \texttt{lifespan\_steps} atau hingga cancer escape terjadi.}
\label{fig:simulation-loop}
\end{figure}"""


def write_figures_and_tables() -> None:
    TEX_FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(exist_ok=True)
    species = _read_csv(RESULTS_DIR / "species_cancer_risk.csv")
    summary = _read_csv(RESULTS_DIR / "analysis_summary.csv")
    top = _read_csv(RESULTS_DIR / "top_suppression_residuals.csv")
    orders = _read_csv(RESULTS_DIR / "order_summary.csv")
    bootstrap = _read_csv(RESULTS_DIR / "bootstrap_slopes.csv")
    thresholds = _read_csv(RESULTS_DIR / "postmortem_thresholds.csv")

    (TEX_FIGURES_DIR / "F0_simulation_workflow.tex").write_text(_simulation_flow_tex(), encoding="utf-8")
    (TEX_FIGURES_DIR / "F0b_simulation_loop.tex").write_text(_simulation_loop_tex(), encoding="utf-8")
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
        "\\caption{Ringkasan empiris dataset mamalia sebagai konteks Peto's Paradox.}",
        "\\label{tab:empirical-context}",
        "\\begin{tabular}{lr}",
        "\\toprule",
        "Besaran & Nilai\\\\",
        "\\midrule",
        f"Jumlah spesies & {int(metrics['n_species'])}\\\\",
        f"Spesies CMR $>$ 0 & {int(metrics['n_species_nonzero_cmr'])}\\\\",
        f"Slope log massa--log CMR & {metrics['slope_log_mass_log_cmr']:.3f}\\\\",
        f"$R^2$ log massa--log CMR & {metrics['r2_log_mass_log_cmr']:.3f}\\\\",
        f"Slope exposure--log CMR & {metrics['slope_log_exposure_log_cmr']:.3f}\\\\",
        f"$R^2$ exposure--log CMR & {metrics['r2_log_exposure_log_cmr']:.3f}\\\\",
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
