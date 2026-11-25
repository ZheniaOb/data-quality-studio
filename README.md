# Studio jakości i wizualizacji danych

Projekt 2 z Programowania V. Aplikacja prowadzi od wczytania CSV, przez diagnozę i czyszczenie danych, do wizualizacji i eksportu.

**Stan:**
- Lab 6 gotowy: profil danych, reguły jakości, pipeline czyszczenia, raport przed/po, `cleaned.csv`.
- Lab 7 gotowy: cztery typy wykresów przed/po, walidacja typów kolumn, korelacja z interpretacją, eksport PNG/SVG/PDF.
- Lab 8–9 (GUI, osadzenie wykresu) w przygotowaniu.

## Instalacja

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Uruchomienie (Lab 6)

```powershell
python data/make_sample.py                  # syntetyczny brudny zbiór -> data/housing_dirty.csv
python lab6_clean.py data/housing_dirty.csv # -> output/cleaned.csv, output/report.md, output/audit_log.csv
python lab6_clean.py <plik.csv> --missing drop --out output_drop
python lab7_plots.py data/housing_dirty.csv # -> output/plots/*.png|svg, correlation_*.png, correlation.md
python -m pytest                            # testy logiki i wykresów
```

Gdy prowadząca udostępni referencyjny zbiór California Housing, wystarczy podać jego ścieżkę zamiast `data/housing_dirty.csv`.

## Struktura

| Plik | Rola |
|---|---|
| `studio/session.py` | `DataSession`: dane surowe (`raw`, nigdy nie zmieniane), bieżące (`current`) i dziennik operacji. Bez zależności od GUI. |
| `studio/plots.py` | Wykresy zwracające `Figure` (bez pyplot): `build_figure(frame, kind, x, y, hue)`, `compare_figure` (przed/po), korelacja, `save_figure`. Walidacja typów kolumn. |
| `lab6_clean.py` | Skrypt Lab 6: reguły dla California Housing, pipeline, raport. |
| `lab7_plots.py` | Skrypt Lab 7: zestaw wykresów przed/po i raport korelacji. |
| `data/make_sample.py` | Generator syntetycznych danych z celowymi błędami (ziarno 42). |
| `data/samples/` | Małe pliki testowe: przecinek, średnik, wadliwy wiersz. |
| `tests/test_session.py` | Testy na małych, ręcznie kontrolowanych DataFrame. |

## Reguły i uzasadnienie strategii

Kolejność pipeline'u: **duplikaty → wartości błędne → braki → outliery**.

1. **Duplikaty** – usuwane są tylko pełne duplikaty (identyczny cały wiersz). Opcjonalnie można podać klucz (`subset`).
2. **Wartości poza zakresem** – zakresy w `RANGE_RULES` (np. `latitude` 32.5–42, `housing_median_age` 1–52, `median_income` 0.5–15). Wartość spoza zakresu to błąd pomiaru, więc zamieniana jest na brak (NaN), a reszta rekordu zostaje. Dostępne też `clip` i `drop`. Wykrywanie (`range_mask`) niczego nie zmienia; zmiana następuje tylko przez jawne `apply_range_rule`.
3. **Braki** – domyślnie liczby uzupełniane medianą (jest odporna na outliery, w przeciwieństwie do średniej), tekst – modą. Alternatywnie `--missing drop` usuwa rekordy z brakami, a `mean` uzupełnia średnią. Każda operacja zmienia tylko swoją kolumnę.
4. **Outliery** – metoda IQR (poza `[Q1 − 1.5·IQR, Q3 + 1.5·IQR]`). Są tylko **oznaczane** kolumną `<kolumna>_outlier`, nie usuwane: duża populacja czy wysoki dochód to zwykle prawdziwe dzielnice, a nie błędy. Przycinanie (`clip`) i usuwanie (`drop`) są dostępne, ale wymagają jawnej decyzji. Dla kolumny stałej (IQR = 0) nic nie jest oznaczane.

Każda operacja zapisuje w dzienniku czas, parametry, liczbę rekordów przed/po oraz liczbę rekordów/komórek, których dotyczyła. `reset()` przywraca dane surowe bez restartu programu. Wynik jest powtarzalny: pipeline jest deterministyczny (sprawdza to test).

## Wykresy (Lab 7)

| Typ | Parametry | Walidacja |
|---|---|---|
| histogram | `x` liczbowa | blokuje kolumnę tekstową, logiczną, pustą i stałą |
| scatter | `x`, `y` liczbowe (różne), `hue` kategoria | jak wyżej + r Pearsona w tytule |
| box | `x` liczbowa, `hue` opcjonalne grupowanie | wąsy = 1.5·IQR, ta sama reguła co outliery w Lab 6 |
| bar | `x` kategoria (≤ 30 wartości), `y` liczbowa → średnia, brak `y` → liczność | blokuje kolumny o zbyt wielu wartościach |

Każdy wykres ma tytuł i opisy osi. Niepoprawny wybór zgłasza `ValueError` z podpowiedzią (w GUI będzie to komunikat). Interpretacja korelacji (w tym zastrzeżenie, że korelacja ≠ przyczynowość) jest w `output/plots/correlation.md`.

## Znane ograniczenia

- Separator wykrywany z nagłówka (`,` albo `;`); kodowania: UTF-8, Windows-1250.
- `data/housing_dirty.csv` to dane syntetyczne, nie prawdziwy zbiór referencyjny.

## Źródła i narzędzia

- pandas, numpy, matplotlib, seaborn, pytest – dokumentacja oficjalna (linki w instrukcji projektu).
- Przy tworzeniu kodu korzystano z asystenta AI (Claude, Anthropic); kod został przeanalizowany i zrozumiany przez autora.

## Autorzy

- _(uzupełnij)_
