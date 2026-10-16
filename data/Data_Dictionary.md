# Data Dictionary

All figures derived from the Kaggle **"Pharma sales data"** dataset
(Milan Zdravković, CC BY-NC 4.0) — 2014-01-02 to 2019-10-08, one pharmacy,
8 Anatomical Therapeutic Chemical (ATC) drug groups.

**Units are real source values. All € figures are estimates**
(units × assumed average unit price; cost = estimated revenue × (1 − assumed
margin)). See the assumptions table below and the README sheet of the Excel
workbook.

---

## `data/pharma_sales_fact.csv` (16,848 rows)

One row = one day × one ATC category. Produced by
`scripts/01_prepare_kaggle_data.py` from `data/kaggle_raw/salesdaily.csv`.

| Column | Type | Description |
|---|---|---|
| Date | date | Trading day (2014-01-02 … 2019-10-08; 2,106 distinct days) |
| Year | int | Calendar year (2019 is a **partial year**, ends 8 Oct) |
| MonthNum | int | 1–12 |
| MonthName | text | Jan … Dec |
| Quarter | text | Q1–Q4 |
| YearMonth | text | e.g. 2016-07 |
| Weekday | text | Monday … Sunday |
| ATCCode | text | M01AB, M01AE, N02BA, N02BE, N05B, N05C, R03, R06 |
| Category | text | Display name (NSAIDs-Acetic … Antihistamines) |
| TherapyArea | text | Plain-English description of the ATC group |
| Units | decimal | **Real** quantity sold in the pharmacy's POS system |
| UnitPrice | decimal | **Assumed** average selling price per unit (EUR) |
| EstRevenue | decimal | **Estimated** = Units × UnitPrice |
| EstCost | decimal | **Estimated** = EstRevenue × (1 − margin rate) |
| EstGrossProfit | decimal | **Estimated** = EstRevenue − EstCost |
| MarginPct | decimal | Assumed gross-margin rate in percentage points (e.g. 30.0) |

## `data/hour_profile.csv` (168 rows)

Average units sold per weekday × hour of day, aggregated from
`saleshourly.csv`. Used for the trading-hour heatmap (Power BI matrix /
HTML dashboard). **Not** cross-filtered by slicers — it is a whole-period
average profile.

| Column | Description |
|---|---|
| Weekday | Monday … Sunday |
| WeekdayNum | 0 = Monday … 6 = Sunday |
| Hour | 0–23 |
| AvgUnits | Average real units per occurrence of that weekday-hour |
| AvgEstRevenue | Same, converted with the price assumptions (estimated) |

## `data/pharma_sales.db` (generated — not committed)

SQLite database built from the two CSVs above by
`scripts/04_sql_analytics.py` (it executes `sql/01_schema.sql`, loads the
CSVs, then runs every query in `sql/`). Tables `fact_sales` and
`hour_profile` mirror the CSV columns exactly. Rebuild any time with:

```bash
python scripts/04_sql_analytics.py
```

## Assumptions applied (documented, adjustable in `01_prepare_kaggle_data.py`)

| ATC | Category | Therapy area | €/unit | Margin |
|---|---|---|---|---|
| M01AB | NSAIDs-Acetic | Anti-inflammatory, acetic acid derivatives (e.g. diclofenac) | 3.10 | 30% |
| M01AE | NSAIDs-Propionic | Anti-inflammatory, propionic acid derivatives (e.g. ibuprofen) | 3.60 | 30% |
| N02BA | Salicylates | Analgesics/antipyretics, salicylic acid (e.g. aspirin) | 2.80 | 28% |
| N02BE | Paracetamol | Analgesics/antipyretics, anilides (e.g. paracetamol) | 2.40 | 26% |
| N05B | Anxiolytics | Psycholeptics, anxiolytic drugs | 6.90 | 34% |
| N05C | Hypnotics | Psycholeptics, hypnotics and sedatives | 7.40 | 34% |
| R03 | Anti-Asthmatics | Drugs for obstructive airway diseases (asthma/COPD) | 16.50 | 22% |
| R06 | Antihistamines | Antihistamines for systemic use | 8.20 | 32% |

## Raw Kaggle files kept in `data/kaggle_raw/`

| File | Grain | Rows | Notes |
|---|---|---|---|
| saleshourly.csv | hour × category (wide) | ~50k | Source of the hour profile |
| salesdaily.csv | day × category (wide) | 2,106 | Source of the fact table |
| salesweekly.csv | week × category | ~313 | Kept for reference |
| salesmonthly.csv | month × category | 71 | Partial Dec-2019 row excluded |

## Totals (sanity check)

- Units: **127,596** (real)
- Estimated revenue: **€616,028**
- Estimated gross profit: **€169,500** (27.5%)
