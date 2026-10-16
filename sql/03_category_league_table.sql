-- =====================================================================
-- 03 — Category league table (mirrors the dashboard's performance table)
-- Rank, share, like-for-like YoY and outperform flags for the 8 ATC groups.
-- =====================================================================

WITH cat AS (
    SELECT
        Category,
        SUM(Units)          AS units,
        SUM(EstRevenue)     AS revenue,
        SUM(EstGrossProfit) AS profit
    FROM fact_sales
    GROUP BY Category
),
lfl AS (                              -- like-for-like windows (2019 is partial)
    SELECT
        Category,
        SUM(CASE WHEN Date BETWEEN '2019-01-01' AND '2019-10-08'
                 THEN EstRevenue END) AS rev_2019_ytd,
        SUM(CASE WHEN Date BETWEEN '2018-01-01' AND '2018-10-08'
                 THEN EstRevenue END) AS rev_2018_window
    FROM fact_sales
    GROUP BY Category
),
avg_profit AS (                       -- average profit across the 8 categories
    SELECT AVG(p) AS avg_p FROM (SELECT SUM(EstGrossProfit) AS p
                                 FROM fact_sales GROUP BY Category)
)
SELECT
    c.Category,
    ROUND(c.units, 1)                                   AS units_real,
    ROUND(c.revenue, 0)                                 AS est_revenue_eur,
    ROUND(c.profit, 0)                                  AS est_profit_eur,
    ROUND(100.0 * c.profit / c.revenue, 1)              AS margin_pct,
    ROUND(100.0 * c.revenue / (SELECT SUM(EstRevenue) FROM fact_sales), 1)
                                                        AS revenue_share_pct,
    RANK() OVER (ORDER BY c.revenue DESC)               AS revenue_rank,
    ROUND(100.0 * (l.rev_2019_ytd / l.rev_2018_window - 1), 1)
                                                        AS lfl_yoy_pct,
    CASE WHEN c.profit >= (SELECT avg_p FROM avg_profit)
         THEN 'Outperforming' ELSE 'Below Average' END  AS profit_flag
FROM cat c
JOIN lfl l ON l.Category = c.Category
WHERE l.rev_2018_window > 0
ORDER BY c.revenue DESC;
