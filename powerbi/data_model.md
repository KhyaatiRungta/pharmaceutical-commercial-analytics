# Power BI — Data Model

Real Kaggle POS data (2014-01-02 → 2019-10-08), one pharmacy, 8 ATC categories.
Everything derives from `data/pharma_sales_fact.csv` (+ `data/hour_profile.csv`).

## Tables

| Table | Role | Grain | Created |
|---|---|---|---|
| **SalesData** | Fact | One day × one ATC category (16,848 rows) | Get data → CSV |
| **Date** | Date table (mark as date table) | One row/day, 2014-01-02 → 2019-10-08 | DAX below |
| **Category** | Dimension | 8 ATC groups + therapy text + assumptions | DAX below |
| **HourProfile** | Standalone matrix | Weekday × hour average units (168 rows) | Get data → CSV |
| **Metric** | Disconnected switcher | 3 rows: Revenue, Profit, Units | Enter data |

## Relationships

```
Date[Date]           1 ──── * SalesData[Date]
Category[Category]   1 ──── * SalesData[Category]
Metric[Metric]       (no relationships - slicer only)
HourProfile          (no relationships - heatmap visual only; slicers do NOT
                      cross-filter it, which is correct: it is an average
                      trading profile for the whole period)
```

Single-direction relationships, dimension → fact. **Mark `Date` as a date table**
(required for SAMEPERIODLASTYEAR / DATESBETWEEN in the LFL measures).

## DAX to create the tables

```dax
Date =
VAR MinD = DATE ( 2014, 1, 2 )
VAR MaxD = DATE ( 2019, 10, 8 )
RETURN
ADDCOLUMNS (
    CALENDAR ( MinD, MaxD ),
    "Year",          YEAR ( [Date] ),
    "MonthNo",       MONTH ( [Date] ),
    "MonthName",     FORMAT ( [Date], "mmm" ),
    "MonthSort",     YEAR ( [Date] ) * 100 + MONTH ( [Date] ),
    "Quarter",       "Q" & ROUNDUP ( MONTH ( [Date] ) / 3, 0 ),
    "YearMonth",     FORMAT ( [Date], "yyyy-mm" ),
    "Weekday",       FORMAT ( [Date], "dddd" ),
    "WeekdayNo",     WEEKDAY ( [Date], 2 ),
    "IsPartialYear", YEAR ( [Date] ) = 2019
)
```

```dax
Category =
SUMMARIZE (
    SalesData,
    SalesData[ATCCode],
    SalesData[Category],
    SalesData[TherapyArea]
)
```

`Metric` via **Enter data**: one column `Metric` with values `Revenue`, `Profit`, `Units`.

**Sort by column:** `MonthName` → `MonthNo`, `Weekday` → `WeekdayNo`.

## Power Query types

| Column | Type |
|---|---|
| Date | Date |
| Year, MonthNum, Units | Whole number |
| UnitPrice, EstRevenue, EstCost, EstGrossProfit | Decimal, currency EUR |
| MarginPct | Decimal (percent points: 26.0 = 26%) |
| rest | Text |

`HourProfile`: Weekday = text, WeekdayNum/Hours = whole number,
AvgUnits/EstRevenue = decimal.

## Caveats baked into the model

- **2019 is a partial year (ends 8 Oct)** — always use the `* LFL YoY %`
  measures for 2019 comparisons; the plain `FY YoY %` is valid for 2015–2018.
- EUR figures are **estimates** (units × assumed price; assumed margins).
  Units are real. Label cards accordingly.
