-- =====================================================================
-- 05 — Time patterns (mirrors the Time Analysis sheet)
-- Month x year matrix, seasonality index, weekday pattern, quarters.
-- =====================================================================

-- Month x year revenue matrix (pivot via conditional aggregation)
SELECT
    MonthNum,
    MonthName,
    ROUND(SUM(CASE WHEN Year = 2014 THEN EstRevenue END), 0) AS y2014,
    ROUND(SUM(CASE WHEN Year = 2015 THEN EstRevenue END), 0) AS y2015,
    ROUND(SUM(CASE WHEN Year = 2016 THEN EstRevenue END), 0) AS y2016,
    ROUND(SUM(CASE WHEN Year = 2017 THEN EstRevenue END), 0) AS y2017,
    ROUND(SUM(CASE WHEN Year = 2018 THEN EstRevenue END), 0) AS y2018,
    ROUND(SUM(CASE WHEN Year = 2019 THEN EstRevenue END), 0) AS y2019
FROM fact_sales
GROUP BY MonthNum, MonthName
ORDER BY MonthNum;

-- Seasonality index: average month across years / overall average month (1.00)
WITH ym AS (                                    -- revenue per year-month
    SELECT Year, MonthNum, SUM(EstRevenue) AS rev
    FROM fact_sales
    GROUP BY Year, MonthNum
),
mo AS (                                         -- mean per calendar month
    SELECT MonthNum, AVG(rev) AS avg_month_rev
    FROM ym GROUP BY MonthNum
)
SELECT
    MonthNum,
    ROUND(avg_month_rev, 0)                                            AS avg_month_eur,
    ROUND(avg_month_rev / (SELECT SUM(avg_month_rev) / 12 FROM mo), 2) AS seasonality_index
FROM mo
ORDER BY seasonality_index DESC
LIMIT 3;

-- Weekday pattern (Monday..Sunday) with revenue share
SELECT
    Weekday,
    ROUND(SUM(Units), 1)                                 AS units_real,
    ROUND(SUM(EstRevenue), 0)                            AS est_revenue_eur,
    ROUND(100.0 * SUM(EstRevenue)
          / (SELECT SUM(EstRevenue) FROM fact_sales), 1) AS revenue_share_pct
FROM fact_sales
GROUP BY Weekday
ORDER BY CASE Weekday WHEN 'Monday'    THEN 1 WHEN 'Tuesday'  THEN 2
                      WHEN 'Wednesday' THEN 3 WHEN 'Thursday' THEN 4
                      WHEN 'Friday'    THEN 5 WHEN 'Saturday' THEN 6
                      WHEN 'Sunday'    THEN 7 END;

-- Quarter x year matrix
SELECT
    Quarter,
    ROUND(SUM(CASE WHEN Year = 2014 THEN EstRevenue END), 0) AS y2014,
    ROUND(SUM(CASE WHEN Year = 2015 THEN EstRevenue END), 0) AS y2015,
    ROUND(SUM(CASE WHEN Year = 2016 THEN EstRevenue END), 0) AS y2016,
    ROUND(SUM(CASE WHEN Year = 2017 THEN EstRevenue END), 0) AS y2017,
    ROUND(SUM(CASE WHEN Year = 2018 THEN EstRevenue END), 0) AS y2018,
    ROUND(SUM(CASE WHEN Year = 2019 THEN EstRevenue END), 0) AS y2019
FROM fact_sales
GROUP BY Quarter
ORDER BY Quarter;
