version 18.0
args study
set more off
capture mkdir outputs
if "`study'" != "digital" & "`study'" != "ai" {
    display as error "Run: do stata/01_preflight.do digital OR do stata/01_preflight.do ai"
    exit 198
}
capture log close _all
log using "outputs/`study'_preflight.log", replace text

if "`study'" == "digital" {
    import delimited using "data/digital_panel.csv", clear varnames(1) case(preserve)
    local expected_n = 47
    local expected_t = 18
    local predictors "Internet Broadband ICT_Exports Unemployment Inflation RnD"
    generate double ln_prod = ln(Productivity) if Productivity > 0
    local y1 "Growth"
    local y2 "ln_prod"
}
else {
    import delimited using "data/ai_panel.csv", clear varnames(1) case(preserve)
    local expected_n = 30
    local expected_t = 9
    assert AI_Investment >= 0 & AI_Patents >= 0
    assert HighTech_Exports > 0
    gen double ln_hightech = ln(HighTech_Exports)
    gen double ln_ai_invest = ln(1 + AI_Investment)
    gen double ln_ai_patent = ln(1 + AI_Patents)
    local predictors "ln_ai_invest ln_ai_patent GDP_Growth"
    local y1 "ln_hightech"
    local y2 "Unemployment"
}

encode ISO3, generate(panel_id)
assert !missing(panel_id, Year)
isid panel_id Year
bysort panel_id (Year): assert Year == Year[1] + _n - 1
quietly levelsof Year, local(all_years)
local nyears : word count `all_years'
quietly levelsof panel_id, local(all_panels)
local npanels : word count `all_panels'
assert `nyears' == `expected_t'
assert `npanels' == `expected_n'
xtset panel_id Year
xtdescribe
summarize `y1' `y2' `predictors', detail

* Panel unit-root diagnostics are exploratory; small T and cross-section
* dependence may invalidate asymptotic calibration. Read the methods note.
foreach x in `y1' `y2' `predictors' {
    display as text "========== Unit-root diagnostic for `x' =========="
    capture noisily xtunitroot ips `x', lags(1)
    if _rc display as error "IPS unavailable/not identified for `x' (r=" _rc ")"
    capture noisily xtunitroot fisher `x', dfuller lags(1)
    if _rc display as error "Fisher ADF unavailable/not identified for `x' (r=" _rc ")"
}

* Pairwise correlation is NOT a causal or conditional association.
pwcorr `predictors', sig obs
* Pooled VIF is a collinearity screen only, not a substitute for dynamic-panel checks.
quietly regress `y1' `predictors'
estat vif
log close