-- =====================================================================
-- 06 — Trading-hour heatmap (mirrors the weekday x hour heatmap)
-- Hour data is a WEEKDAY profile (same hours repeat every week),
-- derived from the source's trading_hours column: 168 rows = 7 x 24.
-- =====================================================================

-- Weekday x hour matrix of average units (one column per trading hour)
SELECT
    Weekday,
    ROUND(MAX(CASE WHEN Hour =  0 THEN AvgUnits END), 1) AS h00,
    ROUND(MAX(CASE WHEN Hour =  1 THEN AvgUnits END), 1) AS h01,
    ROUND(MAX(CASE WHEN Hour =  2 THEN AvgUnits END), 1) AS h02,
    ROUND(MAX(CASE WHEN Hour =  3 THEN AvgUnits END), 1) AS h03,
    ROUND(MAX(CASE WHEN Hour =  4 THEN AvgUnits END), 1) AS h04,
    ROUND(MAX(CASE WHEN Hour =  5 THEN AvgUnits END), 1) AS h05,
    ROUND(MAX(CASE WHEN Hour =  6 THEN AvgUnits END), 1) AS h06,
    ROUND(MAX(CASE WHEN Hour =  7 THEN AvgUnits END), 1) AS h07,
    ROUND(MAX(CASE WHEN Hour =  8 THEN AvgUnits END), 1) AS h08,
    ROUND(MAX(CASE WHEN Hour =  9 THEN AvgUnits END), 1) AS h09,
    ROUND(MAX(CASE WHEN Hour = 10 THEN AvgUnits END), 1) AS h10,
    ROUND(MAX(CASE WHEN Hour = 11 THEN AvgUnits END), 1) AS h11,
    ROUND(MAX(CASE WHEN Hour = 12 THEN AvgUnits END), 1) AS h12,
    ROUND(MAX(CASE WHEN Hour = 13 THEN AvgUnits END), 1) AS h13,
    ROUND(MAX(CASE WHEN Hour = 14 THEN AvgUnits END), 1) AS h14,
    ROUND(MAX(CASE WHEN Hour = 15 THEN AvgUnits END), 1) AS h15,
    ROUND(MAX(CASE WHEN Hour = 16 THEN AvgUnits END), 1) AS h16,
    ROUND(MAX(CASE WHEN Hour = 17 THEN AvgUnits END), 1) AS h17,
    ROUND(MAX(CASE WHEN Hour = 18 THEN AvgUnits END), 1) AS h18,
    ROUND(MAX(CASE WHEN Hour = 19 THEN AvgUnits END), 1) AS h19,
    ROUND(MAX(CASE WHEN Hour = 20 THEN AvgUnits END), 1) AS h20,
    ROUND(MAX(CASE WHEN Hour = 21 THEN AvgUnits END), 1) AS h21,
    ROUND(MAX(CASE WHEN Hour = 22 THEN AvgUnits END), 1) AS h22,
    ROUND(MAX(CASE WHEN Hour = 23 THEN AvgUnits END), 1) AS h23,
    ROUND(AVG(AvgUnits), 1) AS avg_per_hour
FROM hour_profile
GROUP BY WeekdayNum, Weekday
ORDER BY WeekdayNum;

-- Busiest trading hour (average units across the whole week)
-- NOTE: order by the unrounded sum - 19:00 and 20:00 both round to 4.7,
-- and 19:00 is the true peak (4.71 vs 4.67), matching the Findings doc.
SELECT Hour AS peak_hour, ROUND(SUM(AvgUnits), 1) AS avg_units
FROM hour_profile
GROUP BY Hour
ORDER BY SUM(AvgUnits) DESC
LIMIT 1;

-- Quietest ACTIVE hour (trading floor at 07:00, not the closed 00:00-06:00)
SELECT Hour AS quietest_active_hour, ROUND(SUM(AvgUnits), 1) AS avg_units
FROM hour_profile
GROUP BY Hour
HAVING SUM(AvgUnits) >= (SELECT MAX(w) * 0.05 FROM (SELECT SUM(AvgUnits) AS w
                                                    FROM hour_profile GROUP BY Hour))
ORDER BY SUM(AvgUnits) ASC
LIMIT 1;

-- Weekday share of the trading day
SELECT
    Weekday,
    ROUND(SUM(AvgUnits), 1)                                AS avg_units_per_day,
    ROUND(100.0 * SUM(AvgUnits)
          / (SELECT SUM(AvgUnits) FROM hour_profile), 1)   AS day_share_pct
FROM hour_profile
GROUP BY WeekdayNum, Weekday
ORDER BY day_share_pct DESC;
