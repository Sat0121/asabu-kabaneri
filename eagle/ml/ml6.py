import numpy as np, pandas as pd, warnings; warnings.filterwarnings('ignore')
import ml
from tabcalc import X as XT
from feat import load, LAY
df=load(); parts=[]
for sub in (df[df.date<LAY],df[df.date>=LAY]):
    days=sorted(sub.date.unique())
    D=sub.pivot(index='date',columns='machine',values='diff').reindex(days)
    G=sub.pivot(index='date',columns='machine',values='games').reindex(days)
    F={'h15':((D>1500).astype(float).where(D.notna()).shift(1).rolling(5,min_periods=2).sum()>0).astype(float),
       'h10':((D>1000).astype(float).where(D.notna()).shift(1).rolling(5,min_periods=2).sum()>0).astype(float),
       'gm5':G.shift(1).rolling(5,min_periods=2).mean()}
    parts.append(pd.concat({k:v.stack() for k,v in F.items()},axis=1))
E=pd.concat(parts); E.index.names=['date','machine']
X=XT.merge(E.reset_index(),on=['date','machine'],how='left')
X['gm5_r']=X.groupby('date').gm5.rank(pct=True)
ml.X=X
from ml import gbm, FE
days=sorted(X.date.unique())
def segkey(t): return 'old' if t<LAY else ('cur1' if t<pd.Timestamp('2026-09-20') else 'cur2')
def evaluate(name, scorefn, exth=3000, mintrain=40):
    res={}; model=None; last=None
    for t in days:
        tr=X[X.date<t]
        if tr.date.nunique()<mintrain: continue
        te=X[X.date==t]
        if te.d1.isna().all(): continue
        te=te[~(te.prev>exth)]
        if len(te)<5: continue
        if model is None or (t-last).days>=14: model=scorefn('fit',tr); last=t
        o=te.assign(s=scorefn('pred',te,model)+1e-6*np.arange(len(te))).sort_values('s',ascending=False)
        avg=X[X.date==t].yrel.mean()  # =0 (全台平均比)
        r=res.setdefault(segkey(t),{1:[],3:[],5:[],'h':[]})
        for n in (1,3,5): r[n].append(o.yrel.iloc[:n].mean())
        r['h'].append((o.y.iloc[:5]>2000).mean())
    print(f'{name:22s}'+''.join(f' | {k} '+' '.join(f'{np.mean(v[n]):+5.0f}' for n in (1,3,5))+f' 打率{100*np.mean(v["h"]):4.1f}%' for k,v in res.items()))
base=lambda d: d.tab_r.fillna(.5)+.5*d.nb_best1+.5*(1-d.b1_r.fillna(.5))+.5*d.h15+.5*(1-d.gm5_r.fillna(.5))
def R(extra):
    return lambda mode,df,m=None: None if mode=='fit' else base(df)+extra(df)
def E_(extra):
    def f(mode,df,m=None):
        ml.FE=FE; g=gbm({})
        if mode=='fit': return g('fit',df)
        return pd.Series(g('pred',df,m),index=df.index).rank(pct=True)+base(df)+extra(df)
    return f
p1=lambda d:(d.prev>1000).astype(float)
print('== 5台以上用(ルール) 各期間: 上位1/3/5台の全台平均比 と 上位5台の+2000超率')
evaluate('現行(+3000除外)',R(lambda d:0))
evaluate('前日+1000超を除外',R(lambda d:0),exth=1000)
evaluate('前日+1000超を減点0.5',R(lambda d:-.5*p1(d)))
evaluate('前日+1000超を減点1.0',R(lambda d:-1.0*p1(d)))
evaluate('5日内+1000超を減点0.5',R(lambda d:-.5*d.h10))
print('== 1〜3台用(機械学習込み)')
evaluate('現行(+3000除外)',E_(lambda d:0))
evaluate('前日+1000超を除外',E_(lambda d:0),exth=1000)
evaluate('前日+1000超を減点0.5',E_(lambda d:-.5*p1(d)))
evaluate('5日内+1000超を減点0.5',E_(lambda d:-.5*d.h10))
cur=X[(X.date>=LAY)&X.d1.notna()]
print('== 前日差枚帯ごとの翌日(現配置)')
print(cur.groupby(pd.cut(cur.prev,[-1e9,-2000,0,1000,2000,3000,5000,1e9])).agg(yrel=('yrel','mean'),hit=('y',lambda s:(s>2000).mean()),n=('y','size')).round(3).to_string())
