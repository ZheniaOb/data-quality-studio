"""Wykresy (Matplotlib + Seaborn) zwracające Figure.

Ten sam obiekt Figure można osadzić w Tkinter (FigureCanvasTkAgg) i zapisać do pliku.
Nie używamy pyplot, więc nie ma globalnego stanu wykresów.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.axes import Axes
from matplotlib.figure import Figure

ChartKind = Literal["histogram", "scatter", "box", "bar"]
CHART_KINDS: tuple[ChartKind, ...] = ("histogram", "scatter", "box", "bar")
MAX_CATEGORIES = 30
EXPORT_FORMATS = (".png", ".pdf", ".svg")


# ---------- walidacja kolumn ----------


def is_numeric(series: pd.Series) -> bool:
    return pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_bool_dtype(series)


def numeric_columns(frame: pd.DataFrame) -> list[str]:
    return [col for col in frame.columns if is_numeric(frame[col])]


def categorical_columns(frame: pd.DataFrame) -> list[str]:
    return [col for col in frame.columns if 0 < frame[col].nunique() <= MAX_CATEGORIES]


def _require(frame: pd.DataFrame, column: str | None, role: str) -> str:
    if not column:
        raise ValueError(f"Nie wybrano kolumny ({role}).")
    if column not in frame.columns:
        raise ValueError(f"Brak kolumny '{column}' w danych.")
    return column


def validate_numeric(frame: pd.DataFrame, column: str | None, role: str = "oś X") -> pd.Series:
    """Zwraca wartości kolumny bez braków albo zgłasza błąd z podpowiedzią."""
    column = _require(frame, column, role)
    series = frame[column]
    if not is_numeric(series):
        raise ValueError(
            f"Kolumna '{column}' nie jest liczbowa (typ {series.dtype}) – wybierz kolumnę liczbową."
        )
    values = series.dropna()
    if values.empty:
        raise ValueError(f"Kolumna '{column}' nie zawiera żadnych wartości.")
    if values.nunique() < 2:
        raise ValueError(
            f"Kolumna '{column}' jest stała ({values.iloc[0]}) – wykres nie niesie informacji."
        )
    return values


def validate_category(frame: pd.DataFrame, column: str | None, role: str = "kategoria") -> str:
    column = _require(frame, column, role)
    unique = frame[column].nunique()
    if unique == 0:
        raise ValueError(f"Kolumna '{column}' nie zawiera żadnych wartości.")
    if unique > MAX_CATEGORIES:
        raise ValueError(
            f"Kolumna '{column}' ma {unique} unikalnych wartości – jako kategorię wybierz kolumnę "
            f"z co najwyżej {MAX_CATEGORIES} wartościami (np. tekstową)."
        )
    return column


# ---------- rysowanie na osi ----------


def _histogram(ax: Axes, frame: pd.DataFrame, x: str | None) -> None:
    values = validate_numeric(frame, x)
    sns.histplot(x=values, ax=ax)
    ax.set(title=f"Rozkład: {x}", xlabel=x, ylabel="Liczba rekordów")


def _scatter(ax: Axes, frame: pd.DataFrame, x: str | None, y: str | None, hue: str | None) -> None:
    validate_numeric(frame, x, "oś X")
    validate_numeric(frame, y, "oś Y")
    if x == y:
        raise ValueError("Na osi X i Y wybierz dwie różne kolumny.")
    if hue:
        validate_category(frame, hue, "kolor")
    data = frame.dropna(subset=[x, y])
    sns.scatterplot(data=data, x=x, y=y, hue=hue, s=12, alpha=0.5, linewidth=0, ax=ax)
    r = data[x].corr(data[y])
    ax.set(title=f"{y} względem {x} (r Pearsona = {r:.2f})", xlabel=x, ylabel=y)


def _box(ax: Axes, frame: pd.DataFrame, x: str | None, hue: str | None) -> None:
    validate_numeric(frame, x, "wartość")
    if hue:
        validate_category(frame, hue, "grupowanie")
        order = frame[hue].value_counts().index
        sns.boxplot(data=frame, x=hue, y=x, order=order, ax=ax)
        ax.set(title=f"{x} w grupach {hue}", xlabel=hue, ylabel=x)
        ax.tick_params(axis="x", rotation=20)
    else:
        sns.boxplot(data=frame, y=x, ax=ax)
        ax.set(title=f"Rozkład i outliery (wąsy = 1.5·IQR): {x}", xlabel="", ylabel=x)


def _bar(ax: Axes, frame: pd.DataFrame, x: str | None, y: str | None) -> None:
    validate_category(frame, x)
    if y:
        validate_numeric(frame, y, "wartość")
        heights = frame.groupby(x)[y].mean().sort_values(ascending=False)
        ax.set(title=f"Średnia {y} wg {x}", ylabel=f"Średnia {y}")
    else:
        heights = frame[x].value_counts()
        ax.set(title=f"Liczność kategorii: {x}", ylabel="Liczba rekordów")
    ax.bar(heights.index.astype(str), heights.to_numpy(), color="C0")
    ax.set_xlabel(x)
    ax.tick_params(axis="x", rotation=20)


def draw(
    ax: Axes,
    frame: pd.DataFrame,
    kind: ChartKind,
    x: str | None,
    y: str | None = None,
    hue: str | None = None,
) -> None:
    """Rysuje wykres na podanej osi.

    histogram: x liczbowa | scatter: x, y liczbowe, hue = kolor (kategoria)
    box: x liczbowa, hue = grupowanie (kategoria) | bar: x kategoria, y liczbowa (średnia) lub brak (liczność)
    """
    if frame.empty:
        raise ValueError("Brak danych do narysowania – zbiór jest pusty.")
    if kind == "histogram":
        _histogram(ax, frame, x)
    elif kind == "scatter":
        _scatter(ax, frame, x, y, hue)
    elif kind == "box":
        _box(ax, frame, x, hue)
    elif kind == "bar":
        _bar(ax, frame, x, y)
    else:
        raise ValueError(f"Nieznany typ wykresu: {kind}. Dostępne: {', '.join(CHART_KINDS)}")


def build_figure(
    frame: pd.DataFrame,
    kind: ChartKind,
    x: str | None,
    y: str | None = None,
    hue: str | None = None,
) -> Figure:
    """Buduje wykres na podstawie parametrów (używane przez skrypt i GUI)."""
    fig = Figure(figsize=(7, 4.5), dpi=100)
    draw(fig.add_subplot(), frame, kind, x, y, hue)
    fig.tight_layout()
    return fig


def compare_figure(
    before: pd.DataFrame,
    after: pd.DataFrame,
    kind: ChartKind,
    x: str | None,
    y: str | None = None,
    hue: str | None = None,
) -> Figure:
    """Ten sam wykres dla danych przed i po czyszczeniu, obok siebie."""
    fig = Figure(figsize=(13, 4.8), dpi=100)
    for ax, frame, label in zip(fig.subplots(1, 2), (before, after), ("Przed", "Po")):
        draw(ax, frame, kind, x, y, hue)
        ax.set_title(f"{label}: {ax.get_title()}")
    fig.tight_layout()
    return fig


# ---------- korelacja ----------


def correlation_matrix(frame: pd.DataFrame, method: str = "pearson") -> pd.DataFrame:
    columns = [col for col in numeric_columns(frame) if frame[col].nunique() > 1]
    if len(columns) < 2:
        raise ValueError("Do korelacji potrzebne są co najmniej dwie niestałe kolumny liczbowe.")
    return frame[columns].corr(method=method)


def correlation_figure(frame: pd.DataFrame, method: str = "pearson", title: str = "") -> Figure:
    corr = correlation_matrix(frame, method)
    fig = Figure(figsize=(8, 6.5), dpi=100)
    ax = fig.add_subplot()
    sns.heatmap(
        corr, annot=True, fmt=".2f", cmap="coolwarm", vmin=-1, vmax=1, center=0,
        square=True, annot_kws={"size": 8}, ax=ax,
    )
    ax.set_title(title or f"Macierz korelacji ({method})")
    fig.tight_layout()
    return fig


def strength(r: float) -> str:
    size = abs(r)
    level = "silna" if size >= 0.7 else "umiarkowana" if size >= 0.4 else "słaba" if size >= 0.2 else "brak/b. słaba"
    return f"{level} {'dodatnia' if r > 0 else 'ujemna'}"


def top_correlations(frame: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """Najsilniej skorelowane pary (Pearson) wraz ze współczynnikiem Spearmana."""
    pearson = correlation_matrix(frame, "pearson")
    spearman = correlation_matrix(frame, "spearman")
    upper = np.triu(np.ones(pearson.shape, dtype=bool), k=1)
    pairs = pearson.where(upper).stack()
    pairs = pairs.loc[pairs.abs().sort_values(ascending=False).index[:n]]
    return pd.DataFrame(
        {
            "kolumna 1": pairs.index.get_level_values(0),
            "kolumna 2": pairs.index.get_level_values(1),
            "r Pearsona": pairs.round(3).to_numpy(),
            "rho Spearmana": [round(spearman.loc[a, b], 3) for a, b in pairs.index],
            "siła": [strength(r) for r in pairs],
        }
    )


# ---------- eksport ----------


def save_figure(fig: Figure, path: Path | str) -> Path:
    path = Path(path)
    if path.suffix.lower() not in EXPORT_FORMATS:
        raise ValueError(f"Nieobsługiwany format '{path.suffix}'. Wybierz: {', '.join(EXPORT_FORMATS)}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    return path
