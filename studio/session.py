"""Model sesji danych: dane surowe, dane bieżące i dziennik operacji (niezależny od GUI)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from datetime import datetime
from pathlib import Path
from typing import Literal

import pandas as pd

ENCODINGS = ("utf-8-sig", "cp1250")
MissingStrategy = Literal["drop", "mean", "median", "mode", "constant"]
RangeAction = Literal["nan", "clip", "drop"]
OutlierAction = Literal["flag", "clip", "drop"]


class CsvLoadError(ValueError):
    """Błąd wczytywania pliku z komunikatem zrozumiałym dla użytkownika."""


def read_csv(path: Path | str) -> pd.DataFrame:
    """Wczytuje CSV; separator ',' lub ';' wykrywany z wiersza nagłówka."""
    path = Path(path)
    if not path.is_file():
        raise CsvLoadError(f"Nie znaleziono pliku: {path}")
    for encoding in ENCODINGS:
        try:
            with path.open(encoding=encoding) as handle:
                header = handle.readline()
            sep = ";" if header.count(";") > header.count(",") else ","
            frame = pd.read_csv(path, sep=sep, encoding=encoding)
        except UnicodeDecodeError:
            continue
        except pd.errors.EmptyDataError as exc:
            raise CsvLoadError("Plik jest pusty – wybierz plik z nagłówkiem i danymi.") from exc
        except pd.errors.ParserError as exc:
            raise CsvLoadError(
                f"Wadliwy wiersz w pliku: {str(exc).strip()}. Popraw liczbę pól w tym wierszu."
            ) from exc
        if frame.empty:
            raise CsvLoadError("Plik nie zawiera rekordów – dodaj dane pod nagłówkiem.")
        return frame
    raise CsvLoadError("Nieobsługiwane kodowanie pliku. Zapisz plik jako UTF-8.")


@dataclass(frozen=True)
class AuditEntry:
    time: str
    operation: str
    params: str
    rows_before: int
    rows_after: int
    affected: int  # rekordy usunięte / komórki zmienione / rekordy oznaczone


@dataclass
class DataSession:
    raw: pd.DataFrame
    current: pd.DataFrame = field(init=False)
    audit_log: list[AuditEntry] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.current = self.raw.copy(deep=True)

    @classmethod
    def from_csv(cls, path: Path | str) -> DataSession:
        return cls(read_csv(path))

    # ---------- profil ----------

    def summary(self) -> dict[str, int]:
        frame = self.current
        return {
            "rekordy": len(frame),
            "kolumny": frame.shape[1],
            "pełne duplikaty": int(frame.duplicated().sum()),
            "puste komórki": int(frame.isna().sum().sum()),
        }

    def profile(self) -> pd.DataFrame:
        frame = self.current
        return pd.DataFrame(
            {
                "dtype": frame.dtypes.astype(str),
                "missing": frame.isna().sum(),
                "missing_pct": frame.isna().mean().mul(100).round(2),
                "unique": frame.nunique(dropna=True),
            }
        )

    def describe(self) -> pd.DataFrame:
        return self.current.describe(include="all").T

    # ---------- reguły jakości (tylko wykrywanie, bez zmian danych) ----------

    def range_mask(self, column: str, low: float, high: float) -> pd.Series:
        if low > high:
            raise ValueError(f"Dolna granica ({low}) jest większa od górnej ({high}).")
        values = self._numeric(column)
        return values.notna() & ~values.between(low, high)

    def iqr_bounds(self, column: str, factor: float = 1.5) -> tuple[float, float]:
        if factor <= 0:
            raise ValueError("Współczynnik IQR musi być dodatni (zwykle 1.5 lub 3).")
        q1, q3 = self._numeric(column).quantile([0.25, 0.75])
        iqr = q3 - q1
        return q1 - factor * iqr, q3 + factor * iqr

    def iqr_mask(self, column: str, factor: float = 1.5) -> pd.Series:
        low, high = self.iqr_bounds(column, factor)
        if pd.isna(low) or low == high:
            return pd.Series(False, index=self.current.index)
        values = self.current[column]
        return (values < low) | (values > high)

    # ---------- operacje czyszczące (zmieniają tylko `current`) ----------

    def drop_duplicates(self, subset: list[str] | None = None) -> int:
        before = len(self.current)
        self.current = self.current.drop_duplicates(subset=subset).copy()
        removed = before - len(self.current)
        self._log("usunięcie duplikatów", f"klucz={subset or 'pełny wiersz'}", before, removed)
        return removed

    def fill_missing(
        self, column: str, strategy: MissingStrategy, value: float | str | None = None
    ) -> int:
        self._require(column)
        mask = self.current[column].isna()
        count = int(mask.sum())
        before = len(self.current)
        if strategy == "drop":
            self.current = self.current[~mask].copy()
            params = f"kolumna={column}"
        else:
            fill = self._fill_value(column, strategy, value)
            self.current[column] = self.current[column].fillna(fill)
            params = f"kolumna={column}, wartość={fill}"
        self._log(f"braki: {strategy}", params, before, count)
        return count

    def apply_range_rule(
        self, column: str, low: float, high: float, action: RangeAction = "nan"
    ) -> int:
        mask = self.range_mask(column, low, high)
        count = int(mask.sum())
        before = len(self.current)
        if action == "nan":
            self.current[column] = self.current[column].mask(mask)
        elif action == "clip":
            self.current[column] = self.current[column].clip(low, high)
        elif action == "drop":
            self.current = self.current[~mask].copy()
        else:
            raise ValueError(f"Nieznana akcja reguły zakresu: {action}")
        self._log(f"zakres: {action}", f"kolumna={column}, [{low}, {high}]", before, count)
        return count

    def handle_outliers(
        self, column: str, action: OutlierAction = "flag", factor: float = 1.5
    ) -> int:
        low, high = self.iqr_bounds(column, factor)
        mask = self.iqr_mask(column, factor)
        count = int(mask.sum())
        before = len(self.current)
        if action == "flag":
            self.current[f"{column}_outlier"] = mask
        elif action == "clip":
            self.current[column] = self.current[column].clip(low, high)
        elif action == "drop":
            self.current = self.current[~mask].copy()
        else:
            raise ValueError(f"Nieznana akcja dla outlierów: {action}")
        params = f"kolumna={column}, IQR×{factor}, granice=[{low:.4g}, {high:.4g}]"
        self._log(f"outliery: {action}", params, before, count)
        return count

    def reset(self) -> None:
        before = len(self.current)
        self.current = self.raw.copy(deep=True)
        self._log("reset do danych surowych", "-", before, 0)

    def audit_frame(self) -> pd.DataFrame:
        columns = [f.name for f in fields(AuditEntry)]
        return pd.DataFrame([asdict(entry) for entry in self.audit_log], columns=columns)

    # ---------- pomocnicze ----------

    def _require(self, column: str) -> None:
        if column not in self.current.columns:
            available = ", ".join(map(str, self.current.columns))
            raise ValueError(f"Brak kolumny '{column}'. Dostępne kolumny: {available}")

    def _numeric(self, column: str) -> pd.Series:
        self._require(column)
        if not pd.api.types.is_numeric_dtype(self.current[column]):
            raise ValueError(f"Kolumna '{column}' nie jest liczbowa – wybierz kolumnę liczbową.")
        return self.current[column]

    def _fill_value(
        self, column: str, strategy: MissingStrategy, value: float | str | None
    ) -> float | str:
        if strategy == "constant":
            if value is None:
                raise ValueError("Strategia 'constant' wymaga podania wartości.")
            return value
        if strategy == "mode":
            modes = self.current[column].mode(dropna=True)
            if modes.empty:
                raise ValueError(f"Kolumna '{column}' nie ma żadnej wartości do wyznaczenia mody.")
            return modes.iloc[0]
        if strategy in ("mean", "median"):
            stat = getattr(self._numeric(column), strategy)()
            if pd.isna(stat):
                raise ValueError(f"Kolumna '{column}' nie ma wartości liczbowych.")
            return float(stat)
        raise ValueError(f"Nieznana strategia braków: {strategy}")

    def _log(self, operation: str, params: str, rows_before: int, affected: int) -> None:
        self.audit_log.append(
            AuditEntry(
                time=datetime.now().isoformat(timespec="seconds"),
                operation=operation,
                params=params,
                rows_before=rows_before,
                rows_after=len(self.current),
                affected=affected,
            )
        )
