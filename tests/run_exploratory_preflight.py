"""Reproducible Python-only preliminary diagnostics; NOT a replacement for Stata or IPS/GMM."""
from pathlib import Path
from collections import defaultdict
import csv, json, math
import numpy as np
from statsmodels.tsa.stattools import adfuller

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'docs'/'exploratory_preflight.json'
SPECS={
 'digital':('digital_panel.csv',['Internet','Broadband','ICT_Exports','Unemployment','Inflation','RnD'],['Growth','Productivity']),
 'ai':('ai_panel.csv',['AI_Investment','AI_Patents','GDP_Growth'],['HighTech_Exports','Unemployment'])
}

def vif(X,columns):
 out={}
 for i,k in enumerate(columns):
  y=X[:,i]; x=np.delete(X,i,axis=1)
  x=np.column_stack([np.ones(len(x)),x])
  b=np.linalg.lstsq(x,y,rcond=None)[0]
  sse=float(np.sum((y-x@b)**2));sst=float(np.sum((y-np.mean(y))**2))
  r2=1-sse/sst if sst>0 else 1.0
  out[k]=None if r2>=1 else round(1/(1-r2),3)
 return out

def two_way_demean(X,groups,years):
 # Balanced panel; country and year means remove additive main effects.
 grand=X.mean(axis=0)
 out=X.copy()
 for i,(g,t) in enumerate(zip(groups,years)):
  out[i] = X[i] - X[groups==g].mean(axis=0) - X[years==t].mean(axis=0) + grand
 return out

results={}
for name,(filename,regressors,outcomes) in SPECS.items():
 with (ROOT/'data'/filename).open(encoding='utf-8') as f:rows=list(csv.DictReader(f))
 groups=np.array([x['ISO3'] for x in rows]);years=np.array([int(x['Year']) for x in rows]);
 if name=='ai':
  for r in rows:
   r['ln1p_AI_Investment']=math.log1p(float(r['AI_Investment']))
   r['ln1p_AI_Patents']=math.log1p(float(r['AI_Patents']))
  regressors=['ln1p_AI_Investment','ln1p_AI_Patents','GDP_Growth']
 else:
  for r in rows:r['ln_Productivity']=math.log(float(r['Productivity']))
  outcomes=['Growth','ln_Productivity']
 X=np.array([[float(r[k]) for k in regressors] for r in rows])
 WX=two_way_demean(X,groups,years)
 d={
  'type':'Exploratory (Python). Not official Stata IPS, Hansen or Arellano-Bond diagnostics.',
  'regressors':regressors,'pooled_VIF':vif(X,regressors),'two_way_within_VIF':vif(WX,regressors),
  'correlation_matrix':np.round(np.corrcoef(X.T),4).tolist(),
  'country_level_ADF_lag1':{}
 }
 for variable in outcomes+regressors:
  series=defaultdict(list)
  for r in sorted(rows,key=lambda v:(v['ISO3'],int(v['Year']))):
   series[r['ISO3']].append(float(r[variable]))
  probs=[];skipped=[]
  for g,values in series.items():
   try:
    p=float(adfuller(np.array(values),maxlag=1,regression='c',autolag=None)[1]);
    if math.isfinite(p):probs.append(p)
    else:skipped.append(g)
   except (ValueError,np.linalg.LinAlgError,ZeroDivisionError):skipped.append(g)
  d['country_level_ADF_lag1'][variable]={
   'n_tested':len(probs),'n_skipped':len(skipped),
   'fraction_p_lt_0_05':round(sum(p<0.05 for p in probs)/len(probs),4) if probs else None,
   'median_individual_p':round(float(np.median(probs)),4) if probs else None,
   'warning':'Country ADF tests are NOT an IPS estimate. Do not pool individual p values as if independent across countries.'
  }
 if name=='ai':
  c=defaultdict(dict)
  for r in rows:c[r['ISO3']][int(r['Year'])]=float(r['AI_Patents'])
  comparisons=[(g,v[2024]/v[2023]) for g,v in c.items() if 2023 in v and 2024 in v and v[2023]>0]
  d['patent_2024_to_2023_ratios']={'median':round(float(np.median([v for _,v in comparisons])),4),'fell':sum(v<1 for _,v in comparisons),'n':len(comparisons),'caution':'2024 patent application counts may be affected by reporting lag; verify source coverage and vintage.'}
 results[name]=d
with OUT.open('w',encoding='utf-8') as f:json.dump(results,f,ensure_ascii=False,indent=2)
print('PRE-ESTIMATION EXPLORATORY ANALYSIS ONLY')
for k,d in results.items():
 print(k, 'pooled VIF',d['pooled_VIF'],'within VIF',d['two_way_within_VIF'])
 print(k, 'country ADF fractions', {v:x['fraction_p_lt_0_05'] for v,x in d['country_level_ADF_lag1'].items()})
 if k=='ai':print(k,'2024 patent ratios',d['patent_2024_to_2023_ratios'])
print('RESULT_FILE',OUT)
