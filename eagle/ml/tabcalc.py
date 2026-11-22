import numpy as np, pandas as pd, sys, warnings; warnings.filterwarnings('ignore')
sys.path.insert(0,'/home/claude/asabu-kabaneri/tools'); import picker_eagle as p
from ml import X, evaluate, rule, gbm, ridge, FE
# 表スコア(1年表)を各日に付与
data=p.load('/home/claude/eagle/eagle_history.txt'); ds=sorted(data)
from datetime import date
LAY=date(2026,7,9)
ts={}
for i,t in enumerate(ds):
    part=[d for d in ds[:i] if (d>=LAY)==(t>=LAY)]
    if len(part)<3: continue
    hist=p.contiguous(part) if (t-part[-1]).days<=7 else []
    if len(hist)<3: continue
    s,_=p.table_score(data,hist)
    for u,v in s.items(): ts[(pd.Timestamp(t),int(u))]=v
X['tab']=[ts.get((d,m),np.nan) for d,m in zip(X.date,X.machine)]
X['tab_r']=X.groupby('date').tab.rank(pct=True)

