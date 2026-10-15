# Power BI — Dashboard Build Guide

Builds a three-page report from the REAL Kaggle POS dataset:

| Page | Mirrors | Headline visuals |
|---|---|---|
| **Overview** | reference screenshot *"Pharmacy Sales & Profitability Analysis"* | KPI cards, category bars, year columns, weekday bars, category table with flags |
| **Time Patterns** | reference screenshot *"Geographic Performance Page"* | year-vs-year variance line, weekday×hour **heatmap** (replaces the map), metric-toggle contribution chart |
| **ATC Categories** | product page of the reference | category bars, mix donut, growth table |

Data: `../data/pharma_sales_fact.csv` (+ `hour_profile.csv`).
DAX: paste from `measures.dax`. Model: `data_model.md`.
HTML preview of the finished look: `../dashboard/index.html`.
Power BI Desktop is not installed on this machine, so assemble the `.pbix` in the
Power BI GUI using this recipe (~45 min).

---

## 0. Palette

| Token | Hex | Use |
|---|---|---|
| Page background | `#EAF1F4` | Canvas |
| Card background | `#FFFFFF` | Cards, tables |
| Primary teal | `#2E8B9A` | Bars, active buttons |
| Deep navy | `#1F3864` | KPI numbers, headers |
| Light teal tints | `#8FC4CE`, `#CFE6EB` | Secondary series, sidebar |
| Positive green | `#1E9E5A` | Positive YoY, *Outperforming* |
| Negative red | `#C0392B` | Negative YoY, *Below Average* |
| Text gray | `#595959` | Labels, subtitles |

Canvas 16:9, page background `#EAF1F4`. Cards: white, no visual header,
subtle shadow, rounded corners where available.

---

## 1. Import & model (≈10 min)

1. **Get data → Text/CSV** → `data/pharma_sales_fact.csv` → **Transform Data**:
   `Date` → Date; `EstRevenue/EstCost/EstGrossProfit/UnitPrice` → Decimal →
   Data category **Currency (EUR)**; `Units` → Decimal (daily values are fractional);
   `MarginPct` → Decimal. Close & Apply.
2. Import `data/hour_profile.csv` the same way (→ `HourProfile`).
3. Create `Date` + `Category` tables from `data_model.md`, wire relationships,
   **mark Date as a date table**, set Sort-by-column for `MonthName`/`Weekday`.
4. **Enter data** → table `Metric` (Revenue | Profit | Units).
5. Paste `measures.dax`. Sanity check: `[Est. Revenue]` ≈ **€616.0K**,
   `[Total Units Sold]` = **127,596** (real), `[Gross Margin %]` ≈ **27.5%**,
   `[Revenue LFL YoY %]` ≈ **+3.8%**.

---

## 2. Page 1 — Overview (reference screenshot 2)

**Header**: title *Pharmacy Sales & Profitability Analysis* — Georgia italic 24 pt
navy; right-aligned slicers **Category**, **Year**, **Weekday** (dropdown style,
white fill, `#C9DCE4` border).

**Sidebar** (left 150 px, `#CFE6EB`): rounded **buttons** `Overview` (navy/white),
`Time Patterns`, `ATC Categories` with *Page navigation* actions.

**KPI cards** (4 × Card visual, ~230 × 110 px):

| Card | Indicator | Context line |
|---|---|---|
| Est. Revenue | `[Est. Revenue]` → `€0.0,"K"` | `[LFL Context]` |
| Est. Gross Profit | `[Est. Gross Profit]` | `[Profit Context]` |
| Gross Margin % | `[Gross Margin %]` → `0.0%` | `[Margin Context]` |
| Units Sold **(real)** | `[Total Units Sold]` | `[Units Context]` |

Callout 22 pt bold navy, label 10 pt italic gray, context 9 pt gray;
append a **multi-row card row** with `[Revenue LFL YoY %]` colored green/red.

**Metric toggle**: *Insert → Field parameter* `Display Value` (Revenue | Profit |
Units) with the parameter slicer restyled as **tiles** (active teal/white).

**Body visuals**

| Visual | Build |
|---|---|
| *Est. Revenue by Category* | Clustered **bar**, Y `Category[Category]`, X `[Display Value]`, sort desc, data labels `€#,##0,"K"`, teal |
| *Est. Revenue by Year* | Clustered **column**, X `Date[Year]`, Y `[Est. Revenue]`; label 2019 with *partial year* via card footnote or tooltip |
| *Units by Weekday* | Column, X `Date[Weekday]` (sort by WeekdayNo), Y `[Total Units Sold]` |
| *Estimated Revenue Mix* | **Donut** on `Category[Category]`, values `[Est. Revenue]`, labels percent, tints of teal |
| *Category performance table* | Table: `Category[Category]`, `[Total Units Sold]`, `[Est. Revenue]`, `[Est. Gross Profit]`, `[Revenue LFL YoY %]`, `[Outperform Flag]` → data bars on revenue; conditional text: *Outperforming* green / *Below Average* red; YoY 3-color or red/green rules |

---

## 3. Page 2 — Time Patterns (reference screenshot 1 layout)

**Header**: *Time Patterns* + subtitle *Year, Month, Weekday & Trading Hour*;
top-right year slicer **tiles** (2014 … 2019, single-select + *All* reset button).
KPI strip: sync the four cards from page 1 (**View → Sync slicers**).

**Left card — Seasonality**
Line chart: X `Date[MonthName]` (sort MonthNo), Y `[Est. Revenue]`, small
multiples or legend `Date[Year]` (6 thin lines) *or* a single averaged line with a
constant reference line at `[Avg Monthly Revenue]`. Add a card showing
`[Seasonality Index]` for the selected month.

**Right-top — Revenue Trend and Variance** (the reference's signature visual)
- Line chart, X `Date[MonthName]`, Y `[Est. Revenue]`, legend `Date[Year]`.
- Current year solid `#2E8B9A`, prior year dashed `#9DC3E6`.
- **Analytics → Constant line** = `[Avg Monthly Revenue]` (dotted gray) labelled
  *"Avg: …"*.
- Data labels on the current-year series using **Label contents → Field value** =
  `[Revenue MoM Delta]`, conditional colour green ≥ 0 / red < 0 — the +€ / −€
  variance labels from the reference.
- Card in the corner: `[Revenue LFL YoY %]` (never mix plain FY YoY into 2019).

**Left-bottom — Weekday × Hour heatmap** (replaces the reference map)
- **Matrix visual**: rows `HourProfile[Weekday]` (sorted by WeekdayNum), columns
  `HourProfile[Hour]`, values `SUM(AvgUnits)` (or average).
- **Cell elements → Background colour** = conditional formatting on the value,
  teal colour scale (white → `#CFE6EB` → `#2E8B9A`), data labels on.
- Caption: *"Average units by weekday and hour — whole-period trading profile
  (not cross-filtered by slicers)."*

**Right-bottom — Contribution to Revenue / Profit / Units**
Clustered bar: X `[Display Value]`, Y `Category[Category]`, top 8, labels on,
metric parameter slicer restyled as buttons above the chart (Revenue | Profit |
Units) — the reference's button group, minus geography.

---

## 4. Page 3 — ATC Categories

| Visual | Build |
|---|---|
| Category revenue bar | Y `Category[Category]`, X `[Est. Revenue]`, desc sort, labels |
| Mix donut | `Category[Category]` + `[Est. Revenue]` |
| Growth column | X `Category[Category]`, Y `[Revenue LFL YoY %]`, conditional colours |
| Detail table | Category, ATCCode, TherapyArea, `[Total Units Sold]`, `[Est. Revenue]`, `[Gross Margin %]`, `[Revenue LFL YoY %]`, `[Category Rank by Revenue]`, `[Growth Flag]` — data bars on revenue |
| Therapy treemap | Group `Category[TherapyArea]`, values `[Est. Revenue]` |
| Card row | `[Top Category]`, `[Trading Days]`, `[Avg Units per Trading Day]`, `[Revenue LFL YoY %]` |

---

## 5. Polish

1. **Slicers** synced across pages (View → Sync slicers): Category, Year, Weekday.
2. **Reset** button → *Clear all slicers* action; ⟳ icon in every header.
3. **Edit interactions**: KPI cards should NOT cross-filter other visuals.
4. **Tooltips**: small tooltip pages showing the entity's units/revenue/YoY.
5. Conditional formatting everywhere the reference uses it: data bars (teal),
   green/red fonts for YoY, green/red flag text.
6. **Refresh**: store the CSVs in OneDrive/SharePoint → Get data → refresh
   scheduled; or **Refresh now** after `python scripts/01_prepare_kaggle_data.py`.
7. Watermark/footer: *"Data: Kaggle 'Pharma sales data' (Milan Zdravkovic,
   CC BY-NC 4.0). € figures estimated from units × assumed prices."*

---

## 6. Acceptance checklist

- [ ] Cards (All): Est. Revenue **€616.0K** · Est. Gross Profit **€169.5K** ·
      Margin **27.5%** · Units **127,596** (real)
- [ ] `[Revenue LFL YoY %]` (all years) ≈ **+3.8%**, Units LFL ≈ **+0.7%**
- [ ] Category bars: Anti-Asthmatics €191.5K (31.1%) → Hypnotics €9.3K
- [ ] Units: Paracetamol = **49.4%** of units but 24.5% of revenue
- [ ] Year columns: 2016 €116.1K peak, 2017 dip (−18.3%), 2018 €118.5K,
      2019 marked *partial (to 8 Oct)*
- [ ] Seasonality: **Jan index 1.23**, **Jul 0.78**
- [ ] Heatmap: evening peak **19:00**, ramp from **07:00**, Saturday strongest day
- [ ] Flags: Anti-Asthmatics/Paracetamol/Anxiolytics *Outperforming*, rest red
- [ ] Slicers sync across pages; Reset clears; cards don't self-filter
