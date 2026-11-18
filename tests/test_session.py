"""Testy logiki na małych, ręcznie kontrolowanych danych. Uruchomienie: python -m pytest"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from lab6_clean import run_pipeline
from studio.session import CsvLoadError, DataSession

SAMPLES = Path(__file__).resolve().parent.parent / "data" / "samples"


def make_session() -> DataSession:
    return DataSession(
        pd.DataFrame(
            {
                "a": [1.0, 2.0, np.nan, 4.0, 1.0],
                "b": ["x", None, "y", "y", "x"],
                "c": [10, 20, 30, 40, 10],
            }
        )
    )


@pytest.mark.parametrize("name", ["comma.csv", "semicolon.csv"])
def test_separators_give_same_columns(name: str) -> None:
    frame = DataSession.from_csv(SAMPLES / name).raw
    assert list(frame.columns) == ["city", "price", "rooms"]
    assert len(frame) == 4


def test_bad_row_is_controlled_error() -> None:
    with pytest.raises(CsvLoadError, match="Wadliwy wiersz"):
        DataSession.from_csv(SAMPLES / "bad_row.csv")


def test_empty_and_missing_file(tmp_path: Path) -> None:
    empty = tmp_path / "empty.csv"
    empty.write_text("")
    header_only = tmp_path / "header.csv"
    header_only.write_text("a,b\n")
    for path in (empty, header_only, tmp_path / "nope.csv"):
        with pytest.raises(CsvLoadError):
            DataSession.from_csv(path)


def test_cp1250_file_loads(tmp_path: Path) -> None:
    path = tmp_path / "pl.csv"
    path.write_bytes("miasto;cena\nŁódź;10\n".encode("cp1250"))
    assert DataSession.from_csv(path).raw.loc[0, "miasto"] == "Łódź"


def test_only_full_duplicates_removed() -> None:
    session = make_session()
    assert session.drop_duplicates() == 1  # wiersze 0 i 4 są identyczne
    assert len(session.current) == 4
    assert len(session.raw) == 5  # surowe dane nietknięte


def test_median_fill_changes_only_target_column() -> None:
    session = make_session()
    other = session.current[["b", "c"]].copy()
    assert session.fill_missing("a", "median") == 1
    assert session.current.loc[2, "a"] == 1.5
    pd.testing.assert_frame_equal(session.current[["b", "c"]], other)


def test_mode_fill_text_and_drop_strategy() -> None:
    session = make_session()
    assert session.fill_missing("b", "mode") == 1
    assert session.current["b"].isna().sum() == 0
    session.reset()
    assert session.fill_missing("a", "drop") == 1
    assert len(session.current) == 4


def test_numeric_strategy_on_text_column_rejected() -> None:
    with pytest.raises(ValueError, match="nie jest liczbowa"):
        make_session().fill_missing("b", "mean")


def test_range_rule_detects_without_changing() -> None:
    session = make_session()
    mask = session.range_mask("c", 0, 25)
    assert mask.tolist() == [False, False, True, True, False]
    pd.testing.assert_frame_equal(session.current, session.raw)
    assert session.apply_range_rule("c", 0, 25, action="nan") == 2
    assert session.current["c"].isna().sum() == 2


def test_invalid_range_parameters() -> None:
    with pytest.raises(ValueError, match="większa od górnej"):
        make_session().range_mask("c", 50, 10)


def test_iqr_flags_controlled_outlier() -> None:
    session = DataSession(pd.DataFrame({"v": [10, 11, 12, 13, 14, 100]}))
    assert session.handle_outliers("v", action="flag") == 1
    assert session.current["v_outlier"].tolist() == [False] * 5 + [True]
    assert len(session.current) == 6  # oznaczenie niczego nie usuwa


def test_constant_column_has_no_outliers() -> None:
    session = DataSession(pd.DataFrame({"v": [5, 5, 5, 5]}))
    assert not session.iqr_mask("v").any()


def test_reset_and_audit_log() -> None:
    session = make_session()
    session.drop_duplicates()
    session.fill_missing("a", "mean")
    session.reset()
    pd.testing.assert_frame_equal(session.current, session.raw)
    log = session.audit_frame()
    assert log["operation"].tolist() == ["usunięcie duplikatów", "braki: mean", "reset do danych surowych"]
    assert log.loc[0, "rows_before"] == 5 and log.loc[0, "rows_after"] == 4


def test_pipeline_is_repeatable() -> None:
    first, second = make_session(), make_session()
    run_pipeline(first)
    run_pipeline(second)
    pd.testing.assert_frame_equal(first.current, second.current)
    assert first.current[["a", "b", "c"]].isna().sum().sum() == 0


def test_exported_csv_reloads(tmp_path: Path) -> None:
    session = make_session()
    run_pipeline(session)
    out = tmp_path / "cleaned.csv"
    session.current.to_csv(out, index=False)
    reloaded = DataSession.from_csv(out).raw
    assert reloaded.shape == session.current.shape
