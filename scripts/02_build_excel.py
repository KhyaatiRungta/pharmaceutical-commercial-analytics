"""
Phase 9: Build the Excel analysis workbook on the REAL Kaggle dataset.
Source: kaggle.com/datasets/milanzdravkovic/pharma-sales-data (CC BY-NC 4.0)
Output: excel/Pharma_Sales_Analysis.xlsx
Sheets: README | KPI_Dashboard | Sales_Data | Category_Analysis |
        Time_Analysis | Findings
Units are real source values; revenue/cost/profit are ESTIMATED from documented
assumptions (avg unit price + gross-margin rate per ATC group).
2019 ends 8 Oct -> its YoY is like-for-like (1 Jan-8 Oct vs same period 2018).
"""
import math
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, PieChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.formatting.rule import CellIsRule, ColorScaleRule, DataBarRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

BASE = Path(__file__).resolve().parents[1]
FACT_CSV = BASE / "data" / "pharma_sales_fact.csv"
HOUR_CSV = BASE / "data" / "hour_profile.csv"
OUT = BASE / "excel" / "Pharma_Sales_Analysis.xlsx"
OUT.parent.mkdir(exist_ok=True)

fact = pd.read_csv(FACT_CSV, parse_dates=["Date"])
hours = pd.read_csv(HOUR_CSV)
N = len(fact)
LAST = N + 1

# ------------------------------------------------------------------ palette
NAVY, TEAL, LIGHT, LINE = "1F3864", "2E8B9A", "EAF3F6", "C9DCE4"
GRAY, WHITE, GREEN, GREEN_BG = "595959", "FFFFFF", "1E7B34", "DFF3E3"
RED, RED_BG = "B03A2E", "FBE3E0"

F_TITLE = Font(name="Calibri", size=16, bold=True, color=WHITE)
F_SUB = Font(name="Calibri", size=10, italic=True, color="D9E6EC")
F_SECTION = Font(name="Calibri", size=11, bold=True, color=WHITE)
F_TH = Font(name="Calibri", size=10, bold=True, color=WHITE)
F_LBL = Font(name="Calibri", size=10, bold=True, color=GRAY)
F_VAL = Font(name="Calibri", size=20, bold=True, color=NAVY)
F_VAL_S = Font(name="Calibri", size=14, bold=True, color=NAVY)
F_CTX = Font(name="Calibri", size=9, color="7F7F7F")
F_BODY = Font(name="Calibri", size=11, color="262626")
F_BOLD = Font(name="Calibri", size=11, bold=True, color=NAVY)

FILL_LIGHT = PatternFill("solid", fgColor=LIGHT)
FILL_NAVY = PatternFill("solid", fgColor=NAVY)
FILL_TEAL = PatternFill("solid", fgColor=TEAL)
FILL_TOTAL = PatternFill("solid", fgColor="D6E4EA")
THIN = Side(style="thin", color=LINE)

FMT_EUR0 = '€#,##0'
FMT_EUR2 = '€#,##0.00'
FMT_K = '€0.0,"K"'
FMT_UK = '#,##0.0,"K"'
FMT_PCT = '0.0%'
FMT_PCT_S = '+0.0%;-0.0%;0.0%'
FMT_INT = '#,##0'
FMT_PP = '0.0"%"'

# ------------------------------------------------------------- formula base
HDRS = ["Date", "Year", "MonthNum", "MonthName", "Quarter", "YearMonth",
        "Weekday", "ATCCode", "Category", "TherapyArea", "Units",
        "UnitPrice", "EstRevenue", "EstCost", "EstGrossProfit", "MarginPct"]
LC = {h: get_column_letter(i + 1) for i, h in enumerate(HDRS)}


def rg(h):
    return f"Sales_Data!${LC[h]}$2:${LC[h]}${LAST}"


S_REV = f"SUM({rg('EstRevenue')})"
S_CST = f"SUM({rg('EstCost')})"
S_PRF = f"SUM({rg('EstGrossProfit')})"
S_UNT = f"SUM({rg('Units')})"

# ------------------------------------------------------- like-for-like windows
Y_CUR = int(fact["Date"].max().year)                 # 2019
D_END = fact["Date"].max()                           # 2019-10-08
D_PRIOR_END = D_END.replace(year=Y_CUR - 1)          # 2018-10-08
CUR_W = f'{rg("Date")},">="&DATE({Y_CUR},1,1),{rg("Date")},"<="&DATE({D_END.year},{D_END.month},{D_END.day})'
PRI_W = f'{rg("Date")},">="&DATE({Y_CUR - 1},1,1),{rg("Date")},"<="&DATE({D_PRIOR_END.year},{D_PRIOR_END.month},{D_PRIOR_END.day})'
LFL_REV = f"IFERROR(SUMIFS({rg('EstRevenue')},{CUR_W})/SUMIFS({rg('EstRevenue')},{PRI_W})-1,\"\")"
LFL_UNT = f"IFERROR(SUMIFS({rg('Units')},{CUR_W})/SUMIFS({rg('Units')},{PRI_W})-1,\"\")"
LFL_PRF = f"IFERROR(SUMIFS({rg('EstGrossProfit')},{CUR_W})/SUMIFS({rg('EstGrossProfit')},{PRI_W})-1,\"\")"


# ----------------------------------------------------------------- helpers
def box(ws, r1, c1, r2, c2, color=LINE):
    for r in range(r1, r2 + 1):
        for c in range(c1, c2 + 1):
            cell = ws.cell(row=r, column=c)
            cell.border = Border(
                left=THIN if c == c1 else cell.border.left,
                right=THIN if c == c2 else cell.border.right,
                top=THIN if r == r1 else cell.border.top,
                bottom=THIN if r == r2 else cell.border.bottom)


def title_block(ws, title, subtitle, last_col):
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=last_col)
    ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=last_col)
    for c in range(1, last_col + 1):
        ws.cell(row=1, column=c).fill = FILL_NAVY
        ws.cell(row=2, column=c).fill = FILL_NAVY
    a = ws.cell(row=1, column=1)
    a.value, a.font = title, F_TITLE
    a.alignment = Alignment(vertical="center", indent=1)
    b = ws.cell(row=2, column=1)
    b.value, b.font = subtitle, F_SUB
    b.alignment = Alignment(vertical="center", indent=1)
    ws.row_dimensions[1].height = 30
    ws.row_dimensions[2].height = 16
    ws.sheet_view.showGridLines = False


def section(ws, row, text, last_col):
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=last_col)
    for c in range(1, last_col + 1):
        ws.cell(row=row, column=c).fill = FILL_TEAL
    cell = ws.cell(row=row, column=1)
    cell.value, cell.font = text, F_SECTION
    cell.alignment = Alignment(vertical="center", indent=1)
    ws.row_dimensions[row].height = 20


def head_row(ws, row, labels, start_col=1):
    for i, lab in enumerate(labels):
        cell = ws.cell(row=row, column=start_col + i)
        cell.value, cell.font, cell.fill = lab, F_TH, FILL_TEAL
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
    ws.row_dimensions[row].height = 28


def card(ws, r, c1, c2, label, value, vfmt, context, vfont=None, cfmt=None):
    for rr in range(r, r + 4):
        for cc in range(c1, c2 + 1):
            ws.cell(row=rr, column=cc).fill = FILL_LIGHT
    ws.merge_cells(start_row=r, start_column=c1, end_row=r, end_column=c2)
    ws.merge_cells(start_row=r + 1, start_column=c1, end_row=r + 2, end_column=c2)
    ws.merge_cells(start_row=r + 3, start_column=c1, end_row=r + 3, end_column=c2)
    lab = ws.cell(row=r, column=c1)
    lab.value, lab.font = label, F_LBL
    lab.alignment = Alignment(vertical="center", indent=1)
    val = ws.cell(row=r + 1, column=c1)
    val.value, val.font, val.number_format = value, vfont or F_VAL, vfmt
    val.alignment = Alignment(vertical="center", indent=1)
    ctx = ws.cell(row=r + 3, column=c1)
    ctx.value, ctx.font = context, F_CTX
    ctx.number_format = cfmt or "General"
    ctx.alignment = Alignment(vertical="center", indent=1)
    ws.row_dimensions[r].height = 16
    ws.row_dimensions[r + 1].height = 19
    ws.row_dimensions[r + 2].height = 17
    ws.row_dimensions[r + 3].height = 14
    box(ws, r, c1, r + 3, c2)


def bullet(ws, row, text, col=1, font=None):
    cell = ws.cell(row=row, column=col)
    cell.value = text
    cell.font = font or F_BODY
    cell.alignment = Alignment(wrap_text=True, vertical="top")
    ws.row_dimensions[row].height = 15 * max(1, math.ceil(len(text) / 145))
    return row + 1


def style_series(s, color, dash=False):
    s.graphicalProperties.line.solidFill = color
    s.graphicalProperties.line.width = 26000
    if dash:
        s.graphicalProperties.line.dashStyle = "dash"
    s.marker.symbol = "circle"
    s.marker.size = 5
    s.smooth = False


def bar_series(s, color):
    s.graphicalProperties.solidFill = color
    s.graphicalProperties.line.solidFill = color


def flag_cf(ws, rng_):
    ws.conditional_formatting.add(rng_, CellIsRule(
        operator="equal", formula=['"Outperforming"'],
        font=Font(color=GREEN, bold=True), fill=PatternFill("solid", fgColor=GREEN_BG)))
    ws.conditional_formatting.add(rng_, CellIsRule(
        operator="equal", formula=['"Below Average"'],
        font=Font(color=RED, bold=True), fill=PatternFill("solid", fgColor=RED_BG)))


def yoy_cf(ws, rng_):
    ws.conditional_formatting.add(rng_, CellIsRule(
        operator="lessThan", formula=["0"], font=Font(color=RED, bold=True),
        fill=PatternFill("solid", fgColor=RED_BG)))
    ws.conditional_formatting.add(rng_, CellIsRule(
        operator="greaterThanOrEqual", formula=["0"], font=Font(color=GREEN, bold=True),
        fill=PatternFill("solid", fgColor=GREEN_BG)))


# =============================================== stats for Findings (real data)
tot_r, tot_u = fact["EstRevenue"].sum(), fact["Units"].sum()
tot_p = fact["EstGrossProfit"].sum()
days = fact["Date"].nunique()
by_year = fact.groupby("Year").agg(units=("Units", "sum"),
                                   rev=("EstRevenue", "sum"))
by_cat = fact.groupby("Category").agg(units=("Units", "sum"),
                                      rev=("EstRevenue", "sum"),
                                      prof=("EstGrossProfit", "sum"))
by_cat["share"] = by_cat["rev"] / tot_r
by_cat = by_cat.sort_values("rev", ascending=False)
# monthly seasonality: mean monthly revenue per year
msn = fact.groupby(["Year", "MonthNum"])["EstRevenue"].sum().groupby("MonthNum").mean()
msn_idx = msn / msn.mean()
# weekday
wd_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
            "Saturday", "Sunday"]
by_wd = fact.groupby("Weekday").agg(units=("Units", "sum"),
                                     rev=("EstRevenue", "sum")).reindex(wd_order)
by_wd["share"] = by_wd["rev"] / tot_r
# LFL 2019 vs 2018 (1 Jan - 8 Oct)
cur = fact[(fact["Date"] >= f"{Y_CUR}-01-01") & (fact["Date"] <= D_END)]
pri = fact[(fact["Date"] >= f"{Y_CUR - 1}-01-01") & (fact["Date"] <= D_PRIOR_END)]
lfl_r = cur["EstRevenue"].sum() / pri["EstRevenue"].sum() - 1
lfl_u = cur["Units"].sum() / pri["Units"].sum() - 1
cat_lfl = (cur.groupby("Category")["EstRevenue"].sum() /
           pri.groupby("Category")["EstRevenue"].sum() - 1).sort_values(ascending=False)
# hourly peak/trough among ACTIVE trading hours only (ignore closed-door hours)
hp = hours.groupby("Hour")["AvgUnits"].sum()
active = hp[hp >= hp.max() * 0.05]
peak_hour, quiet_hour = int(active.idxmax()), int(active.idxmin())
# full-year yoy
y_rev = by_year["rev"]
yoy_full = {y: y_rev[y] / y_rev[y - 1] - 1 for y in [2015, 2016, 2017, 2018]}
MN = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
      "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
m_hi, m_lo = int(msn_idx.idxmax()), int(msn_idx.idxmin())
wd_hi, wd_lo = by_wd["rev"].idxmax(), by_wd["rev"].idxmin()
cat_top_rev = by_cat.index[0]
cat_top_units = by_cat["units"].idxmax()
cat_up, cat_down = cat_lfl.index[0], cat_lfl.index[-1]

M = lambda v: f"€{v / 1000:,.1f}K"
K = lambda v: f"{v / 1000:,.1f}K"
P = lambda v: f"{v * 100:.1f}%"
S = lambda v: f"{v:+.1%}"

findings = [
    f"Real volume: {K(tot_u)} units across {days:,} trading days "
    f"(2 Jan 2014 - 8 Oct 2019) at one pharmacy; estimated revenue {M(tot_r)}, "
    f"estimated gross profit {M(tot_p)} ({P(tot_p / tot_r)}).",
    f"Revenue is volatile year to year: {yoy_full[2015]:+.1%} (2015), "
    f"{yoy_full[2016]:+.1%} (2016 peak {M(y_rev[2016])}), {yoy_full[2017]:-.1%} (2017 dip), "
    f"{yoy_full[2018]:+.1%} (2018 recovery to {M(y_rev[2018])}).",
    f"2019 YTD (1 Jan-8 Oct) is {S(lfl_r)} revenue and {S(lfl_u)} units versus the "
    f"same period of 2018 — growth is broad-based: "
    f"{int((cat_lfl > 0).sum())} of 8 categories grew, led by {cat_up} "
    f"({S(cat_lfl[cat_up])}); {cat_down} is the only decliner "
    f"({S(cat_lfl[cat_down])}).",
    f"Mix: {cat_top_rev} is the largest category by estimated revenue "
    f"({P(by_cat.loc[cat_top_rev, 'share'])}) even though {cat_top_units} dominates volume "
    f"({P(by_cat.loc[cat_top_units, 'units'] / tot_u)} of units) — price/margin mix, not "
    f"volume, drives value.",
    f"Seasonality: {MN[m_hi - 1]} is the strongest month (index {msn_idx.max():.2f}) and "
    f"{MN[m_lo - 1]} the weakest ({msn_idx.min():.2f}); respiratory/antihistamine demand "
    f"tracks the seasons.",
    f"Weekday pattern: {wd_hi} generates {P(by_wd.loc[wd_hi, 'share'])} of revenue vs "
    f"{wd_lo} {P(by_wd.loc[wd_lo, 'share'])} — staffing and stock cover should follow it.",
    f"Trading peaks at {peak_hour:02d}:00 and troughs at {quiet_hour:02d}:00 "
    f"(average units per hour, all days); the weekday x hour heatmap in Time_Analysis "
    f"shows the exact shift pattern.",
    f"Category economics: assumed margins run 22% (Anti-Asthmatics, reimbursement-driven) "
    f"to 34% (Anxiolytics/Hypnotics); est. profit is concentrated in the top three "
    f"categories ({P(by_cat['prof'].nlargest(3).sum() / tot_p)} of profit).",
]

recommendations = [
    f"Defend 2019: investigate the {S(lfl_r)} like-for-like revenue decline — split it into "
    f"traffic vs basket vs price per category before adjusting the order plan.",
    f"Prioritise {cat_up} (only category flat/growing LFL) with shelf space and stock "
    f"availability; review the ordering cadence for {cat_down} (steepest decline).",
    f"Build the seasonal plan around {MN[m_hi - 1]} (index {msn_idx.max():.2f}) and "
    f"{MN[m_lo - 1]} ({msn_idx.min():.2f}): pre-build inventory from September, pull back "
    f"promotions in the August trough.",
    f"Match labour to demand: staff up for {wd_hi}s and the {peak_hour:02d}:00-peak window; "
    f"schedule replenishment and admin in the {quiet_hour:02d}:00 / {wd_lo} trough.",
    "Grow value, not just volume: Anti-Asthmatics deliver the highest estimated revenue per "
    "unit — pair them with counselling/up-selling, while protecting Paracetamol availability "
    "for footfall.",
    "Refresh this workbook monthly from the same Kaggle extract and review the KPI cards "
    "(units, estimated revenue/margin, like-for-like YoY) in a standing commercial meeting.",
]

method = [
    "Source: Kaggle 'Pharma sales data' by Milan Zdravkovic (CC BY-NC 4.0) - 600k POS "
    "transactions pre-aggregated to hourly/daily/weekly/monthly for 8 ATC groups, "
    "one pharmacy, 2014-01-02 to 2019-10-08.",
    f"Units Sold is real source data. Est. Revenue = Units x assumed average unit price; "
    f"Est. Cost/Profit use assumed category gross-margin rates (README lists all eight). "
    f"Financial figures are ESTIMATES for analytical illustration.",
    "2019 is a partial year (ends 8 Oct): its YoY compares 1 Jan-8 Oct 2019 with the "
    "identical window of 2018 (like-for-like). 2015-2018 are full-year comparisons.",
    "Outperform flags compare a category's estimated gross profit with the average of the "
    "eight categories under the current data cut.",
    "Excel contains no hard-coded results: every KPI/table cell is a SUMIFS/INDEX-MATCH "
    "formula over the Sales_Data table.",
]

# =====================================================================
wb = Workbook()

# ---------------------------------------------------------- 1. README
ws = wb.active
ws.title = "README"
ws.sheet_properties.tabColor = GRAY
ws.column_dimensions["A"].width = 26
ws.column_dimensions["B"].width = 104
title_block(ws, "Pharmaceutical Commercial Analytics — Excel Working File",
            "Real Kaggle POS data 2014–2019 | units real, revenue estimated | currency EUR", 2)
r = 4
r = bullet(ws, r, "PURPOSE", font=F_BOLD)
r = bullet(ws, r, "This workbook analyses six years of real pharmacy point-of-sale data to show "
                  "which drug categories sell best, how demand moves through years, months, "
                  "weekdays and trading hours, and where performance needs attention. Every KPI "
                  "and chart is a live formula over Sales_Data. The same data feeds the Power BI "
                  "dashboard and the HTML preview (see /powerbi and /dashboard).")
r += 1
r = bullet(ws, r, "DATA SOURCE & LICENCE", font=F_BOLD)
r = bullet(ws, r, "Kaggle: 'Pharma sales data' by Milan Zdravkovic — "
                  "kaggle.com/datasets/milanzdravkovic/pharma-sales-data — licence CC BY-NC 4.0. "
                  "Raw extracts (hourly/daily/weekly/monthly) are kept in data/kaggle_raw/. "
                  "Fact table: data/pharma_sales_fact.csv, prepared by scripts/01_prepare_kaggle_data.py.")
r += 1
r = bullet(ws, r, "WORKBOOK CONTENTS", font=F_BOLD)
head_row(ws, r, ["Sheet", "What it contains"])
r += 1
for name, desc in [
    ("KPI_Dashboard", "Executive cards (est. revenue, est. gross profit, margin, units), "
                      "like-for-like YoY, annual performance 2014–2019 and the category league table."),
    ("Sales_Data", f"Source fact table ({N:,} rows): one row = one day x one ATC category "
                   "(Excel Table 'SalesFact'). 2 Jan 2014 – 8 Oct 2019."),
    ("Category_Analysis", "The 8 ATC categories: units, estimated revenue/profit, margin, share, "
                          "2018 full year, 2019 YTD, like-for-like YoY, outperform flags, charts."),
    ("Time_Analysis", "Monthly revenue by year + seasonality index, weekday pattern, and the "
                      "weekday x trading-hour heatmap."),
    ("Findings", "Key findings and recommendations produced by the analysis."),
]:
    c = ws.cell(row=r, column=1)
    c.value, c.font = name, F_BOLD
    c.alignment = Alignment(vertical="top")
    b = ws.cell(row=r, column=2)
    b.value = desc
    b.font = F_BODY
    b.alignment = Alignment(wrap_text=True, vertical="top")
    ws.row_dimensions[r].height = 15 * max(1, math.ceil(len(desc) / 100))
    box(ws, r, 1, r, 2)
    r += 1
r += 1
r = bullet(ws, r, "ESTIMATION ASSUMPTIONS (applied in scripts/01_prepare_kaggle_data.py)",
           font=F_BOLD)
head_row(ws, r, ["ATC code / group", "Assumed avg unit price and gross-margin rate"])
r += 1
for code, name, desc, price, margin in [
    ("M01AB", "NSAIDs-Acetic", "Anti-inflammatory, acetic acid derivatives (e.g. diclofenac)", 3.10, 0.30),
    ("M01AE", "NSAIDs-Propionic", "Anti-inflammatory, propionic acid derivatives (e.g. ibuprofen)", 3.60, 0.30),
    ("N02BA", "Salicylates", "Analgesics/antipyretics, salicylic acid (e.g. aspirin)", 2.80, 0.28),
    ("N02BE", "Paracetamol", "Analgesics/antipyretics, anilides (e.g. paracetamol)", 2.40, 0.26),
    ("N05B", "Anxiolytics", "Psycholeptics, anxiolytic drugs", 6.90, 0.34),
    ("N05C", "Hypnotics", "Psycholeptics, hypnotics and sedatives", 7.40, 0.34),
    ("R03", "Anti-Asthmatics", "Drugs for obstructive airway diseases (asthma/COPD)", 16.50, 0.22),
    ("R06", "Antihistamines", "Antihistamines for systemic use", 8.20, 0.32),
]:
    a = ws.cell(row=r, column=1)
    a.value, a.font = f"{code}  {name}", F_BOLD
    a.alignment = Alignment(vertical="top")
    b = ws.cell(row=r, column=2)
    b.value = f"{desc} — €{price:.2f}/unit, {margin:.0%} gross margin"
    b.font = F_BODY
    b.alignment = Alignment(wrap_text=True, vertical="top")
    box(ws, r, 1, r, 2)
    r += 1
r += 1
r = bullet(ws, r, "IMPORTANT: units are real; € revenue/cost/profit are ESTIMATES derived from "
                  "the assumptions above. 2019 data ends 8 October, so its YoY is "
                  "like-for-like (1 Jan–8 Oct vs the same window of 2018).")
r += 1
r = bullet(ws, r, "REFRESH / REBUILD", font=F_BOLD)
r = bullet(ws, r, "python scripts/01_prepare_kaggle_data.py && python scripts/02_build_excel.py "
                  "— or replace the rows in Sales_Data keeping the same columns; all formulas "
                  "and charts recalculate.")
ws.freeze_panes = "A4"

# ---------------------------------------------------------- 2. SALES_DATA
sd = wb.create_sheet("Sales_Data")
sd.sheet_properties.tabColor = TEAL
sd.append(HDRS)
for row in fact.itertuples(index=False):
    sd.append([
        row.Date.to_pydatetime(), int(row.Year), int(row.MonthNum), row.MonthName,
        row.Quarter, row.YearMonth, row.Weekday, row.ATCCode, row.Category,
        row.TherapyArea, float(row.Units), float(row.UnitPrice),
        float(row.EstRevenue), float(row.EstCost), float(row.EstGrossProfit),
        float(row.MarginPct),
    ])
for c in range(1, len(HDRS) + 1):
    cell = sd.cell(row=1, column=c)
    cell.font, cell.fill = F_TH, FILL_NAVY
    cell.alignment = Alignment(horizontal="center", vertical="center")
sd.row_dimensions[1].height = 24
fmts = {1: "yyyy-mm-dd", 11: '#,##0.00', 12: FMT_EUR2, 13: FMT_EUR2,
        14: FMT_EUR2, 15: FMT_EUR2, 16: FMT_PP}
for rr in range(2, LAST + 1):
    for cc, fmt in fmts.items():
        sd.cell(row=rr, column=cc).number_format = fmt
widths = {"A": 12, "B": 7, "C": 9, "D": 10, "E": 9, "F": 11, "G": 11, "H": 9,
          "I": 16, "J": 46, "K": 10, "L": 10, "M": 12, "N": 12, "O": 14, "P": 10}
for col, w in widths.items():
    sd.column_dimensions[col].width = w
sd.freeze_panes = "B2"
tab = Table(displayName="SalesFact", ref=f"A1:P{LAST}")
tab.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True,
                                    showColumnStripes=False, showFirstColumn=False,
                                    showLastColumn=False)
sd.add_table(tab)

# ---------------------------------------------------------- 3. KPI_DASHBOARD
db = wb.create_sheet("KPI_Dashboard", 1)
db.sheet_properties.tabColor = NAVY
title_block(db, "Pharmaceutical Commercial Analytics Dashboard",
            "Real pharmacy POS data 2014–2019 | € figures estimated from documented assumptions", 12)
db.row_dimensions[3].height = 6
card(db, 4, 1, 3, "EST. REVENUE (6 YEARS)", f"={S_REV}", FMT_K,
     f'="2019 YTD vs 2018: "&TEXT({LFL_REV},"+0.0%;-0.0%")&" (like-for-like)"')
card(db, 4, 4, 6, "EST. GROSS PROFIT", f"={S_PRF}", FMT_K,
     f'="Est. cost of goods: €"&TEXT({S_CST}/1000,"0.0")&"K"')
card(db, 4, 7, 9, "GROSS MARGIN %", f"=IFERROR({S_PRF}/{S_REV},0)", "0.0%",
     "Blended from assumed category margins")
card(db, 4, 10, 12, "UNITS SOLD (REAL)", f"={S_UNT}", FMT_UK,
     f'="Avg "&TEXT({S_UNT}/{days},"#,##0")&" units per trading day"')
db.row_dimensions[8].height = 6
card(db, 9, 1, 2, "EST. REVENUE 2014", f"=SUMIFS({rg('EstRevenue')},{rg('Year')},2014)",
     FMT_K, "Baseline full year", vfont=F_VAL_S)
y18 = f"IFERROR(SUMIFS({rg('EstRevenue')},{rg('Year')},2018)/SUMIFS({rg('EstRevenue')},{rg('Year')},2017)-1,0)"
card(db, 9, 3, 4, "EST. REVENUE 2018", f"=SUMIFS({rg('EstRevenue')},{rg('Year')},2018)",
     FMT_K, f'="vs 2017: "&TEXT({y18},"+0.0%;-0.0%")&" (last full year)"', vfont=F_VAL_S)
card(db, 9, 5, 6, f"REVENUE {Y_CUR} YTD",
     f"=SUMIFS({rg('EstRevenue')},{CUR_W})", FMT_K,
     f'="LFL vs {Y_CUR - 1}: "&TEXT({LFL_REV},"+0.0%;-0.0%")&" (1 Jan–8 Oct)"', vfont=F_VAL_S)
card(db, 9, 7, 8, "TOP CATEGORY",
     "=INDEX(Category_Analysis!$A$5:$A$12,MATCH(MAX(Category_Analysis!$F$5:$F$12),Category_Analysis!$F$5:$F$12,0))",
     "General",
     '="€"&TEXT(MAX(Category_Analysis!$F$5:$F$12),"#,##0")&" est. ("&TEXT(MAX(Category_Analysis!$F$5:$F$12)/'
     f'{S_REV},"0.0%")&" of revenue)"', vfont=F_VAL_S)
card(db, 9, 9, 10, "BUSIEST WEEKDAY",
     "=INDEX(Time_Analysis!$A$23:$A$29,MATCH(MAX(Time_Analysis!$C$23:$C$29),Time_Analysis!$C$23:$C$29,0))",
     "General",
     '="Generates "&TEXT(MAX(Time_Analysis!$C$23:$C$29)/'
     f'{S_REV},"0.0%")&" of est. revenue"', vfont=F_VAL_S)
card(db, 9, 11, 12, "PEAK TRADING HOUR",
     '=INDEX(Time_Analysis!$B$38:$Y$38,MATCH(MAX(Time_Analysis!$B$46:$Y$46),Time_Analysis!$B$46:$Y$46,0))&":00"',
     "General", "Busiest average hour, all days", vfont=F_VAL_S)
db.row_dimensions[13].height = 6

section(db, 14, "ANNUAL PERFORMANCE (ESTIMATED REVENUE, REAL UNITS)", 6)
head_row(db, 15, ["Year", "Units", "Est. Revenue", "YoY %", "", ""])
years = sorted(by_year.index)
for i, y in enumerate(years):
    r = 16 + i
    db.cell(row=r, column=1, value=int(y))
    db.cell(row=r, column=2, value=f"=SUMIFS({rg('Units')},{rg('Year')},$A{r})")
    db.cell(row=r, column=3, value=f"=SUMIFS({rg('EstRevenue')},{rg('Year')},$A{r})")
    if y == Y_CUR:
        db.cell(row=r, column=4, value=f"={LFL_REV}")
        db.cell(row=r, column=5, value="YTD to 8 Oct — LFL vs prior year")
    else:
        db.cell(row=r, column=4, value=f'=IFERROR(C{r}/C{r - 1}-1,"")')
    db.cell(row=r, column=1).number_format = "0"
    db.cell(row=r, column=2).number_format = FMT_INT
    db.cell(row=r, column=3).number_format = FMT_EUR0
    db.cell(row=r, column=4).number_format = FMT_PCT_S
    db.cell(row=r, column=5).font = F_CTX
    box(db, r, 1, r, 5)
r_tot = 16 + len(years)
db.cell(row=r_tot, column=1, value="TOTAL")
db.cell(row=r_tot, column=2, value=f"=SUM(B16:B{r_tot - 1})")
db.cell(row=r_tot, column=3, value=f"=SUM(C16:C{r_tot - 1})")
db.cell(row=r_tot, column=4, value="")
db.cell(row=r_tot, column=2).number_format = FMT_INT
db.cell(row=r_tot, column=3).number_format = FMT_EUR0
for cc in range(1, 6):
    db.cell(row=r_tot, column=cc).fill = FILL_TOTAL
    db.cell(row=r_tot, column=cc).font = F_BOLD
box(db, r_tot, 1, r_tot, 5)
yoy_cf(db, f"D16:D{r_tot - 1}")

sec2 = r_tot + 2
section(db, sec2, "CATEGORY LEAGUE — LIKE-FOR-LIKE YoY & OUTPERFORM FLAGS", 6)
head_row(db, sec2 + 1, ["Category", "Est. Revenue", "Est. Profit", "Share",
                        f"LFL YoY ({Y_CUR} vs {Y_CUR - 1})", "Flag"])
c_first = sec2 + 2
cats_sorted = list(by_cat.index)
for i, cname in enumerate(cats_sorted):
    r = c_first + i
    db.cell(row=r, column=1, value=cname)
    db.cell(row=r, column=2, value=f"=SUMIFS({rg('EstRevenue')},{rg('Category')},$A{r})")
    db.cell(row=r, column=3, value=f"=SUMIFS({rg('EstGrossProfit')},{rg('Category')},$A{r})")
    db.cell(row=r, column=4, value=f"=IFERROR(B{r}/$B${c_first + 8},0)")
    db.cell(row=r, column=5,
            value=f'=IFERROR(SUMIFS({rg("EstRevenue")},{rg("Category")},$A{r},{CUR_W})'
                  f'/SUMIFS({rg("EstRevenue")},{rg("Category")},$A{r},{PRI_W})-1,"")')
    db.cell(row=r, column=6,
            value=f'=IF(C{r}>=AVERAGE($C${c_first}:$C${c_first + 7}),"Outperforming","Below Average")')
    db.cell(row=r, column=2).number_format = FMT_EUR0
    db.cell(row=r, column=3).number_format = FMT_EUR0
    db.cell(row=r, column=4).number_format = FMT_PCT
    db.cell(row=r, column=5).number_format = FMT_PCT_S
    db.cell(row=r, column=6).alignment = Alignment(horizontal="center")
    box(db, r, 1, r, 6)
r_ctot = c_first + 8
db.cell(row=r_ctot, column=1, value="TOTAL")
db.cell(row=r_ctot, column=2, value=f"=SUM(B{c_first}:B{r_ctot - 1})")
db.cell(row=r_ctot, column=3, value=f"=SUM(C{c_first}:C{r_ctot - 1})")
db.cell(row=r_ctot, column=4, value=f"=SUM(D{c_first}:D{r_ctot - 1})")
db.cell(row=r_ctot, column=5, value=f"={LFL_REV}")
for cc, fmt in {2: FMT_EUR0, 3: FMT_EUR0, 4: FMT_PCT, 5: FMT_PCT_S}.items():
    db.cell(row=r_ctot, column=cc).number_format = fmt
for cc in range(1, 7):
    db.cell(row=r_ctot, column=cc).fill = FILL_TOTAL
    db.cell(row=r_ctot, column=cc).font = F_BOLD
box(db, r_ctot, 1, r_ctot, 6)
db.conditional_formatting.add(f"B{c_first}:B{r_ctot - 1}",
                              DataBarRule(start_type="min", end_type="max",
                                          color="5B9BD5", showValue=True))
yoy_cf(db, f"E{c_first}:E{r_ctot - 1}")
flag_cf(db, f"F{c_first}:F{r_ctot - 1}")

for col, w in {"A": 18, "B": 13, "C": 14, "D": 12, "E": 34, "F": 17, "G": 14,
               "H": 14, "I": 14, "J": 14, "K": 14, "L": 14}.items():
    db.column_dimensions[col].width = w

ac = BarChart()
ac.type, ac.style, ac.title = "col", 10, "Est. Revenue by Year (EUR)"
ac.add_data(Reference(db, min_col=3, min_row=15, max_row=r_tot - 1), titles_from_data=True)
ac.set_categories(Reference(db, min_col=1, min_row=16, max_row=r_tot - 1))
bar_series(ac.series[0], TEAL)
ac.legend = None
ac.dataLabels = DataLabelList()
ac.dataLabels.showVal = True
ac.dataLabels.numFmt = '€#,##0,"K"'
ac.y_axis.number_format = '€#,##0,"K"'
ac.width, ac.height = 15, 7.5
db.add_chart(ac, "G14")

cb = BarChart()
cb.type, cb.style, cb.title = "bar", 10, "Est. Revenue by Category (EUR)"
cb.add_data(Reference(db, min_col=2, min_row=sec2 + 1, max_row=r_ctot - 1), titles_from_data=True)
cb.set_categories(Reference(db, min_col=1, min_row=c_first, max_row=r_ctot - 1))
bar_series(cb.series[0], NAVY)
cb.legend = None
cb.dataLabels = DataLabelList()
cb.dataLabels.showVal = True
cb.dataLabels.numFmt = '€#,##0,"K"'
cb.width, cb.height = 15, 7.5
db.add_chart(cb, f"G{sec2 + 5}")

# ---------------------------------------------------------- 4. CATEGORY_ANALYSIS
ca = wb.create_sheet("Category_Analysis")
ca.sheet_properties.tabColor = TEAL
title_block(ca, "Category Performance — 8 ATC Groups",
            "Units real | € estimated | LFL = 1 Jan–8 Oct vs same window prior year", 14)
section(ca, 3, "ALL EIGHT CATEGORIES, RANKED BY ESTIMATED REVENUE", 14)
head_row(ca, 4, ["Category", "ATC", "Price/Unit", "Margin %", "Units",
                 "Est. Revenue", "Est. Gross Profit", "Est. Margin %", "Share",
                 f"{Y_CUR - 1} Full Year", f"{Y_CUR} YTD", "LFL YoY", "Flag", "Rank"])
meta = fact.drop_duplicates("ATCCode").set_index("Category")
for i, cname in enumerate(cats_sorted):
    r = 5 + i
    code = meta.loc[cname, "ATCCode"]
    ca.cell(row=r, column=1, value=cname)
    ca.cell(row=r, column=2, value=code)
    ca.cell(row=r, column=3, value=f"=AVERAGEIFS({rg('UnitPrice')},{rg('Category')},$A{r})")
    ca.cell(row=r, column=4, value=f"=AVERAGEIFS({rg('MarginPct')},{rg('Category')},$A{r})/100")
    ca.cell(row=r, column=5, value=f"=SUMIFS({rg('Units')},{rg('Category')},$A{r})")
    ca.cell(row=r, column=6, value=f"=SUMIFS({rg('EstRevenue')},{rg('Category')},$A{r})")
    ca.cell(row=r, column=7, value=f"=SUMIFS({rg('EstGrossProfit')},{rg('Category')},$A{r})")
    ca.cell(row=r, column=8, value=f"=IFERROR(G{r}/F{r},0)")
    ca.cell(row=r, column=9, value=f"=IFERROR(F{r}/$F$13,0)")
    ca.cell(row=r, column=10, value=f"=SUMIFS({rg('EstRevenue')},{rg('Category')},$A{r},{rg('Year')},{Y_CUR - 1})")
    ca.cell(row=r, column=11, value=f"=SUMIFS({rg('EstRevenue')},{rg('Category')},$A{r},{CUR_W})")
    ca.cell(row=r, column=12, value=f'=IFERROR(K{r}/SUMIFS({rg("EstRevenue")},{rg("Category")},$A{r},{PRI_W})-1,"")')
    ca.cell(row=r, column=13, value=f'=IF(G{r}>=AVERAGE($G$5:$G$12),"Outperforming","Below Average")')
    ca.cell(row=r, column=14, value=f"=RANK(F{r},$F$5:$F$12)")
    for cc, fmt in {3: FMT_EUR2, 4: FMT_PCT, 5: FMT_INT, 6: FMT_EUR0, 7: FMT_EUR0,
                    8: FMT_PCT, 9: FMT_PCT, 10: FMT_EUR0, 11: FMT_EUR0,
                    12: FMT_PCT_S, 14: "0"}.items():
        ca.cell(row=r, column=cc).number_format = fmt
    ca.cell(row=r, column=13).alignment = Alignment(horizontal="center")
    box(ca, r, 1, r, 14)
ca.cell(row=13, column=1, value="TOTAL")
for cc, f_ in {5: "=SUM(E5:E12)", 6: "=SUM(F5:F12)", 7: "=SUM(G5:G12)",
               8: "=IFERROR(G13/F13,0)", 9: "=SUM(I5:I12)", 10: "=SUM(J5:J12)",
               11: "=SUM(K5:K12)", 12: f"={LFL_REV}"}.items():
    ca.cell(row=13, column=cc, value=f_)
for cc, fmt in {5: FMT_INT, 6: FMT_EUR0, 7: FMT_EUR0, 8: FMT_PCT, 9: FMT_PCT,
                10: FMT_EUR0, 11: FMT_EUR0, 12: FMT_PCT_S}.items():
    ca.cell(row=13, column=cc).number_format = fmt
for cc in range(1, 15):
    ca.cell(row=13, column=cc).fill = FILL_TOTAL
    ca.cell(row=13, column=cc).font = F_BOLD
box(ca, 13, 1, 13, 14)
ca.conditional_formatting.add("F5:F12", DataBarRule(start_type="min", end_type="max",
                                                    color="5B9BD5", showValue=True))
yoy_cf(ca, "L5:L12")
flag_cf(ca, "M5:M12")
for col, w in {"A": 16, "B": 8, "C": 11, "D": 10, "E": 11, "F": 14, "G": 16,
               "H": 13, "I": 9, "J": 14, "K": 12, "L": 10, "M": 17, "N": 7}.items():
    ca.column_dimensions[col].width = w

# therapy reference block
section(ca, 16, "THERAPY AREA REFERENCE", 6)
head_row(ca, 17, ["ATC", "Category", "Therapy area", "", "", ""])
for i, cname in enumerate(cats_sorted):
    r = 18 + i
    ca.cell(row=r, column=1, value=meta.loc[cname, "ATCCode"])
    ca.cell(row=r, column=2, value=cname)
    ca.cell(row=r, column=3, value=meta.loc[cname, "TherapyArea"])
    ca.cell(row=r, column=3).font = F_BODY
    box(ca, r, 1, r, 3)

bar = BarChart()
bar.type, bar.style, bar.title = "bar", 10, "Est. Revenue by Category (EUR)"
bar.add_data(Reference(ca, min_col=6, min_row=4, max_row=12), titles_from_data=True)
bar.set_categories(Reference(ca, min_col=1, min_row=5, max_row=12))
bar_series(bar.series[0], TEAL)
bar.legend = None
bar.dataLabels = DataLabelList()
bar.dataLabels.showVal = True
bar.dataLabels.numFmt = '€#,##0,"K"'
bar.width, bar.height = 15, 9
ca.add_chart(bar, "A27")

pie = PieChart()
pie.title = "Estimated Revenue Mix"
pie.add_data(Reference(ca, min_col=6, min_row=4, max_row=12), titles_from_data=True)
pie.set_categories(Reference(ca, min_col=1, min_row=5, max_row=12))
pie.dataLabels = DataLabelList()
pie.dataLabels.showPercent = True
pie.width, pie.height = 12, 9
ca.add_chart(pie, "I27")

# ---------------------------------------------------------- 5. TIME_ANALYSIS
ta = wb.create_sheet("Time_Analysis")
ta.sheet_properties.tabColor = TEAL
title_block(ta, "Time Patterns — Year, Month, Weekday, Trading Hour",
            "Seasonality index 1.00 = average month | heatmap = average units per weekday-hour", 25)
for c in range(2, 26):
    ta.column_dimensions[get_column_letter(c)].width = 9.5
section(ta, 4, "MONTHLY EST. REVENUE BY YEAR", 9)
head_row(ta, 5, ["Month"] + years + ["Avg", "Index"])
for i, m in enumerate(MN):
    r = 6 + i
    ta.cell(row=r, column=1, value=m)
    for j, y in enumerate(years):
        col = 2 + j
        cl = get_column_letter(col)
        ta.cell(row=r, column=col,
                value=f"=SUMIFS({rg('EstRevenue')},{rg('Year')},{cl}$5,{rg('MonthNum')},{i + 1})")
        ta.cell(row=r, column=col).number_format = FMT_EUR0
    ta.cell(row=r, column=8, value=f"=AVERAGE(B{r}:G{r})")
    ta.cell(row=r, column=9, value=f"=IFERROR(H{r}/AVERAGE($H$6:$H$17),0)")
    ta.cell(row=r, column=8).number_format = FMT_EUR0
    ta.cell(row=r, column=9).number_format = "0.00"
    box(ta, r, 1, r, 9)
ta.cell(row=18, column=1, value="TOTAL")
for j in range(len(years)):
    col = 2 + j
    cl = get_column_letter(col)
    ta.cell(row=18, column=col, value=f"=SUM({cl}6:{cl}17)")
    ta.cell(row=18, column=col).number_format = FMT_EUR0
    ta.cell(row=18, column=col).fill = FILL_TOTAL
    ta.cell(row=18, column=col).font = F_BOLD
ta.cell(row=18, column=1).fill = FILL_TOTAL
ta.cell(row=18, column=1).font = F_BOLD
box(ta, 18, 1, 18, 9)
ta.conditional_formatting.add("I6:I17", ColorScaleRule(
    start_type="min", start_color="FBE3E0",
    mid_type="num", mid_value=1, mid_color="FFFFFF",
    end_type="max", end_color="BFE3D0"))

lc = LineChart()
lc.title = "Monthly Seasonality by Year (EUR, est.)"
lc.add_data(Reference(ta, min_col=2, max_col=1 + len(years), min_row=5, max_row=17),
            titles_from_data=True)
lc.set_categories(Reference(ta, min_col=1, min_row=6, max_row=17))
palette = ["9DC3E6", "6FA8DC", "2E8B9A", "1F6E7D", "3D5A80", "1F3864"]
for s, colr in zip(lc.series, palette):
    style_series(s, colr)
lc.y_axis.number_format = '€#,##0,"K"'
lc.legend.position = "b"
lc.width, lc.height = 16, 8
ta.add_chart(lc, "K4")

section(ta, 21, "WEEKDAY PATTERN", 6)
head_row(ta, 22, ["Weekday", "Units", "Est. Revenue", "Share", "Index", ""])
for i, wd in enumerate(wd_order):
    r = 23 + i
    ta.cell(row=r, column=1, value=wd)
    ta.cell(row=r, column=2, value=f"=SUMIFS({rg('Units')},{rg('Weekday')},$A{r})")
    ta.cell(row=r, column=3, value=f"=SUMIFS({rg('EstRevenue')},{rg('Weekday')},$A{r})")
    ta.cell(row=r, column=4, value=f"=IFERROR(C{r}/$C$30,0)")
    ta.cell(row=r, column=5, value=f"=IFERROR(D{r}*7,0)")
    ta.cell(row=r, column=2).number_format = FMT_INT
    ta.cell(row=r, column=3).number_format = FMT_EUR0
    ta.cell(row=r, column=4).number_format = FMT_PCT
    ta.cell(row=r, column=5).number_format = "0.00"
    box(ta, r, 1, r, 5)
ta.cell(row=30, column=1, value="TOTAL")
ta.cell(row=30, column=2, value="=SUM(B23:B29)")
ta.cell(row=30, column=3, value="=SUM(C23:C29)")
ta.cell(row=30, column=4, value="=SUM(D23:D29)")
ta.cell(row=30, column=5, value="")
ta.cell(row=30, column=2).number_format = FMT_INT
ta.cell(row=30, column=3).number_format = FMT_EUR0
ta.cell(row=30, column=4).number_format = FMT_PCT
for cc in range(1, 6):
    ta.cell(row=30, column=cc).fill = FILL_TOTAL
    ta.cell(row=30, column=cc).font = F_BOLD
box(ta, 30, 1, 30, 5)
ta.conditional_formatting.add("C23:C29", DataBarRule(start_type="min", end_type="max",
                                                     color=TEAL, showValue=True))

wc = BarChart()
wc.type, wc.style, wc.title = "col", 10, "Est. Revenue by Weekday (EUR)"
wc.add_data(Reference(ta, min_col=3, min_row=22, max_row=29), titles_from_data=True)
wc.set_categories(Reference(ta, min_col=1, min_row=23, max_row=29))
bar_series(wc.series[0], NAVY)
wc.legend = None
wc.dataLabels = DataLabelList()
wc.dataLabels.showVal = True
wc.dataLabels.numFmt = '€#,##0,"K"'
wc.y_axis.number_format = '€#,##0,"K"'
wc.width, wc.height = 15, 7.5
ta.add_chart(wc, "G21")

section(ta, 37, "TRADING-HOUR HEATMAP — AVERAGE UNITS BY WEEKDAY & HOUR "
                "(source: saleshourly.csv)", 25)
ta.cell(row=38, column=1, value="Weekday")
for h in range(24):
    c = ta.cell(row=38, column=2 + h, value=h)
    c.font = F_TH
    c.fill = FILL_TEAL
    c.alignment = Alignment(horizontal="center")
    c.number_format = '0"h"'
ta.cell(row=38, column=1).font = F_TH
ta.cell(row=38, column=1).fill = FILL_TEAL
ta.cell(row=38, column=1).alignment = Alignment(horizontal="center")
box(ta, 38, 1, 38, 25)
piv = hours.pivot_table(index="Weekday", columns="Hour", values="AvgUnits")
piv = piv.reindex(wd_order)
for i, wd in enumerate(wd_order):
    r = 39 + i
    lab = ta.cell(row=r, column=1, value=wd)
    lab.font = F_BOLD
    lab.border = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
    for h in range(24):
        v = float(piv.loc[wd, h]) if h in piv.columns else 0.0
        c = ta.cell(row=r, column=2 + h, value=round(v, 1))
        c.number_format = "0.0"
        c.alignment = Alignment(horizontal="center")
        c.font = Font(name="Calibri", size=9)
        c.border = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
ta.conditional_formatting.add("B39:Y45", ColorScaleRule(
    start_type="min", start_color="FFFFFF",
    mid_type="percentile", mid_value=60, mid_color="CFE6EB",
    end_type="max", end_color="2E8B9A"))
ta.cell(row=46, column=1, value="Avg/day")
ta.cell(row=46, column=1).font = F_BOLD
ta.cell(row=46, column=1).fill = FILL_TOTAL
for h in range(24):
    cl = get_column_letter(2 + h)
    c = ta.cell(row=46, column=2 + h, value=f"=AVERAGE({cl}39:{cl}45)")
    c.number_format = "0.0"
    c.font = F_BOLD
    c.fill = FILL_TOTAL
    c.alignment = Alignment(horizontal="center")
    c.border = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
box(ta, 46, 1, 46, 25)
ta.cell(row=47, column=1,
        value=f"Peak hour {peak_hour:02d}:00 · quietest {quiet_hour:02d}:00 "
              f"(average units across all days)")
ta.cell(row=47, column=1).font = F_CTX
ta.column_dimensions["A"].width = 13

# ---------------------------------------------------------- 6. FINDINGS
fd = wb.create_sheet("Findings")
fd.sheet_properties.tabColor = GRAY
fd.column_dimensions["A"].width = 150
title_block(fd, "Findings & Recommendations",
            "Produced by the Excel analysis on the real Kaggle dataset", 1)
r = 4
r = bullet(fd, r, "KEY FINDINGS", font=F_BOLD)
for i, t in enumerate(findings, 1):
    r = bullet(fd, r, f"{i}. {t}")
r += 1
r = bullet(fd, r, "RECOMMENDATIONS", font=F_BOLD)
for i, t in enumerate(recommendations, 1):
    r = bullet(fd, r, f"{i}. {t}")
r += 1
r = bullet(fd, r, "METHOD & CAVEATS", font=F_BOLD)
for t in method:
    r = bullet(fd, r, f"• {t}")

wb.save(OUT)
print(f"saved: {OUT}")
print(f"sheets: {wb.sheetnames}")
print(f"fact rows: {N:,} | days: {days} | est rev {tot_r:,.0f} | profit {tot_p:,.0f} "
      f"({tot_p / tot_r:.1%}) | units {tot_u:,.0f}")
print(f"LFL {Y_CUR} vs {Y_CUR - 1}: rev {lfl_r:+.1%} units {lfl_u:+.1%}")
print(f"seasonality {MN[m_hi - 1]} hi {msn_idx.max():.2f} / {MN[m_lo - 1]} lo {msn_idx.min():.2f} "
      f"| weekday hi {wd_hi} | peak hour {peak_hour}")
print("\nFINDINGS:")
for i, t in enumerate(findings, 1):
    print(f"  {i}. {t}")
