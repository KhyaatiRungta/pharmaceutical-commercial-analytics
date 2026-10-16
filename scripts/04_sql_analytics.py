"""Phase: SQL analytics layer.

Builds data/pharma_sales.db (SQLite) from the prepared CSVs using
sql/01_schema.sql, then executes every analysis query in sql/ and prints
the results. One command, reproducible:

    python scripts/04_sql_analytics.py

Units are real source values; Est* euro columns are estimates (the same
assumptions the Excel / Power BI / HTML deliverables use). 2019 is a
partial year (ends 8 Oct) - queries use like-for-like windows for it.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data"
SQL = BASE / "sql"
DB = DATA / "pharma_sales.db"

FACT_COLS = [
    "Date", "Year", "MonthNum", "MonthName", "Quarter", "YearMonth",
    "Weekday", "ATCCode", "Category", "TherapyArea",
    "Units", "UnitPrice", "EstRevenue", "EstCost", "EstGrossProfit", "MarginPct",
]


def split_statements(sql_text: str) -> list[str]:
    """Split a query file into individual statements.

    Our query files use only line comments ('-- ...') and never embed a
    semicolon inside a string literal, so a simple splitter is safe.
    """
    lines = []
    for line in sql_text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("--"):
            continue
        lines.append(line)
    cleaned = "\n".join(lines)
    return [s.strip() for s in cleaned.split(";") if s.strip()]


def show(curs: sqlite3.Cursor, header: str) -> None:
    rows = curs.fetchall()
    cols = [d[0] for d in curs.description]
    widths = [max(len(c), *(len(str(r[i])) for r in rows)) if rows else len(c)
              for i, c in enumerate(cols)]
    print(f"\n--- {header} ---")
    print(" | ".join(c.ljust(w) for c, w in zip(cols, widths)))
    print("-+-".join("-" * w for w in widths))
    for r in rows:
        print(" | ".join(str(v).ljust(w) for v, w in zip(r, widths)))
    print(f"({len(rows)} row{'s' if len(rows) != 1 else ''})")


def main() -> int:
    # ---------------------------------------------------------------- build
    for path in (DB, Path(str(DB) + "-wal")):
        if path.exists():
            path.unlink()

    conn = sqlite3.connect(DB)
    conn.executescript((SQL / "01_schema.sql").read_text(encoding="utf-8"))

    fact = pd.read_csv(DATA / "pharma_sales_fact.csv", parse_dates=["Date"])
    fact["Date"] = fact["Date"].dt.strftime("%Y-%m-%d")
    missing = set(FACT_COLS) - set(fact.columns)
    if missing:
        print(f"FATAL: fact CSV missing columns {sorted(missing)}", file=sys.stderr)
        return 1
    conn.executemany(
        f"INSERT INTO fact_sales ({', '.join(FACT_COLS)}) "
        f"VALUES ({', '.join('?' * len(FACT_COLS))})",
        [tuple(r) for r in fact[FACT_COLS].itertuples(index=False, name=None)],
    )

    hours = pd.read_csv(DATA / "hour_profile.csv")
    conn.executemany(
        "INSERT INTO hour_profile (Weekday, WeekdayNum, Hour, AvgUnits, AvgEstRevenue) "
        "VALUES (?, ?, ?, ?, ?)",
        [tuple(r) for r in hours.itertuples(index=False, name=None)],
    )
    conn.commit()

    n_fact = conn.execute("SELECT COUNT(*) FROM fact_sales").fetchone()[0]
    n_hr = conn.execute("SELECT COUNT(*) FROM hour_profile").fetchone()[0]
    print(f"Built {DB.relative_to(BASE)}  fact_sales={n_fact} rows  hour_profile={n_hr} rows")
    assert n_fact == 16848, f"expected 16848 fact rows, got {n_fact}"
    assert n_hr == 168, f"expected 168 hour rows, got {n_hr}"

    # ------------------------------------------------------------------ run
    query_files = sorted(SQL.glob("0[2-9]_*.sql"))
    if not query_files:
        print("FATAL: no query files found in sql/", file=sys.stderr)
        return 1

    n_results = 0
    for qf in query_files:
        print("\n" + "=" * 72)
        print(f"sql/{qf.name}")
        print("=" * 72)
        for stmt in split_statements(qf.read_text(encoding="utf-8")):
            curs = conn.execute(stmt)
            if curs.description:
                n_results += 1
                first_line = next(
                    (l for l in stmt.splitlines()
                     if l.strip() and not l.strip().startswith("--")), "")
                show(curs, first_line.strip()[:70])

    conn.close()
    print(f"\nOK - {len(query_files)} query files, {n_results} result sets executed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
