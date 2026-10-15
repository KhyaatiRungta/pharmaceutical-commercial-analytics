# Findings & Recommendations

Analysis of real pharmacy POS data (Kaggle, *Pharma sales data* by Milan
Zdravković, CC BY-NC 4.0): **127,596 real units**, 2,106 trading days,
2 Jan 2014 – 8 Oct 2019, 8 ATC drug groups. € figures are estimates
(units × assumed unit prices and margins — see
[`data/Data_Dictionary.md`](data/Data_Dictionary.md)). 2019 is a partial year;
its comparisons are **like-for-like** (1 Jan–8 Oct vs the identical window of
2018).

---

## Key findings

1. **Scale.** One pharmacy traded 127.6K units over six years: estimated
   revenue **€616.0K**, estimated gross profit **€169.5K (27.5%)**.

2. **Revenue is volatile year to year.** +8.0% (2015), +13.3% (2016, €116.1K
   peak), **−18.3% (2017 dip)**, +25.0% (2018 recovery to €118.5K). Any single
   year-over-year read needs context — the six-year view is the honest one.

3. **2019 is actually growing like-for-like.** 1 Jan–8 Oct 2019 is **+3.8%
   revenue / +0.7% units** vs the same period of 2018. Growth is broad-based:
   6 of 8 categories grew, led by **Hypnotics (+16.0%)**; **Anxiolytics (−5.7%)**
   is the only decliner. (A naive full-2019-vs-full-2018 comparison would show a
   false −25% — the partial-year trap this dashboard is built to avoid.)

4. **Price/margin mix, not volume, drives value.** Anti-Asthmatics is the
   largest category by estimated revenue (**31.1%**, €191.5K) on just 9.1% of
   units, while Paracetamol dominates volume (**49.4% of units**) but delivers
   only 24.5% of revenue. Cheap high-volume analgesics pull footfall; expensive
   respiratory and CNS products pull margin.

5. **Clear seasonality.** **January is the strongest month (index 1.23)** and
   **July the weakest (0.78)** — respiratory/anti-inflammatory demand tracks
   the seasons; inventory and promotions should too.

6. **Weekday demand is fairly even**, with a mild Saturday peak (**14.9%** of
   revenue vs Sunday 13.5%, uniform = 14.3%). The real scheduling lever is the
   hour of day, not the day of week.

7. **Trading has a sharp daily rhythm.** Sales ramp from **07:00**, peak at
   **19:00** (evening errand run), and the heatmap in *Time_Analysis* /
   *Time Patterns* shows Saturday evenings as the weekly high point.

8. **Profit is concentrated.** Assumed category margins run 22%
   (Anti-Asthmatics — reimbursement-driven) to 34% (Anxiolytics/Hypnotics), and
   the **top three categories generate 73.9% of estimated gross profit** —
   availability failures there are disproportionately costly.

## Recommendations

1. **Defend 2019's like-for-like growth.** Track the +3.8% LFL KPI monthly; if
   it decays, split it into traffic vs basket vs price per category before
   changing the order plan.
2. **Investigate Anxiolytics (−5.7%).** It is the only declining category —
   check stock-outs, a competitor's generic entry, and prescriber/patient
   churn; review the ordering cadence.
3. **Plan inventory around the seasonal curve.** Build respiratory/analgesic
   stock from September for the January peak (index 1.23); pull back buys and
   run margin-focused promotions in the July trough (0.78).
4. **Match labour to the daily rhythm.** Staff up for the 17:00–20:00 window
   and Saturdays; schedule replenishment, ordering and admin in the 07:00–10:00
   ramp and mid-afternoon lull.
5. **Grow value, not just volume.** Pair high-traffic Paracetamol availability
   with counselling/up-sell to higher-margin categories; Anti-Asthmatics earn
   €16.49 est. revenue per unit — protect their availability first.
6. **Institutionalise the measurement loop.** Re-run the three scripts monthly
   on the same extract and review the KPI cards (units, est. revenue/margin,
   LFL YoY, flags) in a standing commercial meeting; when real revenue data
   becomes available, swap the price/margin assumptions in
   `scripts/01_prepare_kaggle_data.py` and everything downstream recomputes.

## Method & caveats

- **Source:** Kaggle *Pharma sales data* (CC BY-NC 4.0) — 600k POS
  transactions pre-aggregated to hourly/daily/weekly/monthly for 8 ATC groups,
  one pharmacy, 2014-01-02 → 2019-10-08.
- **Units are real; € are estimates.** Estimated revenue = units × assumed
  average unit price per category; cost/profit use assumed category margin
  rates. All assumptions are listed in the Excel README sheet and
  `data/Data_Dictionary.md`, and configurable in one place in the prepare
  script.
- **Partial-year handling.** 2019 ends 8 Oct: its YoY compares 1 Jan–8 Oct
  2019 with the identical window of 2018. 2015–2018 use full-year
  comparisons. The DAX/JS/Excel implementations share this rule.
- **Outperform flags** compare a category's estimated gross profit with the
  average of the eight categories under the current filter.
- **No hard-coded results.** Excel cells are live formulas; the DAX measures
  and the HTML dashboard recompute from the same fact table, so refreshing the
  data refreshes every number in this document's source visuals.
