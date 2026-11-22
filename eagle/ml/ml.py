import numpy as np, pandas as pd, warnings; warnings.filterwarnings('ignore')
from sklearn.ensemble import HistGradientBoostingRegressor as HGR
from sklearn.linear_model import Ridge
from feat import load, build, LAY
X=build(load())
FE=[c for c in X.columns if c not in ('date','machine','y','yrel','layout')]
days=sorted(X.date.unique())
def segkey(t): return 'old' if t<LAY else ('cur1' if t<pd.Timestamp('2026-09-20') else 'cur2')
def evaluate(name, scorefn, mintrain=40):
    res={}
    model=None; last=None
    for i,t in enumerate(days):
        tr=X[X.date<t]
        if tr.date.nunique()<mintrain: continue
        te=X[(X.date==t)]
        te=te[~(te.prev>3000)]
        if len(te)<5 or te.d1.isna().all(): continue
        if model is None or (t-last).days>=14:
            model=scorefn('fit',tr); last=t
        s=scorefn('pred',te,model)
        o=te.assign(s=s).sort_values('s',ascending=False)
        k=segkey(t); r=res.setdefault(k,{1:[],3:[],5:[]})
        for n in (1,3,5): r[n].append(o.yrel.iloc[:n].mean())
    print(f'{name:12s}'+''.join(f' | {k}({len(v[1])}d) '+' '.join(f'{np.mean(v[n]):+5.0f}' for n in (1,3,5)) for k,v in res.items()))
def gbm(params):
    def f(mode,df,m=None):
        if mode=='fit':
            d=df.dropna(subset=['d1'])
            return HGR(max_iter=150,learning_rate=0.05,max_leaf_nodes=15,min_samples_leaf=40,l2_regularization=1.0,**params).fit(d[FE],d.yrel.clip(-8000,12000))
        return m.predict(df[FE])
    return f
def rule(expr):
    def f(mode,df,m=None):
        return None if mode=='fit' else expr(df)
    return f
def ridge(cols):
    def f(mode,df,m=None):
        if mode=='fit':
            d=df.dropna(subset=cols); mu=d[cols].mean(); sd=d[cols].std()+1e-9
            return (Ridge(10).fit((d[cols]-mu)/sd,d.yrel.clip(-8000,12000)),mu,sd)
        r,mu,sd=m; return r.predict(((df[cols]-mu)/sd).fillna(0))
    return f
evaluate('GBM',gbm({}))
evaluate('GBM_q80',gbm({'loss':'quantile','quantile':0.8}))
evaluate('ridge_r',ridge([c for c in FE if c.endswith('_r')]+['sm','sp','nb_best1','tm']))
evaluate('lowG7',rule(lambda d:-d.g7_r.fillna(.5)))
evaluate('nb_best1',rule(lambda d:d.nb_best1+0.01*np.random.RandomState(0).rand(len(d))))
evaluate('b1worst',rule(lambda d:-d.b1_r.fillna(.5)))
evaluate('d1low',rule(lambda d:-d.d1_r.fillna(.5)))
evaluate('kuse',rule(lambda d:d.kuse.fillna(0)))
evaluate('random',rule(lambda d:np.random.RandomState(int(d.date.iloc[0].value%1e6)).rand(len(d))))
