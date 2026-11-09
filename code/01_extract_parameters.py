#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STEP 01 - EXTRACT MODEL PARAMETERS FROM RAW SOURCE FILES (with provenance).
Reads the raw source files in data/ and derives every data-driven parameter used by
the model, printing exactly which file / sheet / column / formula produced each.
Outputs: extracted_parameters.csv        (parameter, value, unit, source_file, detail)
         derived/model_parameters.json   (machine-readable parameters loaded by the model)
Run (from the repository root):  python code/01_extract_parameters.py
"""
import pandas as pd, numpy as np, warnings; warnings.filterwarnings('ignore')
import os as _os
# Project root = the directory that holds code/, data/ and derived/ (override with PROJECT_ROOT).
BASE = _os.environ.get('PROJECT_ROOT', _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
U=BASE+'/data/'
GAL_TO_L=3.785411784                 # 1 US gallon -> litres
rec=[]  # provenance records
def log(param,val,unit,src,detail): rec.append(dict(parameter=param,value=val,unit=unit,source_file=src,detail=detail)); print(f'{param:34s}= {val:<10} {unit:8s} | {src} | {detail}')

print('='*100); print('A. THERMOELECTRIC WATER FACTORS  <-  Cooling_Boiler_Generator_Data_Detail_2024.xlsx (EIA-923 Sch.8D)'); print('='*100)
f='Cooling_Boiler_Generator_Data_Detail_2024.xlsx'
df=pd.read_excel(U+f,sheet_name='Detail',header=2,thousands=',')
df.columns=[str(c).replace(chr(10),' ').strip() for c in df.columns]
WC='Water Consumption Volume (Million Gallons)'; WW='Water Withdrawal Volume (Million Gallons)'
NGcols=['Net Generation from Steam Turbines (MWh)',
        'Net Generation Associated with Single Shaft Combined Cycle Units (MWh)',
        'Net Generation Associated with Combined Cycle Gas Turbines (MWh)']
TECH='Generator Primary Technology'
for c in [WC,WW]+NGcols: df[c]=pd.to_numeric(df[c],errors='coerce')
# dedup: water reported per cooling system; generation per generator (avoid double counting association rows)
w=df.drop_duplicates(['Plant Code','Cooling ID','Year','Month'])          # one row per cooling-system-month
g=df.drop_duplicates(['Plant Code','Generator ID','Year','Month']).copy() # one row per generator-month
g['netgen']=g[NGcols].sum(axis=1)
# per-technology factors (the file holds MONTHLY volumes in Mgal; the sum over 12 months is the annual volume)
wt=w.groupby(TECH).agg(cons=(WC,'sum'),wdr=(WW,'sum'))
gt=g.groupby(TECH)['netgen'].sum()
m=wt.join(gt.rename('gen_MWh'))
m['cons_LkWh']=m['cons']*1e6*GAL_TO_L/(m['gen_MWh']*1e3)   # Mgal->L ; MWh->kWh
m['wdr_LkWh'] =m['wdr'] *1e6*GAL_TO_L/(m['gen_MWh']*1e3)
techmap={'Natural Gas Fired Combined Cycle':'gas_cc','Natural Gas Steam Turbine':'gas_other',
         'Conventional Steam Coal':'coal','Nuclear':'nuclear','Wood/Wood Waste Biomass':'bio'}
for eia,key in techmap.items():
    if eia in m.index:
        log(f'WF[{key}] consumption', round(m.loc[eia,'cons_LkWh'],3),'L/kWh',f,
            f"col '{WC}' / col net-gen, grouped by '{TECH}'='{eia}', dedup cooling & generator")
        log(f'WF_WITH[{key}] withdrawal', round(m.loc[eia,'wdr_LkWh'],3),'L/kWh',f,f"col '{WW}' similarly")
# national thermal totals (dedup):  Mgal -> L (*1e6*GAL_TO_L) -> m3 (/1000) -> billion m3 (/1e9)
Ccons_Bm3=w[WC].sum()*1e6*GAL_TO_L/1000/1e9
Cwdr_Bm3 =w[WW].sum()*1e6*GAL_TO_L/1000/1e9
log('thermal_consumption_2024', round(Ccons_Bm3,2),'billion m3',f,f"sum(col '{WC}') dedup cooling; Mgal->m3")
log('thermal_withdrawal_2024',  round(Cwdr_Bm3,1),'billion m3',f,f"sum(col '{WW}') dedup cooling")

print('\n'+'='*100); print('B. HYDROPOWER WATER FACTOR  <-  es8b00139_si_002.xlsx  (Grubert & Sanders 2018, sheet "Hydropower")'); print('='*100)
f2='es8b00139_si_002.xlsx'
from openpyxl import load_workbook
# 'Total' row of sheet 'Hydropower' in the Supporting Information of Grubert & Sanders (2018),
# Environ. Sci. Technol. 52, 6695-6703, doi:10.1021/acs.est.8b00139.  The SI workbook is not
# redistributed with this repository; if it is placed in data/, the two values are read from it
# (and checked against these), otherwise these published values are used.
GS2018_TOTAL_M3  = 2346976960              # 'Total Water Consumed m^3'
GS2018_M3_PER_GJ = 2.6474617374230047      # 'Intensity, m^3/GJ delivered'
if _os.path.exists(U+f2):
    wb=load_workbook(U+f2,data_only=True); ws=wb['Hydropower']
    rows=list(ws.iter_rows(values_only=True))
    cons_col=del_col=None
    for r in rows:                               # locate the consumption-side header row
        if any(isinstance(c,str) and 'Total Water Consumed' in c for c in r):
            for j,c in enumerate(r):             # take LEFTMOST (consumption block) matches
                if isinstance(c,str) and 'Total Water Consumed' in c and cons_col is None: cons_col=j
                if isinstance(c,str) and 'delivered' in c and del_col is None: del_col=j
            break
    tot_m3=inten_m3GJ=None
    for r in rows:
        if len(r)>1 and r[1]=='Total' and isinstance(r[cons_col],(int,float)):
            tot_m3=r[cons_col]; inten_m3GJ=r[del_col]; break
    print(f'  read from {f2}; matches the published values: '
          f'{tot_m3==GS2018_TOTAL_M3 and inten_m3GJ==GS2018_M3_PER_GJ}')
else:
    tot_m3, inten_m3GJ = GS2018_TOTAL_M3, GS2018_M3_PER_GJ
    print(f'  {f2} not in data/ -> using the published values (see README, "Data not redistributed")')
hydro_LkWh=inten_m3GJ/277.778*1000   # 1 GJ = 277.778 kWh ; m3/GJ -> L/kWh
log('WF[hydro] consumption (central)', round(hydro_LkWh,2),'L/kWh',f2,
    f"sheet 'Hydropower' Intensity {inten_m3GJ:.3f} m3/GJ delivered; /277.778 kWh/GJ *1000 L/m3")
log('hydro_total_consumption_US', round(tot_m3/1e9,2),'billion m3',f2,"sheet 'Hydropower' Total Water Consumed m^3")

print('\n'+'='*100); print('C. 2050 GENERATION MIX  <-  Narrative_Figures.xlsx  (EIA AEO2026, sheet "9_ElecGenMix", 2050 cases)'); print('='*100)
f3='Narrative_Figures.xlsx'
wb3=load_workbook(U+f3,data_only=True); ws3=wb3['9_ElecGenMix']
hdr=[c.value for c in ws3[3]]; ci={h:i for i,h in enumerate(hdr) if h}
def case_shares(name):
    for row in ws3.iter_rows(min_row=4,max_row=14,values_only=True):
        if row[ci['Case']] and name in str(row[ci['Case']]):
            tot=row[ci['Total']]
            return {k:row[ci[k]]/tot for k in ['coal','other','nuclear','oil and gas','wind','solar']}
    return None
casemap={'ref':'Counterfactual Baseline','accel':'Low Oil and Gas Supply','slow':'High Oil and Gas Supply'}
for scn,cname in casemap.items():
    s=case_shares(cname)
    log(f'AEO2050 mix[{scn}] wind%', round(s['wind']*100,1),'%',f3,f"case '{cname}': wind/Total")
    log(f'AEO2050 mix[{scn}] solar%',round(s['solar']*100,1),'%',f3,f"case '{cname}': solar/Total")
    log(f'AEO2050 mix[{scn}] oil+gas%',round(s['oil and gas']*100,1),'%',f3,f"case '{cname}': (oil and gas)/Total")
    log(f'AEO2050 mix[{scn}] nuclear%',round(s['nuclear']*100,1),'%',f3,f"case '{cname}': nuclear/Total")
print("  NOTE: model MIX_2050 = these AEO2050 case shares mapped to model technologies; the national mix is")
print("        interpolated linearly from the 2024 actual mix to this 2050 endpoint.")
print("        'oil and gas' split into gas_cc/gas_steam by 2024 actual ratio; 'other' split into hydro/bio/geo by 2024 actual.")

print('\n'+'='*100); print('D. LITERATURE / REPORT PARAMETERS (from PDFs & agency reports - cited, not column-extracted)'); print('='*100)
log('WF[hydro] range','5.4-68','L/kWh','Macknick 2012 (PDF) Table 1','hydropower 1425-18000 gal/MWh (median 4491=17); *3.78541/1000')
log('WF[solar]',0.10,'L/kWh','Macknick 2012 Table 1','utility PV 26 gal/MWh')
log('COOL current_evap WUE/PUE','0.61/1.145','L/kWh,-','LBNL 2024 report Fig 4.5; LBNL 2025 Update',
    'WUE: AI-specialized aggregate (LBNL 2024); PUE: facilities serving AI equipment, 2024 (LBNL 2025 Update S.3.5)')
log('COOL hyperscale WUE/PUE','0.32/1.22','L/kWh,-','LBNL 2024 report Fig 4.5','hyperscale aggregate')
log('fleet WUE 2023->2028','0.36->0.45-0.48','L/kWh','LBNL 2024 report Fig 4.7',
    'US aggregate site WUE; the 2028 value assumes no advanced-cooling penetration (see Supplementary Note 4). LBNL 2025 Update reports no water figures.')
log('WUE AWS / Microsoft','0.15 / 0.27','L/kWh','Amazon 2024 / Microsoft FY24 ESG','company sustainability reports')
log('demand 2023 / 2024','168 / 192','TWh','LBNL 2025 Update (Smith et al. 2026)','national DC electricity; 2024 = 4.7% of US')
log('demand 2028 / 2030 range','464 / 521-843','TWh','LBNL 2025 Update','Reference Case 2028; 2030 Compounded Uncertainty low-Reference-high 521/649/843')
log('fab freshwater per wafer',6300,'L/wafer','TSMC 2024 report','101 Mm3 / 16M 12-inch wafers (incl 85.7% recycle)')
log('AI share of IT electricity 2024 / 2030', '0.38 / 0.75', 'fraction', 'LBNL 2025 Update Fig. 9; S.3.6',
    'AI-specialised servers ~50 TWh of ~132 TWh IT (2024); AI servers 55% of total DC energy at aggregate PUE 1.36 (2030); model 0.85 in 2050 (0.70-0.90)')
log('non-AI fleet WUE (derived)', 0.24, 'L/kWh', 'mass balance to LBNL 2024 report (2023 values)',
    'AI share 0.32 (Fig 5.1) and fleet WUE 0.36: 0.32*0.61+0.68x=0.36 -> x=0.24 (not assumed)')

pd.DataFrame(rec).to_csv(BASE+'/extracted_parameters.csv',index=False)
print('\n-> wrote extracted_parameters.csv ('+str(len(rec))+' parameters)')

# ---------- emit machine-readable parameters for the model to LOAD (closes the pipeline) ----------
import json
params_out={
 'WF_thermal_consumption':{techmap[e]:round(m.loc[e,'cons_LkWh'],4) for e in techmap if e in m.index},
 'WF_thermal_withdrawal':{techmap[e]:round(m.loc[e,'wdr_LkWh'],4) for e in techmap if e in m.index},
 'WF_hydro_consumption': round(hydro_LkWh,4),
 'thermal_consumption_2024_Bm3': round(Ccons_Bm3,3),
 'thermal_withdrawal_2024_Bm3': round(Cwdr_Bm3,3),
 'AEO2050_case_shares':{scn:case_shares(cn) for scn,cn in casemap.items()},
 '_note':'Generated by code/01_extract_parameters.py from the raw files in data/. Loaded by code/lifecycle_water_model.py.'
}

# ---------- map AEO2050 case shares to model buckets = native 2050 endpoint MIX_2050 (no interpolation) ----------
def _map_mix(scn):
    a=case_shares(casemap[scn])                                  # native AEO 2050 shares
    t=sum(a.values()); a={k:x/t for k,x in a.items()}
    gas=a['oil and gas']; oth=a['other']
    return {'gas_cc':round(0.81*gas,4),'gas_other':round(0.19*gas,4),'coal':round(a['coal'],4),
            'nuclear':round(a['nuclear'],4),'hydro':round(0.789*oth,4),'bio':round(0.155*oth,4),
            'geo':round(0.056*oth,4),'wind':round(a['wind'],4),'solar':round(a['solar'],4),'other':0.0}
MIX_2050_derived={scn:_map_mix(scn) for scn in casemap}
for scn in MIX_2050_derived:
    re=sum(MIX_2050_derived[scn][k] for k in ['wind','solar','hydro','bio','geo'])
    print(f'  MIX_2050[{scn}] (AEO2050 native): RE share {re*100:.0f}%  gas {(MIX_2050_derived[scn]["gas_cc"]+MIX_2050_derived[scn]["gas_other"])*100:.0f}%  coal {MIX_2050_derived[scn]["coal"]*100:.0f}%  nuclear {MIX_2050_derived[scn]["nuclear"]*100:.0f}%')
params_out['MIX_2050']=MIX_2050_derived

_os.makedirs(_os.path.join(BASE,'derived'),exist_ok=True)
with open(_os.path.join(BASE,'derived','model_parameters.json'),'w',encoding='utf-8') as fh: json.dump(params_out,fh,indent=2)
print('-> wrote derived/model_parameters.json (thermal factors, hydro factor, thermal totals, AEO2050 shares)')
