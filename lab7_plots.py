"""Lab 7: wykresy przed/po (histogram, punktowy, pudełkowy, słupkowy) i analiza korelacji.

Użycie:
    python lab7_plots.py data/housing_dirty.csv
    python lab7_plots.py data/housing_dirty.csv --out output/plots
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from lab6_clean import run_pipeline
from studio.plots import compare_figure, correlation_figure, save_figure, top_correlations
from studio.session import CsvLoadError, DataSession

# (nazwa pliku, typ, x, y, hue) – wykresy dla California Housing; brakujące kolumny => wykres pominięty.
CHARTS = [
    ("hist_median_income", "histogram", "median_income", None, None),
    ("hist_housing_median_age", "histogram", "housing_median_age", None, None),
    ("scatter_income_vs_value", "scatter", "median_income", "median_house_value", "ocean_proximity"),
    ("box_housing_median_age", "box", "housing_median_age", None, None),
    ("box_value_by_ocean", "box", "median_house_value", None, "ocean_proximity"),
    ("bar_ocean_counts", "bar", "ocean_proximity", None, None),
    ("bar_value_by_ocean", "bar", "ocean_proximity", "median_house_value", None),
]
FORMATS = (".png", ".svg")

CAUSATION_NOTE = """\
## Interpretacja – korelacja to nie przyczynowość

- Współczynnik korelacji opisuje, jak silnie dwie zmienne **współwystępują**, a nie czy jedna **powoduje** drugą.
- `total_rooms`, `total_bedrooms`, `population` i `households` korelują silnie, bo wszystkie rosną
  z wielkością dzielnicy (wspólna zmienna ukryta), a nie dlatego, że jedna wywołuje drugą.
- Związek `median_income` – `median_house_value` może działać w obie strony (zamożni kupują droższe domy,
  drogie okolice przyciągają zamożnych) albo wynikać z trzeciego czynnika (lokalizacja). Dane obserwacyjne
  tego nie rozstrzygają – potrzebny byłby eksperyment lub model przyczynowy.
- r Pearsona mierzy tylko zależność **liniową** i jest wrażliwy na outliery/błędne wartości; dlatego podajemy też
  rho Spearmana (rangowy) i porównujemy wyniki przed i po czyszczeniu.

## Obserwacje z wykresów przed/po

- Wykres pudełkowy `housing_median_age`: przed czyszczeniem wartości 999 i -1 rozciągają skalę; po regule
  zakresu [1, 52] rozkład jest czytelny.
- Wykres punktowy: imputacja medianą jest widoczna jako pionowy pas punktów przy jednej wartości
  `median_income` – uzupełnione rekordy nie niosą informacji o zależności i lekko ją zaniżają
  (alternatywa: `--missing drop`).
- Wykres słupkowy średnich: kategorie z kilkoma rekordami (np. `ISLAND`) dają niewiarygodną średnią –
  zawsze czytać razem z wykresem liczności (`bar_ocean_counts`).
"""


def correlation_report(before: pd.DataFrame, after: pd.DataFrame) -> str:
    return "\n".join(
        [
            "# Analiza korelacji\n",
            "## Najsilniejsze pary – dane surowe\n",
            f"```\n{top_correlations(before).to_string(index=False)}\n```\n",
            "## Najsilniejsze pary – po czyszczeniu\n",
            f"```\n{top_correlations(after).to_string(index=False)}\n```\n",
            "Skala siły |r|: ≥ 0.7 silna, 0.4–0.7 umiarkowana, 0.2–0.4 słaba, < 0.2 brak/bardzo słaba.\n",
            CAUSATION_NOTE,
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("csv", type=Path, help="plik wejściowy CSV (separator , lub ;)")
    parser.add_argument("--missing", choices=["median", "mean", "drop"], default="median")
    parser.add_argument("--out", type=Path, default=Path("output/plots"), help="katalog na wykresy")
    args = parser.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8")

    try:
        session = DataSession.from_csv(args.csv)
    except CsvLoadError as exc:
        print(f"Błąd wczytywania: {exc}", file=sys.stderr)
        return 1
    run_pipeline(session, args.missing)
    before, after = session.raw, session.current

    try:
        for name, kind, x, y, hue in CHARTS:
            try:
                fig = compare_figure(before, after, kind, x, y, hue)
            except ValueError as exc:
                print(f"Pominięto {name}: {exc}")
                continue
            for suffix in FORMATS:
                save_figure(fig, args.out / f"{name}{suffix}")
            print(f"Zapisano {name} ({', '.join(FORMATS)})")

        for label, frame in (("before", before), ("after", after)):
            title = f"Macierz korelacji Pearsona – {'przed' if label == 'before' else 'po'} czyszczeniu"
            save_figure(correlation_figure(frame, title=title), args.out / f"correlation_{label}.png")
        report = correlation_report(before, after)
        (args.out / "correlation.md").write_text(report, encoding="utf-8")
    except ValueError as exc:
        print(f"Błąd: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"Błąd zapisu do '{args.out}': {exc}. Zamknij plik lub wybierz inny katalog.", file=sys.stderr)
        return 1

    print(f"\n{report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
