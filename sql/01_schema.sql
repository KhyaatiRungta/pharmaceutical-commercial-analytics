-- =====================================================================
-- Pharmaceutical Commercial Analytics — schema (SQLite)
-- Mirrors data/pharma_sales_fact.csv and data/hour_profile.csv.
-- Load with: python scripts/04_sql_analytics.py
-- Dialect notes: verified on SQLite (Python 3.12); core SQL is ANSI.
--   PostgreSQL : TEXT -> VARCHAR, Date -> DATE, REAL stays DOUBLE PRECISION
--   SQL Server : TEXT -> NVARCHAR(...), Date -> DATE, add GO between stmts
-- =====================================================================

DROP TABLE IF EXISTS fact_sales;
CREATE TABLE fact_sales (
    Date           TEXT    NOT NULL,  -- ISO yyyy-mm-dd (2014-01-02 .. 2019-10-08)
    Year           INTEGER NOT NULL,  -- 2019 is a PARTIAL year (ends 8 Oct)
    MonthNum       INTEGER NOT NULL,  -- 1..12
    MonthName      TEXT    NOT NULL,  -- Jan..Dec
    Quarter        TEXT    NOT NULL,  -- Q1..Q4
    YearMonth      TEXT    NOT NULL,  -- yyyy-mm
    Weekday        TEXT    NOT NULL,  -- Monday..Sunday
    ATCCode        TEXT    NOT NULL,  -- M01AB .. R06
    Category       TEXT    NOT NULL,  -- display name
    TherapyArea    TEXT    NOT NULL,  -- plain-English therapy description
    Units          REAL    NOT NULL,  -- REAL source values
    UnitPrice      REAL    NOT NULL,  -- assumed average price (EUR)   - estimate
    EstRevenue     REAL    NOT NULL,  -- Units * UnitPrice             - estimate
    EstCost        REAL    NOT NULL,  -- EstRevenue * (1 - margin)     - estimate
    EstGrossProfit REAL    NOT NULL,  -- EstRevenue - EstCost          - estimate
    MarginPct      REAL    NOT NULL   -- assumed margin rate in pp (30.0 = 30%)
);

CREATE INDEX idx_fact_date   ON fact_sales(Date);
CREATE INDEX idx_fact_cat    ON fact_sales(Category);
CREATE INDEX idx_fact_year   ON fact_sales(Year);
CREATE INDEX idx_fact_weekday ON fact_sales(Weekday);

DROP TABLE IF EXISTS hour_profile;
CREATE TABLE hour_profile (
    Weekday       TEXT    NOT NULL,   -- Monday..Sunday
    WeekdayNum    INTEGER NOT NULL,   -- 0 = Monday .. 6 = Sunday
    Hour          INTEGER NOT NULL,   -- 0..23
    AvgUnits      REAL    NOT NULL,   -- average real units per weekday-hour
    AvgEstRevenue REAL    NOT NULL,   -- estimated revenue equivalent
    PRIMARY KEY (WeekdayNum, Hour)
);
