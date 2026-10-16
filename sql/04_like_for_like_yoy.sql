-- =====================================================================
-- 04 — Like-for-like YoY growth (mirrors the trend & variance chart)
-- 2019 is a PARTIAL year (data ends 8 Oct): its comparison window is
-- 1 Jan - 8 Oct 2018, never a full year vs full year.
-- =====================================================================

-- Headline: like-for-like totals for revenue, profit and units
SELECT
    ROUND(100.0 * (cur.rev / pri.rev - 1), 1)       AS revenue_lfl_yoy_pct,
    ROUND(100.0 * (cur.profit / pri.profit - 1), 1) AS profit_lfl_yoy_pct,
    ROUND(100.0 * (cur.units / pri.units - 1), 1)   AS units_lfl_yoy_pct,
    ROUND(100.0 * (cur.profit / cur.rev - pri.profit / pri.rev), 1)
                                                    AS margin_delta_pp
FROM (
    SELECT SUM(CASE WHEN Date BETWEEN '2019-01-01' AND '2019-10-08' THEN EstRevenue     END) AS rev,
           SUM(CASE WHEN Date BETWEEN '2019-01-01' AND '2019-10-08' THEN EstGrossProfit END) AS profit,
           SUM(CASE WHEN Date BETWEEN '2019-01-01' AND '2019-10-08' THEN Units          END) AS units
    FROM fact_sales
) cur, (
    SELECT SUM(CASE WHEN Date BETWEEN '2018-01-01' AND '2018-10-08' THEN EstRevenue     END) AS rev,
           SUM(CASE WHEN Date BETWEEN '2018-01-01' AND '2018-10-08' THEN EstGrossProfit END) AS profit,
           SUM(CASE WHEN Date BETWEEN '2018-01-01' AND '2018-10-08' THEN Units          END) AS units
    FROM fact_sales
) pri;

-- Monthly variance 2019 vs 2018 (source of the +/- labels on the trend chart)
SELECT
    m.MonthNum,
    m.MonthName,
    ROUND(m.rev, 0)                                   AS rev_2019,
    ROUND(p.rev, 0)                                   AS rev_2018,
    ROUND(m.rev - p.rev, 0)                           AS variance_eur,
    ROUND(100.0 * (m.rev / p.rev - 1), 1)             AS variance_pct
FROM (SELECT MonthNum, MonthName, SUM(EstRevenue) AS rev
      FROM fact_sales WHERE Year = 2019  GROUP BY MonthNum, MonthName) m
JOIN (SELECT MonthNum, SUM(EstRevenue) AS rev
      FROM fact_sales WHERE Year = 2018  GROUP BY MonthNum) p
  ON p.MonthNum = m.MonthNum
WHERE p.rev > 0
ORDER BY m.MonthNum;

-- Full-year YoY with a partial-year guard (LAG over complete years only)
WITH yearly AS (
    SELECT Year, SUM(EstRevenue) AS rev
    FROM fact_sales
    WHERE Year < 2019                       -- exclude the partial year here
    GROUP BY Year
)
SELECT
    Year,
    ROUND(rev, 0)                                        AS est_revenue_eur,
    ROUND(100.0 * (rev / LAG(rev) OVER (ORDER BY Year) - 1), 1)
                                                         AS yoy_pct,
    'full year'                                          AS period_type
FROM yearly
UNION ALL
SELECT
    2019,
    (SELECT ROUND(SUM(EstRevenue), 0) FROM fact_sales WHERE Year = 2019),
    NULL,
    'partial year to 8 Oct - use like-for-like above'
ORDER BY Year;
