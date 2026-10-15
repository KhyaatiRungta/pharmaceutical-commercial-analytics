"""
Phase 8: Prepare the Kaggle "Pharma sales data" dataset (REAL DATA).
Source: https://www.kaggle.com/datasets/milanzdravkovic/pharma-sales-data
        Milan Zdravkovic, CC BY-NC 4.0. 2014-2019, one pharmacy, 8 ATC groups,
        quantity sold (no revenue in source).

This script converts the wide raw files into analysis-ready tables and applies
DOCUMENTED assumptions (average unit price + gross-margin rate per ATC group)
to estimate revenue/profit. Units sold are always real source values.

Outputs:
  data/pharma_sales_fact.csv   daily x ATC category long fact table
  data/hour_profile.csv        weekday x hour average trading profile
                                (from saleshourly.csv, used by the heatmap)
"""
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parents[1]
RAW = BASE / "data" / "kaggle_raw"
OUT = BASE / "data"

# code, display name, therapy description, assumed avg unit price EUR,
# assumed gross-margin rate
CATS = [
    ("M01AB", "NSAIDs-Acetic",    "Anti-inflammatory, acetic acid derivatives (e.g. diclofenac)", 3.10, 0.30),
    ("M01AE", "NSAIDs-Propionic", "Anti-inflammatory, propionic acid derivatives (e.g. ibuprofen)", 3.60, 0.30),
    ("N02BA", "Salicylates",      "Analgesics/antipyretics, salicylic acid (e.g. aspirin)",       2.80, 0.28),
    ("N02BE", "Paracetamol",      "Analgesics/antipyretics, anilides (e.g. paracetamol)",         2.40, 0.26),
    ("N05B",  "Anxiolytics",      "Psycholeptics, anxiolytic drugs",                              6.90, 0.34),
    ("N05C",  "Hypnotics",        "Psycholeptics, hypnotics and sedatives",                       7.40, 0.34),
    ("R03",   "Anti-Asthmatics",  "Drugs for obstructive airway diseases (asthma/COPD)",         16.50, 0.22),
    ("R06",   "Antihistamines",   "Antihistamines for systemic use",                              8.20, 0.32),
]
CODES = [c[0] for c in CATS]
meta = pd.DataFrame(CATS, columns=["ATCCode", "Category", "TherapyArea",
                                   "UnitPrice", "MarginRate"])
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday",
            "Saturday", "Sunday"]

# ------------------------------------------------------------ daily -> long
daily = pd.read_csv(RAW / "salesdaily.csv")
daily["Date"] = pd.to_datetime(daily["datum"], format="%m/%d/%Y")
long = daily.melt(id_vars=["Date"], value_vars=CODES,
                  var_name="ATCCode", value_name="Units")
long = long.merge(meta, on="ATCCode", how="left")
long["Units"] = long["Units"].fillna(0).round(2)

long["Year"] = long["Date"].dt.year
long["MonthNum"] = long["Date"].dt.month
long["MonthName"] = long["Date"].dt.strftime("%b")
long["Quarter"] = "Q" + ((long["Date"].dt.month - 1) // 3 + 1).astype(str)
long["YearMonth"] = long["Date"].dt.strftime("%Y-%m")
long["Weekday"] = long["Date"].dt.day_name()

# estimated commercial measures (assumptions applied here, documented above)
long["EstRevenue"] = (long["Units"] * long["UnitPrice"]).round(2)
long["EstCost"] = (long["EstRevenue"] * (1 - long["MarginRate"])).round(2)
long["EstGrossProfit"] = (long["EstRevenue"] - long["EstCost"]).round(2)
long["MarginPct"] = (long["MarginRate"] * 100).round(1)

fact = long[["Date", "Year", "MonthNum", "MonthName", "Quarter", "YearMonth",
             "Weekday", "ATCCode", "Category", "TherapyArea", "Units",
             "UnitPrice", "EstRevenue", "EstCost", "EstGrossProfit",
             "MarginPct"]].sort_values(["Date", "ATCCode"]).reset_index(drop=True)
fact_path = OUT / "pharma_sales_fact.csv"
fact.to_csv(fact_path, index=False, date_format="%Y-%m-%d")

# ------------------------------------------------- hourly trading profile
hourly = pd.read_csv(RAW / "saleshourly.csv")
hourly["dt"] = pd.to_datetime(hourly["datum"], format="%m/%d/%Y %H:%M")
h = hourly.melt(id_vars=["dt", "Hour", "Weekday Name"],
                value_vars=CODES, var_name="ATCCode", value_name="Units")
h = h.merge(meta, on="ATCCode", how="left")
h["Units"] = h["Units"].fillna(0)
h["EstRevenue"] = h["Units"] * h["UnitPrice"]
prof = (h.groupby(["Weekday Name", "Hour"])
         .agg(AvgUnits=("Units", "mean"), AvgEstRevenue=("EstRevenue", "mean"))
         .reset_index()
         .rename(columns={"Weekday Name": "Weekday"}))
prof["WeekdayNum"] = prof["Weekday"].map({d: i for i, d in enumerate(WEEKDAYS)})
prof["AvgUnits"] = prof["AvgUnits"].round(2)
prof["AvgEstRevenue"] = prof["AvgEstRevenue"].round(2)
prof = prof.sort_values(["WeekdayNum", "Hour"])[
    ["Weekday", "WeekdayNum", "Hour", "AvgUnits", "AvgEstRevenue"]]
prof_path = OUT / "hour_profile.csv"
prof.to_csv(prof_path, index=False)

# ------------------------------------------------------------------ report
tot_u, tot_r = fact["Units"].sum(), fact["EstRevenue"].sum()
tot_p = fact["EstGrossProfit"].sum()
print(f"fact rows : {len(fact):,}   dates: {fact['Date'].min():%Y-%m-%d} .. "
      f"{fact['Date'].max():%Y-%m-%d}")
print(f"file      : {fact_path}")
print(f"units     : {tot_u:,.0f}   est revenue: EUR {tot_r:,.0f}   "
      f"est profit: EUR {tot_p:,.0f}  ({tot_p / tot_r:.1%})")
print("\nby year:")
print(fact.groupby("Year").agg(Units=("Units", "sum"),
                               Rev=("EstRevenue", "sum")).round(0))
print("\nby category:")
print(fact.groupby("Category").agg(Units=("Units", "sum"),
                                   Rev=("EstRevenue", "sum"))
      .sort_values("Rev", ascending=False).round(0))
print("\nYoY revenue by category (2019 vs 2018):")
pv = fact.pivot_table(index="Category", columns="Year",
                      values="EstRevenue", aggfunc="sum")
print(((pv[2019] / pv[2018] - 1) * 100).round(1).sort_values(ascending=False)
      .to_string())
print(f"\nhour profile: {prof_path} ({len(prof)} rows, "
      f"hours {prof['Hour'].min()}-{prof['Hour'].max()})")
