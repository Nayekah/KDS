# Simulasi Peto's Paradox dan Analisis Data Kanker Mamalia

Repositori ini berisi paper, pipeline Python, dan sandbox simulasi untuk proyek
IF3211 Domain-Specific Computation. Fokus utama proyek adalah simulasi konseptual
Peto's Paradox pada tingkat populasi sel, dengan analisis data kanker mamalia
Vincze et al. sebagai konteks empiris pendukung.

## Struktur

```text
main.py                  # Entry point pipeline analisis dan artefak laporan
simulation_app.py        # Sandbox simulasi desktop berbasis tkinter
src/cell_simulation.py   # Engine simulasi populasi sel
src/simulation_exports.py # Generator CSV dan tabel LaTeX hasil simulasi
src/data.py              # Loader dataset Vincze et al.
src/comparative.py       # Analisis CMR, exposure proxy, residual supresi
src/statistics.py        # Statistik ringan tanpa dependensi eksternal
src/figures.py           # Generator tabel/figur LaTeX untuk konteks empiris
tests/                   # Unit test standard-library
data/                    # Dataset XLS asli dan CSV hasil konversi
results/                 # CSV hasil analisis
figures/                 # SVG hasil visualisasi
doc/tex/                 # Paper LaTeX IEEE
.tools/tectonic-0.16.9/  # Compiler LaTeX lokal
```

## Menjalankan Pipeline

```bash
python main.py
```

Pipeline memakai Python standard library saja. Perintah ini menjalankan analisis
data mamalia, membuat ringkasan simulasi berulang, dan memperbarui artefak
laporan.

Output utama:

- `results/species_cancer_risk.csv`
- `results/analysis_summary.csv`
- `results/simulation_summary.csv`
- `doc/tex/contents/generated-results.tex`
- `doc/tex/contents/generated-simulation-results.tex`
- `doc/tex/figures/`

## Menjalankan Sandbox Simulasi

```bash
python simulation_app.py
```

Aplikasi desktop `tkinter` menyediakan preset skenario, slider parameter,
visualisasi grid sel, metrik langsung, dan grafik jumlah sel kanker. Parameter
simulasi mencakup jumlah sel, umur simulasi, laju pembelahan, laju mutasi,
perbaikan DNA, apoptosis, jumlah mutasi wajib, dan kontrol imun.

## Menjalankan Test

```bash
python -m unittest discover -s tests
```

Test mencakup invariant engine simulasi, determinisme seed, arah perilaku preset,
dan pembuatan artefak CSV/LaTeX simulasi.

## Compile Paper

```powershell
.tools\tectonic-0.16.9\tectonic.exe doc\tex\main.tex
```

Output PDF: `doc/tex/main.pdf`.

## Batasan

- Simulasi adalah model stokastik konseptual, bukan prediksi risiko kanker spesies tertentu.
- Analisis empiris memakai body mass dan lifespan sebagai proksi sederhana, bukan jumlah sel atau laju pembelahan jaringan sebenarnya.
- Proyek sengaja mempertahankan Python standard library saja; tidak memakai NumPy, pandas, SciPy, atau GPU.

## Penulis

- Mochammad Fariz Rifqi Rizqulloh (13523069@std.stei.itb.ac.id)
- Muhammad Jibril Ibrahim (13523085@std.stei.itb.ac.id)
- Nayaka Ghana Subrata (13523090@std.stei.itb.ac.id)
