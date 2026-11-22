import numpy as np, pandas as pd, holidays, warnings, sys; warnings.filterwarnings('ignore')
X=pd.read_pickle('/tmp/X.pkl'); LAY=pd.Timestamp('2026-07-09')
X['big']=(X.y>5000).astype(int)
for nm,S in (('old',X[X.date<LAY]),('cur',X[X.date>=LAY])):
    q=S.groupby('date').gm5.rank(pct=True)
    print(nm, S.groupby([S.n1500_5>0, pd.cut(q,[0,.5,1],labels=['少','多'])]).agg(big=('big','mean'),hit=('hit','mean'),n=('y','size')).round(3).to_string())
# 祝日の日: どんな台が出たか
jp=holidays.Japan(years=[2026]); H=X[X.date.isin([d for d in X.date.unique() if d in jp])]
print('祝日 n=',H.date.nunique()); q=H.groupby('date').gm5.rank(pct=True)
print(H.groupby([H.n1500_5>0,pd.cut(q,[0,.5,1],labels=['少','多'])]).agg(yrel=('yrel','mean'),big=('big','mean'),n=('y','size')).round(2).to_string())
