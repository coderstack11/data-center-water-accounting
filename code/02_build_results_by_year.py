#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
STEP 02 - COMPUTE FULL SCENARIO RESULTS and write ONE workbook with a sheet PER YEAR.
Axes: DC growth (slow/mid/fast) x RE growth (slow/mid/fast) x cooling deploy (slow/mid/fast)
      x dispatch (overall_average / green_priority / marginal_price) = 81 combos/year.
Each row also carries the hydropower sensitivity range (_lo excluded, central Grubert, _hi Macknick).
Depends on lifecycle_water_model.py (the computation engine).
Output: results_by_year_FINAL.xlsx (repository root)
Run (from the repository root):  python code/02_build_results_by_year.py
"""
import os as _os
# Project root = the directory that holds code/, data/ and derived/ (override with PROJECT_ROOT).
BASE = _os.environ.get('PROJECT_ROOT', _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import lifecycle_water_model as M, pandas as pd, numpy as np, warnings; warnings.filterwarnings('ignore')
Y=M.YEARS
DC={'slow':'low','mid':'mid','fast':'high'}; RE={'slow':'slow','mid':'ref','fast':'accel'}
COOL={'slow':'slow','mid':'base','fast':'fast'}; DISP={'overall_average':'average','green_priority':'market','marginal_price':'marginal_gas'}
HYD={'lo':0.0,'central':1.0,'hi':17.0/M.WF['hydro']}   # exact Macknick-17 over Grubert-9.5309

records=[]
for dcL,dcs in DC.items():
 for reL,res in RE.items():
  for coL,cos in COOL.items():
   for diL,dis in DISP.items():
     runs={h:M.run_case(dcs,'adaptive_warm',res,hydro_alloc=hv,dry_scn=cos,attribution=dis) for h,hv in HYD.items()}
     c=runs['central']
     for i,yr in enumerate(Y):
       records.append(dict(year=int(yr),dc_growth=dcL,re_growth=reL,cooling_deploy=coL,dispatch=diL,
         demand_TWh=round(M.demand_path(dcs)[i],1),WUE_fleet=round(c.WUE.iloc[i],3),PUE_fleet=round(c.PUE.iloc[i],3),
         I_grid=round(c.I_grid_LkWh.iloc[i],3),I_grid_hydroLo=round(runs['lo'].I_grid_LkWh.iloc[i],3),
         I_grid_hydroHi=round(runs['hi'].I_grid_LkWh.iloc[i],3),
         W_site_Bm3=round(c.W_site_ML.iloc[i]/1e6,4),W_fab_Bm3=round(c.W_fab_ML.iloc[i]/1e6,4),
         W_grid_Bm3=round(c.W_grid_ML.iloc[i]/1e6,4),
         W_total_Bm3=round(c.W_total_ML.iloc[i]/1e6,4),
         W_total_hydroLo=round(runs['lo'].W_total_ML.iloc[i]/1e6,4),
         W_total_hydroHi=round(runs['hi'].W_total_ML.iloc[i]/1e6,4),
         grid_pct=round(c.theta_grid.iloc[i]*100,2),site_pct=round(c.theta_site.iloc[i]*100,2),fab_pct=round(c.theta_fab.iloc[i]*100,3)))
df=pd.DataFrame(records)

legend=pd.DataFrame([
 ['SHEET NAMING','one worksheet per year 2023-2050 (year_2023 = pre-window context; reporting window 2027-2050); each has all 81 scenario combinations',''],
 ['dc_growth','data-center electricity demand pathway',
  'slow/mid/fast = LBNL 2025 Update 2030 anchors 521 / 649 / 843 TWh, extrapolated at 2.0 / 3.5 / 5.0 %/yr'],
 ['re_growth','renewable-energy growth (grid)','slow / mid=AEO2026 reference / fast=accelerated'],
 ['cooling_deploy','advanced-cooling deployment tier',
  'slow/mid/fast = 0.90 / 0.95 / 1.00 new-build adoption by 2030 with 6 / 5 / 4-yr replacement'],
 ['dispatch','electricity attribution','overall_average=location-based avg grid mix (PRIMARY); green_priority=100% renewable PPA (market-based); marginal_price=marginal unit (gas CC)'],
 ['I_grid / I_grid_hydroLo/Hi','grid water intensity central + hydro range','central=Grubert-Sanders 9.53 ; Lo=hydro excluded(0) ; Hi=Macknick 17'],
 ['W_*_Bm3','water in billion m^3 per year',''],
 ['W_total_hydroLo/Hi','total under hydro excluded / Macknick-17','sensitivity band; for green/marginal dispatch equals central (I_grid hydro-independent)'],
 ['pct columns','three-way share at central hydro',''],
], columns=['field','meaning','values'])

with pd.ExcelWriter(BASE+'/results_by_year_FINAL.xlsx',engine='openpyxl') as xw:
    legend.to_excel(xw,sheet_name='00_LEGEND',index=False)
    for yr in Y:
        df[df.year==yr].drop(columns='year').to_excel(xw,sheet_name=f'year_{int(yr)}',index=False)
# format headers
import openpyxl
from openpyxl.styles import Font,PatternFill
wb=openpyxl.load_workbook(BASE+'/results_by_year_FINAL.xlsx')
for ws in wb.worksheets:
    ws.freeze_panes='A2'
    for c in ws[1]: c.fill=PatternFill('solid',fgColor='1F3864'); c.font=Font(bold=True,color='FFFFFF',size=9)
    for col in ws.columns:
        wdt=max((len(str(c.value)) for c in col if c.value is not None),default=10)+1
        ws.column_dimensions[col[0].column_letter].width=min(max(wdt,9),40)
wb.save(BASE+'/results_by_year_FINAL.xlsx')
print('wrote results_by_year_FINAL.xlsx :',len(Y),'year sheets +legend ; rows/year =',len(df[df.year==Y[0]]))

# ---------- append REFERENCE sheets so every figure input lives in the xlsx ----------
import lifecycle_water_model as M2
Yr=M2.YEARS
# generation mix by year (for fig_genmix)
mixrows=[]
for scn in ['slow','ref','accel']:
    mx=M2.mix_path(scn)
    for i,yr in enumerate(Yr):
        d={'grid_scn':scn,'year':int(yr)}; d.update({k:round(mx[k][i],4) for k in mx}); mixrows.append(d)
# cooling adoption + fleet WUE/PUE by year (from the model's anchored AI-share path
# and stock-turnover adoption)
coolrows=[]
ai=M2.ai_share_path()
for i,yr in enumerate(Yr):
    row={'year':int(yr),'AI_share_of_IT':round(float(ai[i]),4)}
    for ds in ['slow','base','fast']:
        w,p=M2.cooling_series('adaptive_warm',ds); adv=M2.adv_share_path(ds)
        row[f'adv_share_within_AI_{ds}']=round(float(adv[i]),4)
        row[f'fleet_WUE_{ds}']=round(float(w[i]),4)
        row[f'fleet_PUE_{ds}']=round(float(p[i]),4)
    coolrows.append(row)
# per-state intensity + DC weight (for fig1 d/f)
strows=[{'state':s,'DC_weight':M2.DC_WEIGHTS[s],
         'I_consumption_LkWh':round(M2.state_intensity(s,1.0,'consumption'),3),
         'I_production_LkWh':round(M2.state_intensity(s,1.0,'production'),3),
         'I_factor_LkWh':round(M2.state_intensity(s,1.0,'factor'),3),
         'self_supply':round(M2.self_supply_fraction(s),3)} for s in M2.STATE_MIX]
# water factors (reference)
wfrows=[{'technology':k,'consumption_LkWh':M2.WF[k],'withdrawal_LkWh':M2.WF_WITH.get(k)} for k in M2.WF]
with pd.ExcelWriter(BASE+'/results_by_year_FINAL.xlsx',engine='openpyxl',mode='a',if_sheet_exists='replace') as xw:
    pd.DataFrame(mixrows).to_excel(xw,sheet_name='ref_generation_mix',index=False)
    pd.DataFrame(coolrows).to_excel(xw,sheet_name='ref_cooling_adoption',index=False)
    pd.DataFrame(strows).to_excel(xw,sheet_name='ref_state_intensity',index=False)
    pd.DataFrame(wfrows).to_excel(xw,sheet_name='ref_water_factors',index=False)
print('appended reference sheets: ref_generation_mix, ref_cooling_adoption, ref_state_intensity, ref_water_factors')
