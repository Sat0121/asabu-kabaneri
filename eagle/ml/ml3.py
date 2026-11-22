import numpy as np, pandas as pd, holidays, warnings; warnings.filterwarnings('ignore')
import ml
from tabcalc import X as XT
E=pd.read_pickle('/tmp/X.pkl')[['date','machine','dmax3','dmax5','dmax7','n1500_3','n1500_5','n1500_7','gm3','gm5','gm7']]
X=XT.merge(E,on=['date','machine'],how='left')
jp=holidays.Japan(years=[2025,2026,2027])
X['hol']=X.date.map(lambda d: int(d in jp)); X['we']=(X.date.dt.dayofweek>=5).astype(int)
X['gm5_r']=X.groupby('date').gm5.rank(pct=True); X['n15']=(X.n1500_5>0).astype(float)
ml.X=X
from ml import evaluate, rule, gbm, FE
def R(f): return rule(lambda d: f(d)+1e-6*np.arange(len(d)))
base=lambda d: d.tab_r.fillna(.5)+.5*d.nb_best1+.5*(1-d.b1_r.fillna(.5))
low=lambda d: 1-d.gm5_r.fillna(.5)
print('--- ルール型(5台以上用の土台 = 表+隣+ボナ少)')
evaluate('base',R(base))
evaluate('user(1500-,低G+)',R(lambda d: base(d)-.5*d.n15+.5*low(d)))
evaluate('低G5のみ+',R(lambda d: base(d)+.5*low(d)))
evaluate('1500+',R(lambda d: base(d)+.5*d.n15))
evaluate('1500+ 低G+',R(lambda d: base(d)+.5*d.n15+.5*low(d)))
evaluate('祝日だけ低G',R(lambda d: base(d)+d.hol*1.0*low(d)))
evaluate('1500+ 祝低G',R(lambda d: base(d)+.5*d.n15+d.hol*low(d)))
print('--- 機械学習込み')
NEW=['dmax3','dmax5','dmax7','n1500_3','n1500_5','n1500_7','gm3','gm5','gm7','gm5_r','hol','we']
def ens(fe, extra):
    def f(mode,df,m=None):
        ml.FE=fe; g=gbm({})
        if mode=='fit': return g('fit',df)
        a=pd.Series(g('pred',df,m),index=df.index).rank(pct=True)
        return a+base(df)+extra(df)
    return f
evaluate('ENS2(現行)',ens(FE,lambda d:0))
evaluate('ENS2+新特徴',ens(FE+NEW,lambda d:0))
evaluate('ENS2+1500+祝低G',ens(FE,lambda d:.5*d.n15+d.hol*low(d)))
evaluate('ENS2新+1500+祝低G',ens(FE+NEW,lambda d:.5*d.n15+d.hol*low(d)))
