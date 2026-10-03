# -*- coding: utf-8 -*-
"""
aum_migration.py — the banking-paper side of the model (CVA Research Journal 2026 submission):
AUM migration from mortality-released wealth.

Reproduces, from the deposited derived series only:
  * Table 7  — per-decade funnel: wealth released -> exposed to advisor attrition -> institution loss,
               cumulative lost stock at decade-end, recurring fee revenue on that stock
  * Fig. 4   — share of OECD household wealth exposed to advisor attrition per decade
  * Fig. 8   — (a) where each decade's released wealth goes; (b) cumulative institution-loss stock
               as a share of OECD household wealth, with fee-revenue callouts

Inputs (../data/):
  inh_all.json      mortality-released wealth by cohort and year, USD trillion nominal (all 8 cohorts)
  model_series.json 'wealth': cohort net worth by year, USD trillion nominal (Medium scenario)

Assumptions (central, illustrative — see paper Section 5):
  RETAIN   = 0.25   share of heirs retaining the benefactor's advisor (Cerulli: 27% intend, 20% once inherited)
  ATTRIT   = 0.75   = 1 - RETAIN, share exposed to advisor attrition
  NET_LOSS = 0.40   share of the attrition flow that leaves the incumbent sector altogether
  INST     = ATTRIT * NET_LOSS = 0.30 of released wealth = "institution loss"
  FEE_LO/HI = 60 / 80 bps blended wealth-management margin; FEE_MID = 70 bps for the figure

Usage:  cd code && python3 aum_migration.py      (writes ../output/table7.txt and ../figures/fig8_instloss_v2.png)
"""
import json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import rcParams

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
OUT_FIG = os.path.join(HERE, "..", "figures")
OUT_TXT = os.path.join(HERE, "..", "output")
os.makedirs(OUT_FIG, exist_ok=True); os.makedirs(OUT_TXT, exist_ok=True)

RETAIN, NET_LOSS = 0.25, 0.40
ATTRIT = 1 - RETAIN
INST = ATTRIT * NET_LOSS
FEE_LO, FEE_MID, FEE_HI = 0.0060, 0.0070, 0.0080

inh = json.load(open(os.path.join(DATA, "inh_all.json")))
ms = json.load(open(os.path.join(DATA, "model_series.json")))
years = list(range(2023, 2101))
released = np.array([sum(inh[str(y)].values()) for y in years])          # USD T / yr
wealth = np.array([sum(ms["wealth"][str(y)]) for y in years])             # USD T, total OECD household wealth
loss = INST * released
cum_loss = np.cumsum(loss)
share = 100 * cum_loss / wealth
Y = np.array(years)

# ---------- Table 7 ----------
decades = [(a, a + 9) for a in range(2025, 2075, 10)]
rows, cum = [], 0.0
for a, b in decades:
    m = (Y >= a) & (Y <= b)
    rel = released[m].sum(); exp_ = ATTRIT * rel; lost = INST * rel; cum += lost
    attr_share = 100 * exp_ / wealth[m].sum()   # Fig. 4: decade attrition flow / decade sum of annual wealth
    rows.append((f"{a}–{b}", rel, exp_, lost, cum, cum * FEE_LO, cum * FEE_HI, attr_share))
with open(os.path.join(OUT_TXT, "table7.txt"), "w") as f:
    hdr = "Decade | Wealth released | Exposed to attrition (75%) | Institution loss (30%) | Cumulative lost stock | Fee on stock 60–80 bps/yr | Fig. 4 attrition flow, % of wealth per decade"
    print(hdr); f.write(hdr + "\n")
    for r in rows:
        line = f"{r[0]} | ${r[1]:.0f}T | ${r[2]:.0f}T | ${r[3]:.0f}T | ${r[4]:.0f}T | ${r[5]:.2f}–{r[6]:.2f}T | {r[7]:.1f}%"
        print(line); f.write(line + "\n")
    for y in (2035, 2050, 2075):
        i = years.index(y)
        line = f"Fig. 8 callout {y}: stock {share[i]:.1f}% of wealth = ${cum_loss[i]:.0f}T -> ${cum_loss[i]*FEE_MID:.2f}T/yr at 70 bps"
        print(line); f.write(line + "\n")

# ---------- Fig. 8 (template style: 8 pt sans, faint 1/4 pt grid, 1/2 pt frame, 1 pt data, 600 DPI) ----------
rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Liberation Sans", "Arial", "Helvetica", "DejaVu Sans"], "font.size": 8, "axes.linewidth": 0.5,
                 "grid.linewidth": 0.25, "grid.color": "#bbbbbb", "lines.linewidth": 1.0,
                 "xtick.labelsize": 8, "ytick.labelsize": 8, "axes.titlesize": 8.5, "legend.fontsize": 7.5})
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.7, 3.3), dpi=600, gridspec_kw={"width_ratios": [1.05, 1]})

# (a) stacked bars: where each decade's released wealth goes
labels = [r[0] for r in rows]; tot = np.array([r[1] for r in rows])
keep, move, leave = RETAIN * tot, (ATTRIT - INST) * tot, INST * tot
x = np.arange(len(rows))
ax1.bar(x, keep, color="#d9d9d9", edgecolor="black", linewidth=0.4, label="Stays with benefactor's advisor (25%)")
ax1.bar(x, move, bottom=keep, color="#8da9c4", edgecolor="black", linewidth=0.4, label="Moves to another incumbent (45%)")
ax1.bar(x, leave, bottom=keep + move, color="#e07b39", edgecolor="black", linewidth=0.4, label="Leaves the incumbent sector = institution loss (30%)")
for i, t in enumerate(tot):
    ax1.text(i, t * 1.02, f"${t:,.0f}T", ha="center", va="bottom", fontsize=7)
    yc = keep[i] + move[i] + leave[i] / 2
    if leave[i] > 90:
        ax1.text(i, yc, f"${leave[i]:,.0f}T", ha="center", va="center", fontsize=7, color="white", fontweight="bold")
    else:
        ax1.text(i + 0.44, yc, f"${leave[i]:,.0f}T", ha="left", va="center", fontsize=7, color="#c45f1f", fontweight="bold")
ax1.set_xticks(x); ax1.set_xticklabels(labels)
ax1.set_ylabel("Wealth released by mortality in the decade\n(USD trillion, nominal)")
ax1.set_title("(a) Where each decade's released wealth goes", loc="left")
ax1.set_ylim(0, tot.max() * 1.12)
ax1.yaxis.grid(True); ax1.set_axisbelow(True)
ax1.legend(loc="upper left", frameon=False, handlelength=1.2)

# (b) cumulative institution-loss stock as % of OECD household wealth
m = (Y >= 2025) & (Y <= 2075)
ax2.fill_between(Y[m], share[m], color="#e07b39", alpha=0.18)
ax2.plot(Y[m], share[m], color="#e07b39")
for y, ytxt in ((2035, 21.5), (2050, 29), (2075, 36.5)):
    i = years.index(y)
    txt = (f"{y}: {share[i]:.0f}% of OECD wealth = ${cum_loss[i]:,.0f}T lost\n"
           f"→ ≈ ${cum_loss[i]*FEE_MID:,.1f}T per year of fee revenue at 70 bps")
    ax2.plot(y, share[i], "o", color="#e07b39", ms=3)
    ax2.annotate(txt, (y, share[i]), xytext=(2026.5, ytxt), fontsize=6.8, ha="left", va="bottom",
                 bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#999999", lw=0.4),
                 arrowprops=dict(arrowstyle="-", lw=0.5, color="#666666", shrinkB=2))
ax2.set_xlim(2025, 2076); ax2.set_ylim(0, 44)
ax2.set_xlabel("Year"); ax2.set_ylabel("Cumulative institution loss\n(% of total OECD household wealth)")
ax2.set_title("(b) The accumulated stock of AUM lost to incumbents", loc="left")
ax2.grid(True); ax2.set_axisbelow(True)
for ax in (ax1, ax2):
    for s in ax.spines.values(): s.set_linewidth(0.5)
fig.tight_layout(w_pad=2.0)
fig.savefig(os.path.join(OUT_FIG, "fig8_instloss_v2.png"), dpi=600)
print("wrote", os.path.join(OUT_FIG, "fig8_instloss_v2.png"))
