#!/usr/bin/env python3
"""Reproduce the price results of:

  "The Bitcoin Intergenerational Wealth Framework: A Demographic Floor for Bitcoin
   and the Reinvention of the Banking Business Model"
  Klaus L. Fuchs and Winnie M. Fuchs — CVA Academic Research Journal 2026
  (CVA CFP 2026: On-Chain Finance and the Reinvention of Financial Infrastructure)

Inputs  : ../data/*.json   (derived model series; provenance in ../data/MANIFEST.md)
Outputs : ../output/tables_cva.txt

  Table 3  recalibrated price by year and scenario        -- reproduced EXACTLY (asserted, 18 values)
  Table 4  floor vs observed spot, 2023-2026              -- reproduced EXACTLY (asserted, 12 values)
  Table 6  one-at-a-time sensitivity of the 2100 price    -- reproduced to <1% (growth rows are the
                                                            analytic approximation stated in the table note)
Equation (1):  P_t = delta * sum_g( W_{g,t} * alpha_{g,t} ) / ( S_t - L_t - I_t )
  W from model_series.json['wealth'] (USD trillion, 8 cohorts), S-L from model_series.json['supply']
  (coins net of lost), I from inst_params.json['ic'] (institutional/sovereign coins off-market).
Then runs aum_migration.py (Table 7, Figs. 4 and 8) and make_figures_cva.py.
"""
import json, os, sys, subprocess
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
D = lambda f: os.path.join(HERE, "..", "data", f)
OUT = os.path.join(HERE, "..", "output"); os.makedirs(OUT, exist_ok=True)

ms   = json.load(open(D("model_series.json")))
scen = json.load(open(D("newscen.json")))        # unconditional crypto share of net worth by cohort: low / med / high
ip   = json.load(open(D("inst_params.json")))    # 'ic': institutional coins withheld from float
W, S, IC = ms["wealth"], ms["supply"], ip["ic"]
DELTA = 0.66
COHORTS = ["Silent", "Boomers", "Gen X", "Millennials", "Gen Z", "Gen Alpha", "Gen Beta", "Following"]

def ic_capped(year, cap):
    """Institutional-coin series as in Section 3: 1.515M in 2025 growing 3%/yr, capped."""
    y = int(year)
    base = IC["2025"] * 1.03 ** (y - 2025) if y >= 2025 else IC[year]
    return min(base, cap)

def price(year, alloc, delta=DELTA, lam=1.0, gscale=None, cap=None):
    w = W[year]
    if gscale is not None:                       # growth-rate rescaling ((1+g)/1.052)^(t-2023), Table 6 note
        w = [x * gscale ** (int(year) - 2023) for x in w]
    demand = sum(wi * ai for wi, ai in zip(w, alloc)) * 1e12
    inst = IC[year] if cap is None else ic_capped(year, cap)
    return delta * demand / (S[year] - lam * inst)

lines = ["CVA paper — deterministic reproduction of equation (1)", ""]

# ---------- Table 3 ----------
T3 = {"2023": (14549, 25120, 43552), "2025": (17195, 29695, 51446), "2030": (24662, 42591, 73419),
      "2050": (136142, 238165, 409706), "2070": (866596, 1576713, 2862286), "2100": (6170858, 10986927, 20820094)}
lines.append("Table 3 — price by year and scenario (USD):")
for y, tgt in T3.items():
    got = tuple(round(price(y, scen[s])) for s in ("low", "med", "high"))
    assert got == tgt, f"MISMATCH Table 3 {y}: got {got}, manuscript {tgt}"
    lines.append(f"  {y}: low {got[0]:>12,}  med {got[1]:>12,}  high {got[2]:>12,}   == manuscript OK")
cagr = (price("2100", scen["med"]) / price("2023", scen["med"])) ** (1 / 77) - 1
lines.append(f"  Medium CAGR 2023–2100: {cagr*100:.1f}%  (manuscript 8.2%)")

# ---------- Table 4 ----------
T4 = {"2023": (14549, 25120, 43552), "2024": (15768, 27233, 47207), "2025": (17195, 29695, 51446), "2026": (18368, 31727, 54931)}
SPOT = {"2023": 42265, "2024": 93460, "2025": 87502, "2026": 62900}
lines += ["", "Table 4 — floor vs observed spot (USD):"]
for y, tgt in T4.items():
    got = tuple(round(price(y, scen[s])) for s in ("low", "med", "high"))
    assert got == tgt, f"MISMATCH Table 4 {y}: got {got}, manuscript {tgt}"
    flag = "High > spot by %.1f%%" % (100 * (got[2] / SPOT[y] - 1)) if got[2] > SPOT[y] else "all three below spot"
    lines.append(f"  {y}: {got}  spot {SPOT[y]:,}  -> {flag}")
lines.append("All 18 + 12 deterministic values reproduced exactly.")

# ---------- Table 6 ----------
base = price("2100", scen["med"])
flat = scen["med"][:5] + [scen["med"][4]] * 3           # post-Gen Z adoption flat at the Gen Z share
rows = [
 ("Asset growth 4.0% (analytic)",   dict(gscale=1.040 / 1.052), 4.54e6),
 ("Asset growth 6.0% (analytic)",   dict(gscale=1.060 / 1.052), 19.69e6),
 ("Bitcoin dominance 0.50",         dict(delta=0.50),            8.32e6),
 ("Bitcoin dominance 0.80",         dict(delta=0.80),           13.32e6),
 ("Institutional cap 3.0M",         dict(cap=3.0e6),             9.09e6),
 ("Institutional cap 8.0M",         dict(cap=8.0e6),            16.00e6),
 ("No institutional subtraction",   dict(lam=0.0),               7.22e6),
]
lines += ["", f"Table 6 — sensitivity of the Medium 2100 price (baseline ${base/1e6:.2f}M):"]
allok = True
for name, kw, tgt in rows:
    got = price("2100", scen["med"], **kw)
    ok = abs(got - tgt) / tgt < 0.01; allok &= ok
    lines.append(f"  {name:34s}: ${got/1e6:6.2f}M  ({(got/base-1)*100:+.0f}%)  manuscript ${tgt/1e6:.2f}M  {'OK' if ok else 'CHECK'}")
got = price("2100", flat); ok = abs(got - 8.65e6) / 8.65e6 < 0.01; allok &= ok
lines.append(f"  {'Post-Gen Z adoption flat at 1.5%':34s}: ${got/1e6:6.2f}M  ({(got/base-1)*100:+.0f}%)  manuscript $8.65M  {'OK' if ok else 'CHECK'}")
assert allok, "a Table 6 row deviates by more than 1%"

report = "\n".join(lines)
open(os.path.join(OUT, "tables_cva.txt"), "w").write(report + "\n")
print(report)

# ---------- AUM migration (Table 7, Figs. 4 and 8) and figures ----------
for script in ("aum_migration.py", "make_figures_cva.py"):
    r = subprocess.run([sys.executable, os.path.join(HERE, script)], capture_output=True, text=True)
    print(r.stdout if r.returncode == 0 else r.stderr)
