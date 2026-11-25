"""Testy wykresów i korelacji na małych, kontrolowanych danych."""

from pathlib import Path

import pandas as pd
import pytest

from studio.plots import build_figure, compare_figure, save_figure, top_correlations


@pytest.fixture
def frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "x": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            "y": [2.0, 4.0, 6.0, 8.0, 10.0, 12.0],  # y = 2x
            "z": [6.0, 1.0, 4.0, 2.0, 5.0, 3.0],
            "const": [7, 7, 7, 7, 7, 7],
            "cat": ["a", "a", "b", "b", "b", "c"],
            "flag": [True, False, False, False, False, True],
        }
    )


@pytest.mark.parametrize(
    ("kind", "x", "y", "hue"),
    [
        ("histogram", "x", None, None),
        ("scatter", "x", "y", "cat"),
        ("box", "x", None, None),
        ("box", "x", None, "cat"),
        ("bar", "cat", None, None),
        ("bar", "cat", "x", None),
    ],
)
def test_valid_charts_have_title_and_labels(frame: pd.DataFrame, kind: str, x: str, y: str, hue: str) -> None:
    ax = build_figure(frame, kind, x, y, hue).axes[0]
    assert ax.get_title()
    assert ax.get_ylabel()


@pytest.mark.parametrize(
    ("kind", "x", "y", "message"),
    [
        ("histogram", "cat", None, "nie jest liczbowa"),
        ("histogram", "const", None, "jest stała"),
        ("histogram", "flag", None, "nie jest liczbowa"),
        ("histogram", None, None, "Nie wybrano"),
        ("scatter", "x", None, "Nie wybrano"),
        ("scatter", "x", "x", "różne kolumny"),
        ("box", "missing_col", None, "Brak kolumny"),
        ("bar", "x", "cat", "nie jest liczbowa"),
        ("pie", "x", None, "Nieznany typ"),
    ],
)
def test_invalid_charts_are_blocked(frame: pd.DataFrame, kind: str, x: str, y: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        build_figure(frame, kind, x, y)


def test_bar_counts(frame: pd.DataFrame) -> None:
    ax = build_figure(frame, "bar", "cat").axes[0]
    assert [patch.get_height() for patch in ax.patches] == [3, 2, 1]


def test_too_many_categories_rejected() -> None:
    data = pd.DataFrame({"id": [f"k{i}" for i in range(40)]})
    with pytest.raises(ValueError, match="unikalnych"):
        build_figure(data, "bar", "id")


def test_empty_frame_rejected(frame: pd.DataFrame) -> None:
    with pytest.raises(ValueError, match="pusty"):
        build_figure(frame.iloc[0:0], "histogram", "x")


def test_compare_figure_has_two_panels(frame: pd.DataFrame) -> None:
    fig = compare_figure(frame, frame.iloc[:4], "histogram", "x")
    titles = [ax.get_title() for ax in fig.axes]
    assert titles[0].startswith("Przed") and titles[1].startswith("Po")


def test_top_correlation_finds_linear_pair(frame: pd.DataFrame) -> None:
    top = top_correlations(frame, n=1).iloc[0]
    assert {top["kolumna 1"], top["kolumna 2"]} == {"x", "y"}
    assert top["r Pearsona"] == 1.0
    assert top["siła"] == "silna dodatnia"


@pytest.mark.parametrize("suffix", [".png", ".svg", ".pdf"])
def test_export_formats(frame: pd.DataFrame, tmp_path: Path, suffix: str) -> None:
    path = save_figure(build_figure(frame, "histogram", "x"), tmp_path / f"chart{suffix}")
    assert path.stat().st_size > 0


def test_export_bad_format(frame: pd.DataFrame, tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Nieobsługiwany format"):
        save_figure(build_figure(frame, "histogram", "x"), tmp_path / "chart.jpg")
