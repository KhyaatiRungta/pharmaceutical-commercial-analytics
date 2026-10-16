# SQL analytics layer

The same commercial questions the Excel workbook, Power BI model and HTML
dashboard answer — written as SQL over the prepared fact table.

## Run everything

```bash
python scripts/04_sql_analytics.py     # builds data/pharma_sales.db and runs all queries
```

Or interactively with the sqlite3 CLI after building the db:

```bash
sqlite3 data/pharma_sales.db
> .mode column
> .headers on
> .read sql/03_category_league_table.sql
```

## Files

| File | Business question it answers | Mirrors |
|---|---|---|
| `01_schema.sql` | Table DDL (`fact_sales`, `hour_profile`) + indexes | `data/Data_Dictionary.md` |
| `02_kpi_overview.sql` | Headline KPIs: units, est. revenue/profit/margin, trading days, busiest weekday, peak hour | KPI cards |
| `03_category_league_table.sql` | Which categories sell best — rank, share, like-for-like YoY, outperform flags | Category league table |
| `04_like_for_like_yoy.sql` | Is the business growing — 2019 YTD vs same window of 2018, monthly variance, full-year YoY with partial-year guard | Trend & variance chart |
| `05_time_patterns.sql` | Month × year matrix, seasonality index, weekday pattern, quarter × year | Time Analysis sheet |
| `06_trading_hour_heatmap.sql` | Weekday × hour average-units matrix + peak/trough hours | Trading-hour heatmap |

## Techniques showcased

- **Window functions** — `RANK()` for category rank, `LAG()` for year-over-year,
  rolling sums
- **Like-for-like logic** — `CASE WHEN Date BETWEEN …` windows so 2019
  (partial year, ends 8 Oct) is compared with the identical 1 Jan–8 Oct window
  of 2018, never a misleading full-year vs full-year
- **Conditional aggregation** — pivot-style month×year and weekday×hour
  matrices (`SUM(CASE WHEN … END)`)
- **Flags & segmentation** — `CASE WHEN` outperform flags vs the average
  category profit

## Caveats (same as the rest of the project)

- `Units` are **real** source values; all `Est*` euro columns are
  **estimates** (units × assumed unit price and margin — see
  `data/Data_Dictionary.md`).
- 2019 is a **partial year** (data ends 8 Oct): use the like-for-like queries,
  not plain year-over-year, when 2019 is in scope.
- Dialect: verified on **SQLite**; core statements are ANSI and run on
  PostgreSQL / MySQL 8 / SQL Server with the type substitutions noted in
  `01_schema.sql` (dates are ISO strings in SQLite, `DATE` elsewhere).
