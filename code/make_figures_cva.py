# -*- coding: utf-8 -*-
"""
make_figures_cva.py — regenerates the model figures of the CVA paper from the deposited series
(Figs. 1, 2, 3, 5, 6, 7; Figs. 4 and 8 come from aum_migration.py). Styling follows the CVA/Ledger
template guidance (8 pt sans, faint 1/4 pt grid, 1/2 pt frame, 600 DPI). The regenerated plots carry
the same data as the manuscript figures; cosmetic details may differ from the typeset versions.
Writes ../figures/cva_fig{1,2,3,5,6,7}_*.png
"""
import json, os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import rcParams

HERE = os.path.dirname(os.path.abspath(__file__))
D = lambda f: os.path.join(HERE, "..", "data", f)
OUT = os.path.join(HERE, "..", "figures"); os.makedirs(OUT, exist_ok=True)
rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["Liberation Sans", "Arial", "Helvetica", "DejaVu Sans"], "font.size": 8, "axes.linewidth": 0.5, "grid.linewidth": 0.25,
                 "grid.color": "#bbbbbb", "lines.linewidth": 1.0, "legend.fontsize": 7.5, "axes.titlesize": 8.5})

ms = json.load(open(D("model_series.json"))); scen = json.load(open(D("newscen.json")))
ip = json.load(open(D("inst_params.json"))); comp = json.load(open(D("comp.json")))
W, S, IC = ms["wealth"], ms["supply"], ip["ic"]
YEARS = list(range(2023, 2101)); Y = np.array(YEARS)
COH = ["Silent", "Boomers", "Gen X", "Millennials", "Gen Z", "Gen Alpha", "Gen Beta", "Following"]
SPOT = {2023: 42265, 2024: 93460, 2025: 87502, 2026: 62900}
DELTA = 0.66

def price(y, alloc):
    return DELTA * sum(w * a for w, a in zip(W[str(y)], alloc)) * 1e12 / (S[str(y)] - IC[str(y)])
P = {s: np.array([price(y, scen[s]) for y in YEARS]) for s in ("low", "med", "high")}

def save(fig, name):
    fig.tight_layout(); fig.savefig(os.path.join(OUT, name), dpi=600); plt.close(fig); print("wrote", name)

# Fig. 1 — floor vs related long-horizon models, 2023–2045, log scale
fig, ax = plt.subplots(figsize=(6.5, 3.6), dpi=600)
m = Y <= 2045
ax.fill_between(Y[m], P["low"][m], P["high"][m], color="#8da9c4", alpha=0.35, label="Demographic floor, Low–High band")
ax.plot(Y[m], P["med"][m], color="#1f3864", label="Medium (this paper)")
cy = sorted(int(k) for k in comp)
for key, lab, ls in (("rudd", "Rudd & Porter (2025), supply–demand", "--"), ("quant", "Quantile Model v2", ":"),
                     ("b1m", "Bitcoin One Million", "-."), ("s2f", "Stock-to-Flow / Rainbow", (0, (3, 1, 1, 1)))):
    xs = [y for y in cy if comp[str(y)].get(key)]; ys = [comp[str(y)][key] for y in xs]
    ax.plot(xs, ys, linestyle=ls, color="#555555", label=lab)
ax.plot(list(SPOT), list(SPOT.values()), "o", color="black", ms=3, label="Observed spot (2026 = mid-year)")
ax.set_yscale("log"); ax.set_xlabel("Year"); ax.set_ylabel("Bitcoin price (USD, log scale)")
ax.grid(True, which="both"); ax.set_axisbelow(True); ax.legend(frameon=False, loc="upper left")
save(fig, "cva_fig1_models.png")

# Fig. 2 — full-horizon price path by scenario, linear
fig, ax = plt.subplots(figsize=(6.5, 3.4), dpi=600)
ax.fill_between(Y, P["low"] / 1e6, P["high"] / 1e6, color="#8da9c4", alpha=0.35, label="Low–High band")
ax.plot(Y, P["med"] / 1e6, color="#1f3864", label="Medium")
ax.plot(list(SPOT), [v / 1e6 for v in SPOT.values()], "o", color="black", ms=3, label="Observed spot 2023–2026")
for y, lab in ((2050, "2050: $0.24M"), (2100, "2100: $11.0M")):
    i = YEARS.index(y); ax.annotate(lab, (y, P["med"][i] / 1e6), xytext=(-60, 10), textcoords="offset points", fontsize=7,
                                    bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#999999", lw=0.4),
                                    arrowprops=dict(arrowstyle="-", lw=0.5, color="#666666"))
ax.set_xlabel("Year"); ax.set_ylabel("Bitcoin price (USD million, nominal)"); ax.grid(True); ax.set_axisbelow(True)
ax.legend(frameon=False, loc="upper left"); save(fig, "cva_fig2_horizon.png")

# Fig. 3 — tradable float
fig, ax = plt.subplots(figsize=(6.5, 3.0), dpi=600)
sup = np.array([S[str(y)] for y in YEARS]) / 1e6; inst = np.array([IC[str(y)] for y in YEARS]) / 1e6
ax.plot(Y, sup, color="#555555", label="Circulating supply net of lost coins")
ax.plot(Y, sup - inst, color="#1f3864", label="… minus off-market institutional and sovereign coins (tradable float)")
ax.fill_between(Y, sup - inst, sup, color="#e07b39", alpha=0.25, label="Institutional / sovereign coins (1.5M in 2025 → 5.0M cap)")
ax.set_xlabel("Year"); ax.set_ylabel("Million BTC"); ax.grid(True); ax.set_axisbelow(True); ax.legend(frameon=False, loc="lower left")
save(fig, "cva_fig3_float.png")

# Fig. 5 / 6 — generational wealth and shares
Wm = np.array([W[str(y)] for y in YEARS])
colors = ["#bdbdbd", "#8c8c8c", "#8da9c4", "#4f7cac", "#e07b39", "#f2b385", "#c9b1d9", "#7a5c9c"]
fig, ax = plt.subplots(figsize=(6.5, 3.4), dpi=600)
ax.stackplot(Y, Wm.T, labels=COH, colors=colors, linewidth=0.3, edgecolor="white")
ax.set_xlabel("Year"); ax.set_ylabel("OECD household wealth (USD trillion, nominal)"); ax.grid(True); ax.set_axisbelow(True)
ax.legend(frameon=False, loc="upper left", ncol=2); save(fig, "cva_fig5_genwealth.png")
fig, ax = plt.subplots(figsize=(6.5, 3.4), dpi=600)
sh = 100 * Wm / Wm.sum(axis=1, keepdims=True)
for i, c in enumerate(COH):
    ax.plot(Y, sh[:, i], color=colors[i], label=c, linewidth=1.6 if c == "Gen Z" else 1.0)
ax.set_xlabel("Year"); ax.set_ylabel("Share of total OECD wealth (%)"); ax.grid(True); ax.set_axisbelow(True)
ax.legend(frameon=False, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.18)); save(fig, "cva_fig6_genshare.png")

# Fig. 7 — Bitcoin demand by generation, Medium
fig, ax = plt.subplots(figsize=(6.5, 3.4), dpi=600)
dem = DELTA * Wm * np.array(scen["med"])[None, :]
ax.stackplot(Y, dem.T, labels=COH, colors=colors, linewidth=0.3, edgecolor="white")
ax.set_xlabel("Year"); ax.set_ylabel("Bitcoin demand (USD trillion, nominal)"); ax.grid(True); ax.set_axisbelow(True)
ax.legend(frameon=False, loc="upper left", ncol=2); save(fig, "cva_fig7_gendemand.png")
