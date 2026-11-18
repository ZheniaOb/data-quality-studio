# Raport jakości danych – housing_dirty.csv

## Podsumowanie przed / po

```
                 przed    po
rekordy           2030  2000
kolumny             10    15
pełne duplikaty     30     0
puste komórki      141     0
```

## Profil danych surowych

```
                      dtype  missing  missing_pct  unique
longitude           float64        0         0.00     862
latitude            float64        0         0.00     833
housing_median_age    int64        0         0.00      54
total_rooms         float64        0         0.00    1772
total_bedrooms      float64       61         3.00    1194
population          float64        0         0.00    1633
households            int64        0         0.00    1086
median_income       float64       40         1.97    1927
median_house_value  float64        0         0.00    1976
ocean_proximity         str       40         1.97       5
```

## Statystyki opisowe (dane surowe)

```
                     count unique        top freq           mean           std      min       25%       50%       75%       max
longitude           2030.0    NaN        NaN  NaN    -119.241759      2.876666  -124.29    -121.7  -119.185   -116.81    -114.3
latitude            2030.0    NaN        NaN  NaN       37.49032      4.286204     32.6     34.96     37.41     39.61      99.0
housing_median_age  2030.0    NaN        NaN  NaN       29.50936     54.920173     -1.0      13.0      27.0      40.0     999.0
total_rooms         2030.0    NaN        NaN  NaN    4258.812808   2419.614826    245.0   2228.25    4156.0    6178.0   10319.0
total_bedrooms      1969.0    NaN        NaN  NaN     847.799898     500.50889     41.0     436.0     812.0    1215.0    2377.0
population          2030.0    NaN        NaN  NaN    2471.757635   2886.781644    114.0    1219.0    2278.0    3324.5   78075.0
households          2030.0    NaN        NaN  NaN     774.850246    420.080795     51.0     410.0     776.0    1144.5    1498.0
median_income       1990.0    NaN        NaN  NaN        4.03998      1.976856     -3.0   2.59945   3.72745  5.135175   14.1737
median_house_value  2030.0    NaN        NaN  NaN  163939.848276  83958.359712  15000.0  105073.0  154901.0  211361.5  500001.0
ocean_proximity       1990      5  <1H OCEAN  866            NaN           NaN      NaN       NaN       NaN       NaN       NaN
```

## Wykryte problemy (reguły jakości, przed czyszczeniem)

```
                               reguła             kolumna  liczba rekordów
0                     pełne duplikaty       (cały wiersz)               30
1      poza zakresem [-124.5, -114.0]           longitude                0
2          poza zakresem [32.5, 42.0]            latitude                6
3               poza zakresem [1, 52]  housing_median_age               14
4              poza zakresem [1, inf]         total_rooms                0
5              poza zakresem [0, inf]      total_bedrooms                0
6              poza zakresem [1, inf]          population                0
7              poza zakresem [1, inf]          households                0
8     poza zakresem [0.4999, 15.0001]       median_income                4
9       poza zakresem [14999, 500001]  median_house_value                0
10  outlier IQR×1.5 [-3696, 1.21e+04]         total_rooms                0
11     outlier IQR×1.5 [-732.5, 2384]      total_bedrooms                0
12      outlier IQR×1.5 [-1939, 6483]          population               10
13     outlier IQR×1.5 [-691.8, 2246]          households                0
14    outlier IQR×1.5 [-1.204, 8.939]       median_income               51
```

## Ślad zmian (kolejne operacje)

```
                   time             operation                                                    params  rows_before  rows_after  affected
0   2026-11-18T12:36:25  usunięcie duplikatów                                        klucz=pełny wiersz         2030        2000        30
1   2026-11-18T12:36:25           zakres: nan                       kolumna=longitude, [-124.5, -114.0]         2000        2000         0
2   2026-11-18T12:36:25           zakres: nan                            kolumna=latitude, [32.5, 42.0]         2000        2000         6
3   2026-11-18T12:36:25           zakres: nan                       kolumna=housing_median_age, [1, 52]         2000        2000        13
4   2026-11-18T12:36:25           zakres: nan                             kolumna=total_rooms, [1, inf]         2000        2000         0
5   2026-11-18T12:36:25           zakres: nan                          kolumna=total_bedrooms, [0, inf]         2000        2000         0
6   2026-11-18T12:36:25           zakres: nan                              kolumna=population, [1, inf]         2000        2000         0
7   2026-11-18T12:36:25           zakres: nan                              kolumna=households, [1, inf]         2000        2000         0
8   2026-11-18T12:36:25           zakres: nan                  kolumna=median_income, [0.4999, 15.0001]         2000        2000         4
9   2026-11-18T12:36:25           zakres: nan               kolumna=median_house_value, [14999, 500001]         2000        2000         0
10  2026-11-18T12:36:25         braki: median                           kolumna=latitude, wartość=37.39         2000        2000         6
11  2026-11-18T12:36:25         braki: median                  kolumna=housing_median_age, wartość=27.0         2000        2000        13
12  2026-11-18T12:36:25         braki: median                     kolumna=total_bedrooms, wartość=810.0         2000        2000        60
13  2026-11-18T12:36:25         braki: median                    kolumna=median_income, wartość=3.72705         2000        2000        44
14  2026-11-18T12:36:25           braki: mode                kolumna=ocean_proximity, wartość=<1H OCEAN         2000        2000        40
15  2026-11-18T12:36:25        outliery: flag  kolumna=total_rooms, IQR×1.5, granice=[-3749, 1.211e+04]         2000        2000         0
16  2026-11-18T12:36:25        outliery: flag   kolumna=total_bedrooms, IQR×1.5, granice=[-691.5, 2336]         2000        2000         3
17  2026-11-18T12:36:25        outliery: flag        kolumna=population, IQR×1.5, granice=[-1973, 6502]         2000        2000        10
18  2026-11-18T12:36:25        outliery: flag       kolumna=households, IQR×1.5, granice=[-695.9, 2245]         2000        2000         0
19  2026-11-18T12:36:25        outliery: flag    kolumna=median_income, IQR×1.5, granice=[-1.029, 8.77]         2000        2000        53
```

## Braki w kolumnach przed / po

```
                        braki przed  braki po
households                        0         0
households_outlier                0         0
housing_median_age                0         0
latitude                          0         0
longitude                         0         0
median_house_value                0         0
median_income                    40         0
median_income_outlier             0         0
ocean_proximity                  40         0
population                        0         0
population_outlier                0         0
total_bedrooms                   61         0
total_bedrooms_outlier            0         0
total_rooms                       0         0
total_rooms_outlier               0         0
```

## Statystyki opisowe (po czyszczeniu)

```
                         count unique        top  freq         mean           std      min       25%       50%       75%       max
longitude               2000.0    NaN        NaN   NaN   -119.23999      2.885181  -124.29    -121.7   -119.18   -116.79    -114.3
latitude                2000.0    NaN        NaN   NaN    37.306155      2.677108     32.6     34.95     37.39   39.5625      41.9
housing_median_age      2000.0    NaN        NaN   NaN      26.7195     15.004312      1.0      14.0      27.0      40.0      52.0
total_rooms             2000.0    NaN        NaN   NaN    4253.8615   2418.570651    245.0    2198.5    4156.0   6163.25   10319.0
total_bedrooms          2000.0    NaN        NaN   NaN      844.857     492.33685     41.0     444.0     810.0    1201.0    2377.0
population              2000.0    NaN        NaN   NaN     2472.085   2904.798225    114.0   1204.75    2280.0    3323.5   78075.0
households              2000.0    NaN        NaN   NaN      774.316    420.555979     51.0     407.0     776.0   1142.25    1498.0
median_income           2000.0    NaN        NaN   NaN     4.042232       1.92529      0.5   2.64545   3.72705  5.095375   14.1737
median_house_value      2000.0    NaN        NaN   NaN  163846.4505  83558.532152  15000.0  105176.5  154901.0  211330.5  500001.0
ocean_proximity           2000      5  <1H OCEAN   895          NaN           NaN      NaN       NaN       NaN       NaN       NaN
total_rooms_outlier       2000      1      False  2000          NaN           NaN      NaN       NaN       NaN       NaN       NaN
total_bedrooms_outlier    2000      2      False  1997          NaN           NaN      NaN       NaN       NaN       NaN       NaN
population_outlier        2000      2      False  1990          NaN           NaN      NaN       NaN       NaN       NaN       NaN
households_outlier        2000      1      False  2000          NaN           NaN      NaN       NaN       NaN       NaN       NaN
median_income_outlier     2000      2      False  1947          NaN           NaN      NaN       NaN       NaN       NaN       NaN
```
