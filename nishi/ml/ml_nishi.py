"""西町: ウォークフォワード比較(その日より前のデータだけで学習・順位付け)。
データが2か月ほどしかないので、機械学習は二十四軒・イーグル麻生・西町をまとめて学習する(特徴量は店内の相対値・順位が中心)。"""
import sys, pathlib, numpy as np, pandas as pd, warnings; warnings.filterwarnings('ignore')
R=pathlib.Path(__file__).resolve().parents[2]; sys.path.insert(0,str(R/'tools'))
import picker_nishi as p, nishi_feat as nf, n24_feat as n24f, eagle_feat as ef
from sklearn.ensemble import HistGradientBoostingRegressor as HGR
df=nf.load(R/'nishi/nishi_kabaneri.csv'); X=nf.build(df)
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
for c in ['tab','gm5']: X[c+'_r']=X.groupby('date')[c].rank(pct=True)
FE=[c for c in X.columns if c not in ('date','machine','y','yrel','layout','tab','tab_r','gm5_r','tail','tm','dom')]
OX=pd.concat([n24f.build(n24f.load(R/'n24/n24_kabaneri.csv')), ef.build(ef.load(R/'eagle/eagle_kabaneri.csv'))],ignore_index=True)
def gbm(tr):
    d=tr.dropna(subset=['d1']); return HGR(max_iter=150,learning_rate=0.05,max_leaf_nodes=15,min_samples_leaf=40,l2_regularization=1.0,random_state=0).fit(d[FE],d.yrel.clip(-8000,12000))
days=sorted(X.date.unique())
def evaluate(name, score, use_gbm=False, pool=True):
    res={1:[],3:[],5:[],'h':[]}; m=None; last=None
    for t in days:
        if t<pd.Timestamp('2026-09-15'): continue
        te=X[(X.date==t)&X.y.notna()&X.games.notna() if 'games' in X else (X.date==t)]
        te=X[X.date==t]; te=te[~(te.prev>3000)]
        if te.d1.isna().all() or len(te)<6: continue
        if use_gbm and (m is None or (t-last).days>=14):
            tr=pd.concat([X[X.date<t]]+([OX[OX.date<t]] if pool else []),ignore_index=True); m=gbm(tr); last=t
        g=pd.Series(m.predict(te[FE]),index=te.index).rank(pct=True) if use_gbm else 0
        o=te.assign(s=score(te,g)+1e-6*np.arange(len(te))).sort_values('s',ascending=False)
        for n in (1,3,5): res[n].append(o.yrel.iloc[:n].mean())
        res['h'].append((o.y.iloc[:5]>2000).mean())
    print(f'{name:22s} ({len(res[1])}日) 上位1 {np.mean(res[1]):+5.0f}  上位3 {np.mean(res[3]):+5.0f}  上位5 {np.mean(res[5]):+5.0f}  5台+2000超 {100*np.mean(res["h"]):4.1f}%',flush=True)
T=lambda d:d.tab_r.fillna(.5); LG=lambda d:1-d.gm5_r.fillna(.5)
if __name__=='__main__':
    rnd=lambda d,g: pd.Series(np.random.RandomState(int(d.date.iloc[0].value%1e6)).rand(len(d)),index=d.index)
    evaluate('ランダム',rnd)
    evaluate('低Gのみ',lambda d,g:LG(d))
    evaluate('表(二十四軒)のみ',lambda d,g:T(d))
    evaluate('表+低G',lambda d,g:T(d)+LG(d))
    evaluate('GBM(3店)のみ',lambda d,g:g,use_gbm=True)
    evaluate('GBM(3店)+低G',lambda d,g:g+LG(d),use_gbm=True)
    evaluate('GBM(3店)+表+低G',lambda d,g:g+T(d)+LG(d),use_gbm=True)
    W=lambda d:1-d.d5.rank(pct=True).fillna(.5); SM=lambda d:d.sm.rank(pct=True)
    evaluate('5日差枚少(採用 1〜3台用)',lambda d,g:W(d))
    evaluate('5日差枚少+0.5連続マイナス(採用 5台以上用)',lambda d,g:W(d)+.5*SM(d))
