"""Offline integrity checks. Run from project root with Python >=3.9."""
from pathlib import Path
from collections import Counter
import csv, math
BASE=Path(__file__).resolve().parents[1] / 'data'
SPECS={
 'digital_panel.csv':(47,range(2005,2023),['Country','ISO3','Year','Growth','Productivity','Internet','Broadband','ICT_Exports','Unemployment','Inflation','RnD']),
 'ai_panel.csv':(30,range(2016,2025),['ISO3','Year','AI_Investment','AI_Patents','HighTech_Exports','GDP_Growth','Unemployment']),
}

def test_file(name, spec):
 n,cyrs,expected=spec
 with (BASE/name).open(encoding='utf-8-sig',newline='') as f:
  reader=csv.DictReader(f)
  assert reader.fieldnames==expected,(name,reader.fieldnames)
  rows=list(reader)
 assert len(rows)==n*len(cyrs),(name,len(rows))
 uniq={(r['ISO3'],int(r['Year'])) for r in rows}
 assert len(uniq)==len(rows),f'duplicate ISO3-year: {name}'
 counts=Counter(r['ISO3'] for r in rows)
 assert len(counts)==n and all(v==len(cyrs) for v in counts.values()),name
 assert {int(r['Year']) for r in rows}==set(cyrs),name
 assert 'IRN' not in counts,name
 for r in rows:
  assert all(str(v).strip() for v in r.values()),('blank',name,r)
  for k in expected:
   if k not in ('Country','ISO3'):
    v=float(r[k]);assert math.isfinite(v),(name,k,v)
  if name=='digital_panel.csv':
   assert float(r['Productivity'])>0
  else:
   assert float(r['AI_Investment'])>=0 and float(r['AI_Patents'])>=0
   assert float(r['HighTech_Exports'])>0
 return f'PASS {name}: {len(rows)} rows, {len(counts)} panels × {len(cyrs)} years'

if __name__=='__main__':
 for a,b in SPECS.items(): print(test_file(a,b))
