# -*- coding: utf-8 -*-
"""
OECD Population Parsing — CORRECTED (no Weibull double-count)
============================================================

Fixes the methodological flaw flagged in review: the original script applied a
Weibull survival weight to UN World Population Prospects data that ALREADY embeds
mortality, then renormalised to preserve the total — a double-count that shifts
population mass from the oldest cohort (Silent) toward younger cohorts.

This corrected version maps single-year-of-age directly to generations with NO
survival re-weighting. UN WPP projections are used as-is, because they are already
mortality- and migration-adjusted.

USAGE
-----
1. Export "Total population by single year of age, both sexes" for all OECD members
   from the UN WPP 2024 data portal (https://population.un.org/dataportal/),
   years 2023–2100, as a tab-separated .txt (as in the original workflow).
2. Set INPUT_FILE below and run:  python oecd_population_parsing_CORRECTED.py
3. Output: generation_population_by_year_2023_2100_CORRECTED.csv (millions).

Requires: pandas, numpy.
"""

import re
import numpy as np
import pandas as pd

INPUT_FILE = "unpopulation_dataportal_20251025160640.txt"   # <-- set to your UN export
OUTPUT_FILE = "generation_population_by_year_2023_2100_CORRECTED.csv"

# --- Generation definitions (birth-year ranges) ---
GENERATIONS = {
    "Silent":      (1925, 1945),
    "Boomers":     (1946, 1964),
    "Gen X":       (1965, 1979),
    "Millennials": (1980, 1994),
    "Gen Z":       (1995, 2009),
    "Gen Alpha":   (2010, 2024),
    "Gen Beta":    (2025, 2039),
    "Following":   (2040, 3000),
}
YEARS = list(range(2023, 2101))
AGE_MAX = 120


def load_un(path):
    """Load the UN data-portal export and aggregate to OECD totals by age bracket & year."""
    df = pd.read_csv(path, sep="\t")
    # Keep only what we need; UN exports carry many metadata columns.
    # Expected usable fields after export: a country, a year, an age label/bracket, a value.
    # Adjust these names to match your export's headers if they differ.
    val_col = "Value" if "Value" in df.columns else df.columns[-1]
    age_col = next(c for c in df.columns if "Age" in c and ("Label" in c or "Bracket" in c or c == "Age"))
    year_col = next(c for c in df.columns if c.lower() in ("time", "year", "timelabel"))
    agg = (df.groupby([year_col, age_col])[val_col].sum().reset_index())
    pivot = agg.pivot_table(index=year_col, columns=age_col, values=val_col)
    pivot.index.name = "Year"
    return pivot.reset_index()


def parse_bracket(col):
    """'0-4' -> (0,4);  '100+' -> (100,120)."""
    if isinstance(col, str) and re.match(r"^\d{1,3}\-\d{1,3}$", col):
        a, b = map(int, col.split("-"))
        return min(a, b), max(a, b)
    if isinstance(col, str) and re.match(r"^\d{1,3}\+$", col):
        return int(col[:-1]), AGE_MAX
    return None


def reconstruct_single_year(pivot):
    """Least-squares reconstruction of single-year ages from brackets (kept from original)."""
    usable = []
    for col in pivot.columns:
        if col == "Year":
            continue
        rng = parse_bracket(col)
        if rng is not None:
            usable.append((col, rng[0], rng[1]))
    out = {}
    for _, row in pivot.iterrows():
        year = int(row["Year"])
        A, b = [], []
        for col, lo, hi in usable:
            v = row.get(col, np.nan)
            if pd.isna(v):
                continue
            vec = np.zeros(AGE_MAX + 1)
            vec[lo:hi + 1] = 1.0
            A.append(vec)
            b.append(float(v))
        if not A:
            out[year] = np.zeros(AGE_MAX + 1)
            continue
        x, *_ = np.linalg.lstsq(np.vstack(A), np.array(b), rcond=None)
        out[year] = np.maximum(x, 0.0)     # single-year age vector (already mortality-adjusted)
    return out


def to_generations(age_by_year):
    """Map single-year ages to generations by birth year. NO survival re-weighting."""
    rows = []
    for year, ages in sorted(age_by_year.items()):
        rec = {"Year": year}
        for gen, (b0, b1) in GENERATIONS.items():
            # birth year = year - age  ->  age = year - birth_year
            age_lo = max(0, year - b1)          # youngest member's age
            age_hi = min(AGE_MAX, year - b0)    # oldest member's age
            rec[gen] = float(ages[age_lo:age_hi + 1].sum()) if age_hi >= age_lo else 0.0
        rows.append(rec)
    return pd.DataFrame(rows).sort_values("Year").reset_index(drop=True)


def main():
    pivot = load_un(INPUT_FILE)
    ages = reconstruct_single_year(pivot)
    gen = to_generations(ages)
    for g in GENERATIONS:
        gen[g] = (gen[g] / 1_000_000).round(0).astype(int)   # to millions
    gen.to_csv(OUTPUT_FILE, index=False)
    print("Done. Wrote", OUTPUT_FILE)
    print(gen.head(10).to_string(index=False))


if __name__ == "__main__":
    main()
