from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from src.cell_simulation import (
    CANCER,
    HEALTHY,
    MUTATED,
    PRECANCER,
    CellSimulation,
    SimulationParameters,
    SimulationSnapshot,
    scenario_presets,
)


CELL_COLORS = {
    HEALTHY: "#2e7d32",
    MUTATED: "#fdd835",
    PRECANCER: "#fb8c00",
    CANCER: "#c62828",
}


PARAMETER_HELP = {
    "initial_cells": "Starting number of simulated cell units. In this sandbox, one unit represents a scaled group of real cells, not one biological cell.",
    "max_cells": "Carrying capacity of the simulated tissue. Larger values represent a larger body or tissue with more opportunities for cell divisions.",
    "lifespan_steps": "Number of time steps the organism is simulated. More steps represent a longer period for mutations to accumulate.",
    "division_rate": "Probability that a normal cell attempts division during one step. More divisions create more chances for mutation.",
    "mutation_rate": "Probability that a dividing normal cell gains mutation damage. This represents mutation per division in the multi-hit cancer model.",
    "repair_rate": "Probability that a damaged non-cancer cell repairs one mutation. Higher repair reduces the chance that cells reach the cancer threshold.",
    "apoptosis_rate": "Probability that a damaged non-cancer cell is removed by programmed cell death. This is a protective mechanism against heavily damaged cells.",
    "required_mutations": "Number of mutation hits needed before a cell becomes cancerous. Higher values mean cancer requires more steps to emerge.",
    "cancer_division_rate": "Probability that a cancer cell divides during one step. Higher values make cancer cells expand faster after transformation.",
    "immune_strength": "Initial immune control threshold. Cancer escape is marked when cancer cells exceed this remaining immune capacity.",
    "immune_kill_rate": "Strength of immune removal of cancer cells. Higher values mean immune control is more effective at clearing cancer cells.",
    "immune_aging_rate": "Natural decline of immune control per step. This represents weakening immune surveillance over time.",
    "immune_depletion_rate": "Additional immune decline caused by cancer burden. More cancer cells can exhaust immune control faster.",
}


class Tooltip:
    def __init__(self, widget: tk.Widget, text: str) -> None:
        self.widget = widget
        self.text = text
        self.window: tk.Toplevel | None = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, _event: tk.Event | None = None) -> None:
        if self.window is not None:
            return
        x = self.widget.winfo_rootx() + 18
        y = self.widget.winfo_rooty() + 18
        self.window = tk.Toplevel(self.widget)
        self.window.wm_overrideredirect(True)
        self.window.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            self.window,
            text=self.text,
            justify="left",
            wraplength=320,
            background="#fff7cc",
            foreground="#1f2937",
            relief="solid",
            borderwidth=1,
            padx=8,
            pady=6,
        )
        label.pack()

    def hide(self, _event: tk.Event | None = None) -> None:
        if self.window is not None:
            self.window.destroy()
            self.window = None


class SimulationApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Peto's Paradox Cell Simulation")
        self.root.minsize(1100, 720)

        self.presets = scenario_presets()
        self.current_preset = tk.StringVar(value="large_long_lived_naive")
        self.running = False
        self.after_id: str | None = None

        self.slider_vars: dict[str, tk.DoubleVar] = {}
        self.metric_vars: dict[str, tk.StringVar] = {}

        self.simulation = CellSimulation(self.presets[self.current_preset.get()])

        self._build_layout()
        self._load_parameters(self.simulation.parameters)
        self._refresh_view()

    def _build_layout(self) -> None:
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=0)

        self.controls_container = ttk.Frame(self.root, padding=10)
        self.controls_container.grid(row=0, column=0, sticky="ns")

        self.center = ttk.Frame(self.root, padding=10)
        self.center.grid(row=0, column=1, sticky="nsew")
        self.center.columnconfigure(0, weight=1)
        self.center.rowconfigure(1, weight=1)

        self.metrics = ttk.Frame(self.root, padding=10)
        self.metrics.grid(row=0, column=2, sticky="ns")

        self.graph = tk.Canvas(self.root, height=170, background="#111827", highlightthickness=0)
        self.graph.grid(row=1, column=0, columnspan=3, sticky="ew", padx=10, pady=(0, 10))

        self._build_controls()
        self._build_center()
        self._build_metrics()

    def _build_controls(self) -> None:
        self.controls_canvas = tk.Canvas(self.controls_container, width=285, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.controls_container, orient="vertical", command=self.controls_canvas.yview)
        self.controls = ttk.Frame(self.controls_canvas)
        self.controls_canvas.configure(yscrollcommand=scrollbar.set)

        self.controls_window = self.controls_canvas.create_window((0, 0), window=self.controls, anchor="nw")
        self.controls_canvas.pack(side="left", fill="y", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.controls.bind("<Configure>", self._update_controls_scroll_region)
        self.controls_canvas.bind("<Configure>", self._resize_controls_window)
        self.controls_canvas.bind("<Enter>", self._bind_mousewheel)
        self.controls_canvas.bind("<Leave>", self._unbind_mousewheel)

        ttk.Label(self.controls, text="Scenario", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        preset_box = ttk.Combobox(
            self.controls,
            textvariable=self.current_preset,
            values=list(self.presets.keys()),
            state="readonly",
            width=28,
        )
        preset_box.pack(fill="x", pady=(4, 8))
        preset_box.bind("<<ComboboxSelected>>", lambda _event: self._apply_preset())

        buttons = ttk.Frame(self.controls)
        buttons.pack(fill="x", pady=(0, 12))
        ttk.Button(buttons, text="Run", command=self.start).grid(row=0, column=0, sticky="ew")
        ttk.Button(buttons, text="Pause", command=self.pause).grid(row=0, column=1, sticky="ew")
        ttk.Button(buttons, text="Step", command=self.step_once).grid(row=1, column=0, sticky="ew")
        ttk.Button(buttons, text="Reset", command=self.reset).grid(row=1, column=1, sticky="ew")
        buttons.columnconfigure(0, weight=1)
        buttons.columnconfigure(1, weight=1)

        ttk.Label(self.controls, text="Parameters", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self._add_slider("initial_cells", 10, 250, 1)
        self._add_slider("max_cells", 50, 5000, 1)
        self._add_slider("lifespan_steps", 50, 900, 1)
        self._add_slider("division_rate", 0.0, 0.25, 0.005)
        self._add_slider("mutation_rate", 0.0, 0.15, 0.005)
        self._add_slider("repair_rate", 0.0, 0.25, 0.005)
        self._add_slider("apoptosis_rate", 0.0, 0.15, 0.005)
        self._add_slider("required_mutations", 1, 8, 1)
        self._add_slider("cancer_division_rate", 0.0, 0.35, 0.005)
        self._add_slider("immune_strength", 0, 80, 1)
        self._add_slider("immune_kill_rate", 0.0, 0.2, 0.005)
        self._add_slider("immune_aging_rate", 0.0, 0.08, 0.002)
        self._add_slider("immune_depletion_rate", 0.0, 0.02, 0.001)

    def _update_controls_scroll_region(self, _event: tk.Event) -> None:
        self.controls_canvas.configure(scrollregion=self.controls_canvas.bbox("all"))

    def _resize_controls_window(self, event: tk.Event) -> None:
        self.controls_canvas.itemconfigure(self.controls_window, width=event.width)

    def _bind_mousewheel(self, _event: tk.Event) -> None:
        self.root.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self, _event: tk.Event) -> None:
        self.root.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event: tk.Event) -> None:
        self.controls_canvas.yview_scroll(int(-event.delta / 120), "units")

    def _add_slider(self, name: str, minimum: float, maximum: float, step: float) -> None:
        frame = ttk.Frame(self.controls)
        frame.pack(fill="x", pady=2)
        label_row = ttk.Frame(frame)
        label_row.pack(fill="x")
        label = ttk.Label(label_row, text=name)
        label.pack(side="left")
        help_label = ttk.Label(label_row, text="(?)", cursor="question_arrow")
        help_label.pack(side="left", padx=(5, 0))
        Tooltip(help_label, PARAMETER_HELP[name])
        value_var = tk.DoubleVar()
        self.slider_vars[name] = value_var
        value_label = ttk.Label(frame, width=8)
        value_label.pack(anchor="e")
        scale = ttk.Scale(
            frame,
            from_=minimum,
            to=maximum,
            variable=value_var,
            command=lambda _value, n=name, s=step, v=value_var, l=value_label: self._slider_changed(n, s, v, l),
        )
        scale.pack(fill="x")

    def _build_center(self) -> None:
        ttk.Label(
            self.center,
            text="Cell Grid",
            font=("Segoe UI", 13, "bold"),
        ).grid(row=0, column=0, sticky="w")
        self.canvas = tk.Canvas(self.center, background="#0f172a", highlightthickness=0)
        self.canvas.grid(row=1, column=0, sticky="nsew", pady=(8, 0))

        legend = ttk.Frame(self.center)
        legend.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        for state, color in CELL_COLORS.items():
            item = ttk.Frame(legend)
            item.pack(side="left", padx=(0, 14))
            swatch = tk.Canvas(item, width=14, height=14, highlightthickness=0)
            swatch.create_rectangle(0, 0, 14, 14, fill=color, outline=color)
            swatch.pack(side="left")
            ttk.Label(item, text=state).pack(side="left", padx=(4, 0))

    def _build_metrics(self) -> None:
        ttk.Label(self.metrics, text="Live Metrics", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        for name in (
            "step",
            "healthy_cells",
            "mutated_cells",
            "precancer_cells",
            "cancer_cells",
            "dead_removed_cells",
            "total_cells",
            "immune_strength",
            "immune_escape",
            "escape_time",
        ):
            var = tk.StringVar(value="-")
            self.metric_vars[name] = var
            row = ttk.Frame(self.metrics)
            row.pack(fill="x", pady=4)
            ttk.Label(row, text=name, width=20).pack(side="left")
            ttk.Label(row, textvariable=var, width=14).pack(side="right")

        ttk.Separator(self.metrics).pack(fill="x", pady=12)
        self.interpretation = tk.StringVar(value="Adjust parameters or choose a preset, then run the model.")
        ttk.Label(
            self.metrics,
            textvariable=self.interpretation,
            wraplength=230,
            justify="left",
        ).pack(anchor="w")

    def _slider_changed(
        self,
        name: str,
        step: float,
        value_var: tk.DoubleVar,
        label: ttk.Label,
    ) -> None:
        value = value_var.get()
        if step >= 1:
            value = round(value)
            value_var.set(value)
            label.configure(text=str(int(value)))
        else:
            decimals = 3 if step < 0.005 else 2
            label.configure(text=f"{value:.{decimals}f}")

    def _apply_preset(self) -> None:
        self.pause()
        parameters = self.presets[self.current_preset.get()]
        self.simulation = CellSimulation(parameters)
        self._load_parameters(parameters)
        self._refresh_view()

    def _load_parameters(self, parameters: SimulationParameters) -> None:
        for name, value_var in self.slider_vars.items():
            value_var.set(float(getattr(parameters, name)))

    def _parameters_from_sliders(self) -> SimulationParameters:
        initial_cells = int(self.slider_vars["initial_cells"].get())
        max_cells = max(initial_cells, int(self.slider_vars["max_cells"].get()))
        return SimulationParameters(
            initial_cells=initial_cells,
            max_cells=max_cells,
            lifespan_steps=int(self.slider_vars["lifespan_steps"].get()),
            division_rate=self.slider_vars["division_rate"].get(),
            mutation_rate=self.slider_vars["mutation_rate"].get(),
            repair_rate=self.slider_vars["repair_rate"].get(),
            apoptosis_rate=self.slider_vars["apoptosis_rate"].get(),
            required_mutations=int(self.slider_vars["required_mutations"].get()),
            cancer_division_rate=self.slider_vars["cancer_division_rate"].get(),
            immune_strength=self.slider_vars["immune_strength"].get(),
            immune_kill_rate=self.slider_vars["immune_kill_rate"].get(),
            immune_aging_rate=self.slider_vars["immune_aging_rate"].get(),
            immune_depletion_rate=self.slider_vars["immune_depletion_rate"].get(),
        )

    def start(self) -> None:
        if self.running:
            return
        if self.simulation.step_number >= self.simulation.parameters.lifespan_steps:
            self.reset()
        self.running = True
        self._tick()

    def pause(self) -> None:
        self.running = False
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None

    def step_once(self) -> None:
        self.pause()
        if self.simulation.step_number >= self.simulation.parameters.lifespan_steps:
            return
        self.simulation.step()
        self._refresh_view()

    def reset(self) -> None:
        self.pause()
        self.simulation = CellSimulation(self._parameters_from_sliders())
        self._refresh_view()

    def _tick(self) -> None:
        if not self.running:
            return
        if self.simulation.step_number >= self.simulation.parameters.lifespan_steps:
            self.pause()
            return
        self.simulation.step()
        self._refresh_view()
        self.after_id = self.root.after(60, self._tick)

    def _refresh_view(self) -> None:
        snapshot = self.simulation.snapshot()
        self._draw_grid()
        self._draw_graph()
        self._update_metrics(snapshot)
        self._update_interpretation(snapshot)

    def _draw_grid(self) -> None:
        self.canvas.delete("all")
        width = max(1, self.canvas.winfo_width())
        height = max(1, self.canvas.winfo_height())
        cells = self.simulation.cells
        if not cells:
            return

        columns = max(1, int(len(cells) ** 0.5))
        rows = (len(cells) + columns - 1) // columns
        cell_size = max(2, min(width / columns, height / rows))

        for index, cell in enumerate(cells):
            column = index % columns
            row = index // columns
            x1 = column * cell_size
            y1 = row * cell_size
            x2 = x1 + cell_size - 1
            y2 = y1 + cell_size - 1
            color = CELL_COLORS.get(cell.state, "#e5e7eb")
            self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline="")

    def _draw_graph(self) -> None:
        self.graph.delete("all")
        history = self.simulation.history
        width = max(1, self.graph.winfo_width())
        height = max(1, self.graph.winfo_height())
        padding = 18
        self.graph.create_text(12, 10, text="Cancer cells over time", fill="#e5e7eb", anchor="nw")
        if len(history) < 2:
            return

        max_cancer = max(1, max(snapshot.cancer_cells for snapshot in history))
        max_step = max(1, self.simulation.parameters.lifespan_steps)
        points: list[float] = []
        for snapshot in history:
            x = padding + (width - 2 * padding) * snapshot.step / max_step
            y = height - padding - (height - 3 * padding) * snapshot.cancer_cells / max_cancer
            points.extend([x, y])
        if len(points) >= 4:
            self.graph.create_line(*points, fill="#f87171", width=2)

        current_immune = history[-1].immune_strength
        immune_y = height - padding - (height - 3 * padding) * min(current_immune, max_cancer) / max_cancer
        self.graph.create_line(padding, immune_y, width - padding, immune_y, fill="#60a5fa", dash=(4, 3))
        self.graph.create_text(width - padding, immune_y - 8, text="immune threshold", fill="#bfdbfe", anchor="e")

    def _update_metrics(self, snapshot: SimulationSnapshot) -> None:
        values = {
            "step": str(snapshot.step),
            "healthy_cells": str(snapshot.healthy_cells),
            "mutated_cells": str(snapshot.mutated_cells),
            "precancer_cells": str(snapshot.precancer_cells),
            "cancer_cells": str(snapshot.cancer_cells),
            "dead_removed_cells": str(snapshot.dead_removed_cells),
            "total_cells": str(snapshot.total_cells),
            "immune_strength": f"{snapshot.immune_strength:.2f}",
            "immune_escape": str(snapshot.immune_escape),
            "escape_time": "-" if snapshot.escape_time is None else str(snapshot.escape_time),
        }
        for name, value in values.items():
            self.metric_vars[name].set(value)

    def _update_interpretation(self, snapshot: SimulationSnapshot) -> None:
        if snapshot.immune_escape:
            self.interpretation.set(
                "Cancer escape occurred: cancer cells crossed the current immune threshold. Earlier escape means higher simulated risk."
            )
        elif snapshot.cancer_cells > 0:
            self.interpretation.set(
                "Cancer cells exist, but immune control is still above the cancer-cell count."
            )
        else:
            self.interpretation.set(
                "No cancer escape yet. Mutation, repair, apoptosis, division, and immune parameters shape the trajectory."
            )


def main() -> None:
    root = tk.Tk()
    app = SimulationApp(root)
    root.bind("<space>", lambda _event: app.pause() if app.running else app.start())
    root.mainloop()


if __name__ == "__main__":
    main()
