# Analisis Komputasional Peto's Paradox pada Data Kanker Mamalia

Repositori ini berisi paper dan pipeline Python untuk proyek IF3211
Domain-Specific Computation. Studi memakai dataset publik Vincze et al.
2022 untuk menganalisis hubungan cancer mortality risk, massa tubuh, adult
life expectancy, dan sinyal supresi kanker lintas mamalia.

## Struktur

```text
main.py                  # Entry point simulasi
src/data.py              # Loader dataset Vincze et al.
src/comparative.py       # Analisis CMR, exposure proxy, residual supresi
src/statistics.py        # Statistik ringan tanpa dependensi eksternal
src/figures.py           # Generator tabel dan figur TikZ
data/                    # Dataset XLS asli dan CSV hasil konversi
results/                 # CSV hasil analisis
figures/                 # SVG hasil visualisasi
doc/tex/                 # Paper LaTeX IEEE
.tools/tectonic-0.16.9/  # Compiler LaTeX lokal
```

## Menjalankan Analisis

```bash
python main.py
```

Pipeline memakai Python standard library saja. Hasil analisis ditulis ke
`results/`, `figures/`, `doc/tex/figures/`, dan
`doc/tex/contents/generated-results.tex`.

## Compile Paper

```powershell
cd doc/tex
..\..\.tools\tectonic-0.16.9\tectonic.exe main.tex
```

Output PDF: `doc/tex/main.pdf`.

## Penulis

- Mochammad Fariz Rifqi Rizqulloh (13523069@std.stei.itb.ac.id)
- Muhammad Jibril Ibrahim (13523085@std.stei.itb.ac.id)
- Nayaka Ghana Subrata (13523090@std.stei.itb.ac.id)
