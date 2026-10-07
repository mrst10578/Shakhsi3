# Shakhsi3 | Independent Dynamic Panel GMM Research

This repository is **independent** of `Shakhsi2` and all previous Linear projects. It contains two **separate research tracks** based on source files emailed on 2026-09-30 and methodology screenshots emailed on 2026-10-07. Do not pool these two datasets or treat their effects as one study.

## Datasets

| Track | Dataset | Cross-sections | Years | Rows | Outcomes |
|---|---|---:|---|---:|---|
| Digital economy and technology spillovers | `data/digital_panel.csv` | 47 | 2005–2022 | 846 | Growth, log(Productivity) |
| AI investment and patents | `data/ai_panel.csv` | 30 | 2016–2024 | 270 | log(HighTech_Exports), Unemployment |

Both input spreadsheets were balanced, had unique ISO3-Year keys, and contained no blank entries. **Missing values are not evidence that original measurements are correct.** AI investment is zero in five cases, so `ln(1+x)` is used. Growth can be negative, so it is not logged. Productivity is strictly positive in the provided panel. Neither panel contains Iran.

## Run in Stata 18

Start Stata from the repository root, then:

```stata
do stata/01_preflight.do digital
do stata/02_estimate.do digital
do stata/01_preflight.do ai
do stata/02_estimate.do ai
```

`xtabond2` must be installed before estimating (via the trusted SSC package and associated dependencies). Logs are placed under `outputs/`. **No Stata estimates are claimed in this repository until Stata has actually run.** Check the pre-estimation diagnostics before trusting dynamic-panel estimates. Model choice is conditional on econometric assumptions and diagnostics.

**Difference-in-Hansen correction:** `xtabond2` reports group-specific Difference-in-Hansen automatically when using Mata and suitable instrument groups, especially `gmm(..., split)`. Its `noleveleq` option requests Difference GMM, not a Difference-in-Hansen test. Do not treat `p > 0.05` as proof of instrument validity, particularly if instrument proliferation weakens the Hansen test.

## Audit and reproducibility

- `docs/digital_audit.json`, `docs/ai_audit.json` include country/year coverage, missing/negative/zero values and largest correlations.
- `tests/test_data.py` checks source integrity without third-party libraries. Run: `python tests/test_data.py`.
- `stata/01_preflight.do` checks panel keys, unit roots, pairwise correlations, VIF, and stores logs.
- `stata/02_estimate.do` specifies restricted lag windows with collapsed instruments, separate groups for Difference-in-Hansen, two-step robust SE with finite-sample correction, and country/time structure.
- `docs/METHODOLOGY_FA.md` documents caveats, source dictionary definitions and follow-up steps.

**Source mapping:** World Bank WDI and CSET are described in the supplied dictionaries, but the downloaded sheets were not individually reconciled with original time-series feeds. These are *provided research data*, not independently verified WDI/CSET extracts.

Independent Linear project: [Shakhsi3 | Independent Panel GMM Studies](https://linear.app/zhstt13/project/shakhsi3-independent-panel-gmm-studies-6c60554e43c7).

### Preliminary local diagnostics (not Stata results)

`python tests/run_exploratory_preflight.py` writes `docs/exploratory_preflight.json`; `docs/PRELIMINARY_FINDINGS_FA.md` explains the results and caveats. Pooled VIFs: digital Internet 4.039 / Broadband 4.763, AI ln1p investment 1.578 / ln1p patents 1.572. **26 of 30 countries show lower AI patent counts in 2024 vs 2023**, requiring source-vintage verification and robustness excluding 2024. Country-specific ADF checks are **not** panel IPS and are not a license to report a final GMM estimate. 