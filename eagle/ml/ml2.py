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
import ml; ml.X=X
pr=lambda s: s.rank(pct=True)
def R(f): return rule(lambda d: f(d)+1e-6*np.arange(len(d)))
evaluate('table',R(lambda d:d.tab_r.fillna(.5)))
evaluate('nb+bw',R(lambda d:d.nb_best1+(1-d.b1_r.fillna(.5))))
evaluate('tab+nb',R(lambda d:d.tab_r.fillna(.5)+0.5*d.nb_best1))
evaluate('tab+bw',R(lambda d:d.tab_r.fillna(.5)+(1-d.b1_r.fillna(.5))))
evaluate('tab+nb+bw',R(lambda d:d.tab_r.fillna(.5)+0.5*d.nb_best1+0.5*(1-d.b1_r.fillna(.5))))
FE2=FE+['tab','tab_r']; ml.FE=FE2
evaluate('GBM+tab',gbm({}))
ml.FE=FE
def ens(mode,df,m=None):
    g=gbm({}); r=ridge([c for c in FE if c.endswith('_r')]+['sm','sp','nb_best1','tm'])
    if mode=='fit': return (g('fit',df),r('fit',df))
    a=pd.Series(g('pred',df,m[0]),index=df.index).rank(pct=True); b=pd.Series(r('pred',df,m[1]),index=df.index).rank(pct=True)
    return a+b+df.tab_r.fillna(.5)+0.5*df.nb_best1
evaluate('ENS',ens)
def ens2(mode,df,m=None):
    g=gbm({})
    if mode=='fit': return g('fit',df)
    a=pd.Series(g('pred',df,m),index=df.index).rank(pct=True)
    return a+df.tab_r.fillna(.5)+0.5*df.nb_best1+0.5*(1-df.b1_r.fillna(.5))
evaluate('ENS2',ens2)
