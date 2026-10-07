version 18.0
args study
set more off
capture mkdir outputs
if "`study'" != "digital" & "`study'" != "ai" {
    display as error "Run: do stata/02_estimate.do digital OR do stata/02_estimate.do ai"
    exit 198
}
capture which xtabond2
if _rc {
    display as error "xtabond2 is not installed. Install a trusted Stata xtabond2 package before running."
    exit 499
}
capture log close _all
log using "outputs/`study'_gmm.log", replace text
if "`study'" == "digital" {
    import delimited using "data/digital_panel.csv", clear varnames(1) case(preserve)
    gen double ln_prod = ln(Productivity) if Productivity > 0
    local y1 "Growth"
    local y2 "ln_prod"
    local regressors "Internet Broadband ICT_Exports Unemployment Inflation RnD"
    local gmm_endogenous "Internet Broadband ICT_Exports"
    local iv_controls "Unemployment Inflation RnD"
}
else {
    import delimited using "data/ai_panel.csv", clear varnames(1) case(preserve)
    assert AI_Investment >= 0 & AI_Patents >= 0
    assert HighTech_Exports > 0
    gen double ln_hightech = ln(HighTech_Exports)
    gen double ln_ai_invest = ln(1 + AI_Investment)
    gen double ln_ai_patent = ln(1 + AI_Patents)
    local y1 "ln_hightech"
    local y2 "Unemployment"
    local regressors "ln_ai_invest ln_ai_patent GDP_Growth"
    local gmm_endogenous "ln_ai_invest ln_ai_patent"
    local iv_controls "GDP_Growth"
}
encode ISO3, gen(panel_id)
isid panel_id Year
xtset panel_id Year
quietly tabulate Year, generate(year_dummy_)
local n_years = r(r)
local timevars ""
forvalues j = 2/`n_years' {
    local timevars "`timevars' year_dummy_`j'"
}

foreach y in `y1' `y2' {
    display as text "========== Outcome `y': pooled OLS baseline =========="
    regress `y' L.`y' `regressors' `timevars', vce(cluster panel_id)
    estimates store ols_`study'_`y'
    display as text "========== Outcome `y': country FE baseline =========="
    xtreg `y' L.`y' `regressors' `timevars', fe vce(cluster panel_id)
    estimates store fe_`study'_`y'
    display as text "========== Outcome `y': two-step System GMM =========="
    * Lag-restricted collapsed instruments to limit proliferation.
    * split enables difference-in-Hansen tests for levels vs differences.
    * Endogeneity classifications must be reassessed in robustness analysis.
    xtabond2 `y' L.`y' `regressors' `timevars', ///
        gmm(L.`y', lag(1 2) collapse split) ///
        gmm(`gmm_endogenous', lag(2 3) collapse) ///
        iv(`iv_controls' `timevars', eq(level)) ///
        twostep robust small artests(2)
    estimates store sysgmm_`study'_`y'
    * Read instrument count, # groups, AR(1)/AR(2), Hansen and difference-in-Hansen.
    * Check Hansen weakening near 1.0; >0.05 does NOT prove validity.
    ereturn list
}
log close
