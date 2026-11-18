"""Lab 6: profil danych, reguły jakości, pipeline czyszczenia, raport przed/po i cleaned.csv.

Użycie:
    python lab6_clean.py data/housing_dirty.csv
    python lab6_clean.py data/housing_dirty.csv --missing drop --out output
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

from studio.session import CsvLoadError, DataSession

INF = float("inf")

# Zakresy poprawnych wartości dla California Housing. Kolumny nieobecne w pliku są pomijane.
RANGE_RULES: dict[str, tuple[float, float]] = {
    "longitude": (-124.5, -114.0),
    "latitude": (32.5, 42.0),
    "housing_median_age": (1, 52),
    "total_rooms": (1, INF),
    "total_bedrooms": (0, INF),
    "population": (1, INF),
    "households": (1, INF),
    "median_income": (0.4999, 15.0001),
    "median_house_value": (14999, 500001),
}

# Kolumny, w których outliery IQR są tylko OZNACZANE (nie usuwane) – patrz README.
OUTLIER_COLUMNS = ["total_rooms", "total_bedrooms", "population", "households", "median_income"]


def active_rules(session: DataSession) -> dict[str, tuple[float, float]]:
    return {col: bounds for col, bounds in RANGE_RULES.items() if col in session.current.columns}


def outlier_columns(session: DataSession) -> list[str]:
    frame = session.current
    return [
        col
        for col in OUTLIER_COLUMNS
        if col in frame.columns and pd.api.types.is_numeric_dtype(frame[col])
    ]


def quality_findings(session: DataSession) -> pd.DataFrame:
    """Wykrywa problemy bez modyfikowania danych."""
    rows = [("pełne duplikaty", "(cały wiersz)", int(session.current.duplicated().sum()))]
    for col, (low, high) in active_rules(session).items():
        rows.append((f"poza zakresem [{low}, {high}]", col, int(session.range_mask(col, low, high).sum())))
    for col in outlier_columns(session):
        low, high = session.iqr_bounds(col)
        rows.append((f"outlier IQR×1.5 [{low:.4g}, {high:.4g}]", col, int(session.iqr_mask(col).sum())))
    return pd.DataFrame(rows, columns=["reguła", "kolumna", "liczba rekordów"])


def run_pipeline(session: DataSession, missing: str = "median") -> None:
    """Kolejność: duplikaty -> błędne wartości (na NaN) -> braki -> oznaczenie outlierów."""
    session.drop_duplicates()
    for col, (low, high) in active_rules(session).items():
        session.apply_range_rule(col, low, high, action="nan")
    frame = session.current
    for col in frame.columns[frame.isna().any()]:
        if missing == "drop":
            session.fill_missing(col, "drop")
        elif pd.api.types.is_numeric_dtype(session.current[col]):
            session.fill_missing(col, missing)
        else:
            session.fill_missing(col, "mode")
    for col in outlier_columns(session):
        session.handle_outliers(col, action="flag")


def block(frame: pd.DataFrame | pd.Series) -> str:
    return f"```\n{frame.to_string()}\n```\n"


def build_report(
    source: Path,
    before_summary: dict[str, int],
    before_profile: pd.DataFrame,
    before_describe: pd.DataFrame,
    findings: pd.DataFrame,
    session: DataSession,
) -> str:
    comparison = pd.DataFrame({"przed": before_summary, "po": session.summary()})
    missing = pd.DataFrame(
        {"braki przed": before_profile["missing"], "braki po": session.profile()["missing"]}
    ).fillna(0).astype(int)
    return "\n".join(
        [
            f"# Raport jakości danych – {source.name}\n",
            "## Podsumowanie przed / po\n",
            block(comparison),
            "## Profil danych surowych\n",
            block(before_profile),
            "## Statystyki opisowe (dane surowe)\n",
            block(before_describe.round(3)),
            "## Wykryte problemy (reguły jakości, przed czyszczeniem)\n",
            block(findings),
            "## Ślad zmian (kolejne operacje)\n",
            block(session.audit_frame()),
            "## Braki w kolumnach przed / po\n",
            block(missing),
            "## Statystyki opisowe (po czyszczeniu)\n",
            block(session.describe().round(3)),
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("csv", type=Path, help="plik wejściowy CSV (separator , lub ;)")
    parser.add_argument("--missing", choices=["median", "mean", "drop"], default="median",
                        help="strategia braków liczbowych (tekstowe: moda albo drop)")
    parser.add_argument("--out", type=Path, default=Path("output"), help="katalog wynikowy")
    args = parser.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):  # konsola Windows (cp1250/cp1251) nie zna wszystkich polskich znaków
        stream.reconfigure(encoding="utf-8")

    try:
        session = DataSession.from_csv(args.csv)
    except CsvLoadError as exc:
        print(f"Błąd wczytywania: {exc}", file=sys.stderr)
        return 1

    print(f"Podgląd danych ({args.csv}):\n{session.current.head().to_string()}\n")
    before_summary = session.summary()
    before_profile = session.profile()
    before_describe = session.describe()
    findings = quality_findings(session)

    run_pipeline(session, args.missing)

    report = build_report(args.csv, before_summary, before_profile, before_describe, findings, session)
    try:
        args.out.mkdir(parents=True, exist_ok=True)
        session.current.to_csv(args.out / "cleaned.csv", index=False)
        (args.out / "report.md").write_text(report, encoding="utf-8")
        session.audit_frame().to_csv(args.out / "audit_log.csv", index=False)
    except OSError as exc:
        print(f"Błąd zapisu do '{args.out}': {exc}. Zamknij plik lub wybierz inny katalog.", file=sys.stderr)
        return 1

    print(findings.to_string(index=False), "\n")
    print(session.audit_frame()[["operation", "params", "rows_before", "rows_after", "affected"]].to_string(index=False))
    print(f"\nZapisano: {args.out / 'cleaned.csv'}, {args.out / 'report.md'}, {args.out / 'audit_log.csv'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
