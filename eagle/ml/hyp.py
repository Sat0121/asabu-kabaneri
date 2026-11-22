import numpy as np, pandas as pd, holidays, warnings; warnings.filterwarnings('ignore')
from feat import load, build, LAY
df=load(); X=build(df)
# 追加特徴: 直近5/7日の最大差枚・+1500超の有無・平均回転数
parts=[]
for lay,sub in ((0,df[df.date<LAY]),(1,df[df.date>=LAY])):
    days=sorted(sub.date.unique())
    D=sub.pivot(index='date',columns='machine',values='diff').reindex(days)
    G=sub.pivot(index='date',columns='machine',values='games').reindex(days)
    F={}
    for n in (3,5,7):
        F[f'dmax{n}']=D.shift(1).rolling(n,min_periods=2).max()
        F[f'n1500_{n}']=(D>1500).astype(float).where(D.notna()).shift(1).rolling(n,min_periods=2).sum()
        F[f'gm{n}']=G.shift(1).rolling(n,min_periods=2).mean()
    parts.append(pd.concat({k:v.stack() for k,v in F.items()},axis=1))
E=pd.concat(parts); E.index.names=['date','machine']
X=X.merge(E.reset_index(),on=['date','machine'],how='left')
X=X[X.d1.notna()&~(X.prev>3000)]
X['hit']=(X.y>2000).astype(int)
cur=X[X.date>=LAY]; old=X[X.date<LAY]
print('== 仮説1: 直近n日に+1500超あり → 翌日 (yrel平均, +2000超率)')
for n in (5,7):
    for nm,S in (('old',old),('cur',cur)):
        g=S.groupby(S[f'n1500_{n}']>0).agg(yrel=('yrel','mean'),hit=('hit','mean'),n=('y','size'))
        print(n,nm,g.round(3).to_dict('index'))
print('== 仮説2: 直近n日の平均回転数 3分位(日内順位)')
for n in (5,7):
    for nm,S in (('old',old),('cur',cur)):
        q=S.groupby('date')[f'gm{n}'].rank(pct=True)
        g=S.groupby(pd.cut(q,[0,1/3,2/3,1],labels=['少','中','多'])).agg(yrel=('yrel','mean'),hit=('hit','mean'))
        print(n,nm,g.round(3).to_dict('index'))
print('== 仮説1×2 (cur, n=5): +1500なし & 回転少')
for nm,S in (('old',old),('cur',cur)):
    q=S.groupby('date').gm5.rank(pct=True)
    g=S.groupby([S.n1500_5>0,pd.cut(q,[0,.5,1],labels=['少','多'])]).agg(yrel=('yrel','mean'),hit=('hit','mean'),n=('y','size'))
    print(nm,g.round(3).to_string())
# 仮説3 祝日
jp=holidays.Japan(years=[2026])
d=df[df.date>=pd.Timestamp('2026-03-04')].groupby('date').agg(avg=('diff','mean'))
d['hol']=[x in jp for x in d.index]; d['dow']=d.index.dayofweek
d['kind']=np.where(d.hol,'祝日',np.where(d.dow>=5,'土日','平日'))
print('== 仮説3: 日の全台平均差枚'); print(d.groupby('kind').avg.agg(['mean','median','count']).round(0))
print(d[d.hol].round(0).assign(name=[jp.get(x) for x in d[d.hol].index]))
d['prehol']=[(x+pd.Timedelta(days=1)) in jp for x in d.index]
print('祝前日', d[d.prehol].avg.mean().round(0), d[d.prehol].shape[0])
X.to_pickle('/tmp/X.pkl')
