"""二十四軒: ウォークフォワード比較(その日より前のデータだけで学習・順位付け、14日ごとに再学習)"""
import sys, numpy as np, pandas as pd, warnings; warnings.filterwarnings('ignore')
sys.path.insert(0,'/home/claude/asabu-kabaneri/tools')
import picker_n24 as p
from n24_feat import load, build
from sklearn.ensemble import HistGradientBoostingRegressor as HGR
CSV='/home/claude/asabu-kabaneri/n24/n24_kabaneri.csv'
df=load(CSV); X=build(df)
# 1年表スコア
data={}
for r in df.itertuples():
    data.setdefault(r.date.date(),{})[str(r.machine)]=dict(g=None if pd.isna(r.games) else int(r.games),diff=int(r.diff))
ds=sorted(data); ts={}
for i,t in enumerate(ds):
    if i<3: continue
    h=p.contiguous(ds[:i])
    if (t-h[0]).days>7 or len(h)<3: continue
    s,_=p.table_score(data,h)
    for u,v in s.items(): ts[(pd.Timestamp(t),int(u))]=v
X['tab']=[ts.get((d,m),np.nan) for d,m in zip(X.date,X.machine)]
for c in ['tab','gm5','mx5']: X[c+'_r']=X.groupby('date')[c].rank(pct=True)
X['h15']=(X.n1500_5.fillna(0)>0).astype(float)
X.to_pickle('/tmp/X24.pkl')
FE=[c for c in X.columns if c not in ('date','machine','y','yrel','layout','tab','tab_r','gm5_r','mx5_r','h15')]
days=sorted(X.date.unique())
def seg(t): return 'A 4/20-7/15' if t<pd.Timestamp('2026-07-16') else ('B 7/16-9/30' if t<pd.Timestamp('2026-10-01') else 'C 10/1-11/22')
def gbm(tr):
    d=tr.dropna(subset=['d1']); return HGR(max_iter=150,learning_rate=0.05,max_leaf_nodes=15,min_samples_leaf=40,l2_regularization=1.0,random_state=0).fit(d[FE],d.yrel.clip(-8000,12000))
def evaluate(name, score, ex=lambda d:d.prev>3000, use_gbm=False):
    res={}; m=None; last=None
    for t in days:
        tr=X[X.date<t]
        if tr.date.nunique()<40: continue
        te=X[X.date==t]
        if te.d1.isna().all(): continue
        te=te[~ex(te)]
        if len(te)<6: continue
        if use_gbm and (m is None or (t-last).days>=14): m=gbm(tr); last=t
        g=pd.Series(m.predict(te[FE]),index=te.index).rank(pct=True) if use_gbm else 0
        o=te.assign(s=score(te,g)+1e-6*np.arange(len(te))).sort_values('s',ascending=False)
        r=res.setdefault(seg(t),{1:[],3:[],5:[],'h':[]})
        for n in (1,3,5): r[n].append(o.yrel.iloc[:n].mean())
        r['h'].append((o.y.iloc[:5]>2000).mean())
    out=f'{name:26s}'+''.join(f' | {k[0]}({len(v[1])}) '+' '.join(f'{np.mean(v[n]):+5.0f}' for n in (1,3,5))+f' {100*np.mean(v["h"]):4.1f}%' for k,v in sorted(res.items()))
    allv=[x for v in res.values() for x in v[5]]; print(out+f' || 5台平均 {np.mean(allv):+.0f}', flush=True)
T=lambda d:d.tab_r.fillna(.5); NB=lambda d:d.nb_best1; BW=lambda d:1-d.b1_r.fillna(.5); LG=lambda d:1-d.gm5_r.fillna(.5)
H15=lambda d:d.h15; P1=lambda d:((d.prev>1000)&(d.prev<=5000)).astype(float); PN=lambda d:((d.prev<=-1000)&(d.prev>-3000)).astype(float)
M5=lambda d:(d.mx5>3000).astype(float); LG1=lambda d:(d.g1<=2000).astype(float)
if __name__=='__main__':
    rnd=lambda d,g: pd.Series(np.random.RandomState(int(d.date.iloc[0].value%1e6)).rand(len(d)),index=d.index)
    evaluate('ランダム',rnd)
    evaluate('表のみ',lambda d,g:T(d))
    evaluate('イーグル型(表+隣+ボナ少+1500+低G)',lambda d,g:T(d)+.5*NB(d)+.5*BW(d)+.5*H15(d)+.5*LG(d))
    evaluate('表+低G',lambda d,g:T(d)+LG(d))
    evaluate('表+低G-5日内3000',lambda d,g:T(d)+LG(d)-.5*M5(d))
    evaluate('表+低G-5日内3000(除外)',lambda d,g:T(d)+LG(d),ex=lambda d:d.mx5>3000)
    evaluate('表+低G+凹み-前日+1000',lambda d,g:T(d)+LG(d)+.5*PN(d)-.5*P1(d))
    evaluate('表+低G+凹み-前日+1000-M5',lambda d,g:T(d)+LG(d)+.5*PN(d)-.5*P1(d)-.5*M5(d))
    evaluate('GBMのみ',lambda d,g:g,use_gbm=True)
    evaluate('GBM+表',lambda d,g:g+T(d),use_gbm=True)
    evaluate('GBM+表+低G',lambda d,g:g+T(d)+LG(d),use_gbm=True)
    evaluate('GBM+表+低G+凹み-前日+1000-M5',lambda d,g:g+T(d)+LG(d)+.5*PN(d)-.5*P1(d)-.5*M5(d),use_gbm=True)
    evaluate('GBM+イーグル型',lambda d,g:g+T(d)+.5*NB(d)+.5*BW(d)+.5*H15(d)+.5*LG(d),use_gbm=True)
