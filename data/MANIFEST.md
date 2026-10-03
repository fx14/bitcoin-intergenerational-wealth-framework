# Data Manifest — provenance of every file in data/

All files are DERIVED series computed by the authors for the CVA paper. No third-party
microdata are redistributed. Source names refer to the paper's Notes and References.

| File | Contents | Derived from |
|---|---|---|
| `model_series.json` | `wealth`: cohort net worth, USD trillion nominal, 8 cohorts (Silent … Following) × 2023–2100, Medium growth path. `supply`: circulating coins net of estimated lost coins (S_t − L_t in eq. 1). `inst`: legacy institutional-wealth series (not used by eq. 1). | Wealth: OECD Wealth Distribution Database base-year calibration; UN World Population Prospects 2024 cohort populations; 5.2%/yr per-capita net-worth growth; 80/10/10 inheritance matrix; 10% inheritance tax (Section 3). Supply: Bitcoin issuance schedule; lost-coin assumption (3.24M base, +80k in 2023 declining 2%/yr). |
| `newscen.json` | Unconditional crypto share of cohort net worth, scenarios `low`/`med`/`high` (Table 2, Table B1). | Participation × conditional weight, anchored to OeNB (Fessler & Weber 2025), ECB FSR May 2025, Norges Bank 2024, Bank of Canada SDP 2025-4, Fed SCF; post-Gen Z increments are the paper's stated directional assumptions. |
| `inst_params.json` | `ic`: institutional and sovereign coins withheld from tradable float, 2023–2100 (≈1.5M in 2025, +3%/yr, capped at 5.0M ≈2066) = I_t in eq. (1). `low/med/high`: legacy allocation vectors, superseded by `newscen.json`. | Spot-ETF issuer/SEC filings, corporate-treasury 8-K disclosures, sovereign reserve disclosures as of mid-2026, net of retail-held shares (Section 3). |
| `inh_all.json` | Mortality-released wealth by cohort and year, USD trillion nominal (all 8 cohorts) — the input to the AUM-migration funnel (Table 7, Figs. 4 and 8). | Same demographic engine as `model_series.json`. |
| `comp.json` | Comparison trajectories 2025–2045 for Fig. 1 / Table 5: Rudd & Porter supply–demand framework, Bitcoin One Million, Stock-to-Flow/Rainbow family, Quantile Model v2 (published zones; medians not published — interpolated, see Table 5 note). | Interpolated from the published trajectories cited in Section 2. |

Verification: `code/reproduce_cva.py` asserts all 30 Table 3–4 values exactly and every Table 6 row to <1%;
`code/aum_migration.py` recomputes Table 7, the Fig. 4 attrition shares and the Fig. 8 callouts.
