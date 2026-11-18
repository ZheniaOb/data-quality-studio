"""Generuje syntetyczny „brudny” zbiór w układzie California Housing (do czasu otrzymania pliku od prowadzącej).

Problemy wprowadzane celowo (ziarno 42 => wynik powtarzalny):
braki liczbowe i tekstowe, 30 pełnych duplikatów, wartości poza zakresem, outliery.

Użycie: python data/make_sample.py  ->  data/housing_dirty.csv
"""

from pathlib import Path

import numpy as np
import pandas as pd

N = 2000
OUT = Path(__file__).with_name("housing_dirty.csv")


def main() -> None:
    rng = np.random.default_rng(42)
    households = rng.integers(50, 1500, N)
    rooms = (households * rng.uniform(4, 7, N)).round()
    income = rng.gamma(4, 1, N).clip(0.5, 15).round(4)
    df = pd.DataFrame(
        {
            "longitude": rng.uniform(-124.3, -114.3, N).round(2),
            "latitude": rng.uniform(32.6, 41.9, N).round(2),
            "housing_median_age": rng.integers(1, 53, N),
            "total_rooms": rooms,
            "total_bedrooms": (rooms * rng.uniform(0.15, 0.25, N)).round(),
            "population": (households * rng.uniform(2, 4, N)).round(),
            "households": households,
            "median_income": income,
            "median_house_value": (income * 40000 + rng.normal(0, 30000, N)).clip(15000, 500001).round(),
            "ocean_proximity": rng.choice(
                ["<1H OCEAN", "INLAND", "NEAR OCEAN", "NEAR BAY", "ISLAND"], N, p=[0.44, 0.32, 0.13, 0.109, 0.001]
            ),
        }
    )
    # braki
    for col, frac in [("total_bedrooms", 0.03), ("median_income", 0.02), ("ocean_proximity", 0.02)]:
        df.loc[rng.choice(N, int(N * frac), replace=False), col] = np.nan
    # wartości poza zakresem (błędy)
    df.loc[rng.choice(N, 8, replace=False), "housing_median_age"] = -1
    df.loc[rng.choice(N, 5, replace=False), "housing_median_age"] = 999
    df.loc[rng.choice(N, 6, replace=False), "latitude"] = 99.0
    df.loc[rng.choice(N, 4, replace=False), "median_income"] = -3.0
    # outliery (realne, ale skrajne)
    df.loc[rng.choice(N, 10, replace=False), "population"] *= 15
    # pełne duplikaty
    df = pd.concat([df, df.sample(30, random_state=1)], ignore_index=True)
    df.to_csv(OUT, index=False)
    print(f"Zapisano {OUT} ({len(df)} rekordow)")


if __name__ == "__main__":
    main()
