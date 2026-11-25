# Analiza korelacji

## Najsilniejsze pary – dane surowe

```
     kolumna 1          kolumna 2  r Pearsona  rho Spearmana                 siła
   total_rooms     total_bedrooms       0.961          0.971       silna dodatnia
   total_rooms         households       0.950          0.958       silna dodatnia
 median_income median_house_value       0.921          0.913       silna dodatnia
total_bedrooms         households       0.914          0.933       silna dodatnia
total_bedrooms         population       0.472          0.874 umiarkowana dodatnia
```

## Najsilniejsze pary – po czyszczeniu

```
     kolumna 1          kolumna 2  r Pearsona  rho Spearmana                 siła
   total_rooms         households       0.950          0.958       silna dodatnia
   total_rooms     total_bedrooms       0.942          0.953       silna dodatnia
 median_income median_house_value       0.922          0.906       silna dodatnia
total_bedrooms         households       0.898          0.918       silna dodatnia
    population         households       0.452          0.925 umiarkowana dodatnia
```

Skala siły |r|: ≥ 0.7 silna, 0.4–0.7 umiarkowana, 0.2–0.4 słaba, < 0.2 brak/bardzo słaba.

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
