-- =====================================================================
-- 02 — Headline KPI overview (mirrors the dashboard's KPI cards)
-- Units are REAL; Est* euro figures are estimates.
-- =====================================================================

-- KPI cards: revenue, gross profit, margin, units, trading days
SELECT
    COUNT(DISTINCT Date)                                   AS trading_days,
    ROUND(SUM(Units), 1)                                   AS units_sold_real,
    ROUND(SUM(EstRevenue), 0)                              AS est_revenue_eur,
    ROUND(SUM(EstCost), 0)                                 AS est_cost_eur,
    ROUND(SUM(EstGrossProfit), 0)                          AS est_gross_profit_eur,
    ROUND(100.0 * SUM(EstGrossProfit) / SUM(EstRevenue), 1) AS gross_margin_pct,
    ROUND(SUM(Units) / COUNT(DISTINCT Date), 1)            AS avg_units_per_trading_day,
    MIN(Date)                                              AS first_day,
    MAX(Date)                                              AS last_day
FROM fact_sales;

-- Secondary strip: baseline year, latest full year, busiest weekday
SELECT 'Baseline full year (2014)' AS metric,
       ROUND(SUM(EstRevenue), 0)   AS value_eur
FROM fact_sales
WHERE Year = 2014
UNION ALL
SELECT 'Latest full year (2018)', ROUND(SUM(EstRevenue), 0)
FROM fact_sales
WHERE Year = 2018;

-- Busiest weekday by estimated revenue
SELECT Weekday,
       ROUND(SUM(EstRevenue), 0)                              AS revenue_eur,
       ROUND(100.0 * SUM(EstRevenue)
             / (SELECT SUM(EstRevenue) FROM fact_sales), 1)   AS revenue_share_pct
FROM fact_sales
GROUP BY Weekday
ORDER BY revenue_eur DESC
LIMIT 3;
