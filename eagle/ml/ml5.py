import numpy as np, pandas as pd, warnings; warnings.filterwarnings('ignore')
import ml
from tabcalc import X as XT
from feat import load, LAY
df=load(); parts=[]
for sub in (df[df.date<LAY],df[df.date>=LAY]):
    days=sorted(sub.date.unique())
    D=sub.pivot(index='date',columns='machine',values='diff').reindex(days)
    G=sub.pivot(index='date',columns='machine',values='games').reindex(days)
    F={}
    for n in range(5,10):
        F[f'h{n}']=((D>1500).astype(float).where(D.notna()).shift(1).rolling(n,min_periods=2).sum()>0).astype(float)
        F[f'gm{n}']=G.shift(1).rolling(n,min_periods=2).mean()
    parts.append(pd.concat({k:v.stack() for k,v in F.items()},axis=1))
E=pd.concat(parts); E.index.names=['date','machine']
X=XT.merge(E.reset_index(),on=['date','machine'],how='left')
for n in range(5,10): X[f'gm{n}_r']=X.groupby('date')[f'gm{n}'].rank(pct=True)
ml.X=X
from ml import evaluate, rule, gbm, FE
cur=X[(X.date>=LAY)&X.d1.notna()&~(X.prev>3000)]
print('「+1500超なし」の台の割合と翌日成績(現配置)')
for n in range(5,10):
    g=cur.groupby(f'h{n}').yrel.agg(['mean','size']); print(n,'日: なし',f"{g.loc[0,'mean']:+.0f}({g.loc[0,'size']})",' あり',f"{g.loc[1,'mean']:+.0f}({g.loc[1,'size']})")
base=lambda d: d.tab_r.fillna(.5)+.5*d.nb_best1+.5*(1-d.b1_r.fillna(.5))
def R(f): return rule(lambda d: f(d)+1e-6*np.arange(len(d)))
def ens(extra):
    def f(mode,df,m=None):
        ml.FE=FE; g=gbm({})
        if mode=='fit': return g('fit',df)
        return pd.Series(g('pred',df,m),index=df.index).rank(pct=True)+base(df)+extra(df)
    return f
for n in range(5,10):
  for gn in (5,n):
    if gn!=5 and gn==n and n==5: continue
    low=lambda d,gn=gn:1-d[f'gm{gn}_r'].fillna(.5)
    evaluate(f'R h{n} G{gn}',R(lambda d,n=n,low=low: base(d)+.5*d[f'h{n}']+.5*low(d)))
    evaluate(f'E h{n} G{gn}',ens(lambda d,n=n,low=low: .5*d[f'h{n}']+.5*low(d)))
