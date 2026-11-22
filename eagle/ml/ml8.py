exec(open('ml6.py').read().split("p1=lambda")[0])
import pandas as pd
# 直近5日の最大差枚
df_=load(); parts=[]
for sub in (df_[df_.date<LAY],df_[df_.date>=LAY]):
    days_=sorted(sub.date.unique()); D=sub.pivot(index='date',columns='machine',values='diff').reindex(days_)
    parts.append(D.shift(1).rolling(5,min_periods=1).max().stack().rename('mx5'))
M=pd.concat(parts); M.index.names=['date','machine']
X2=X.merge(M.reset_index(),on=['date','machine'],how='left'); ml.X=X2
import ml6; 
def evaluate2(name, scorefn, ex):
    res={}; model=None; last=None
    for t in days:
        tr=X2[X2.date<t]
        if tr.date.nunique()<40: continue
        te=X2[X2.date==t]
        if te.d1.isna().all(): continue
        te=te[~ex(te)]
        if len(te)<5: continue
        if model is None or (t-last).days>=14: model=scorefn('fit',tr); last=t
        o=te.assign(s=scorefn('pred',te,model)+1e-6*np.arange(len(te))).sort_values('s',ascending=False)
        r=res.setdefault(segkey(t),{1:[],3:[],5:[],'h':[],'n':[]})
        for n in (1,3,5): r[n].append(o.yrel.iloc[:n].mean())
        r['h'].append((o.y.iloc[:5]>2000).mean()); r['n'].append(len(te))
    print(f'{name:24s}'+''.join(f' | {k} '+' '.join(f'{np.mean(v[n]):+5.0f}' for n in (1,3,5))+f' 打率{100*np.mean(v["h"]):4.1f}% 候補{np.mean(v["n"]):.0f}' for k,v in res.items()))
p1=lambda d:(d.prev>1000).astype(float)
ex_prev=lambda d:d.prev>3000; ex_5=lambda d:d.mx5>3000
evaluate2('5台用 前日+3000除外',R(lambda d:-.5*p1(d)),ex_prev)
evaluate2('5台用 5日内+3000除外',R(lambda d:-.5*p1(d)),ex_5)
evaluate2('1〜3台用 前日+3000除外',E_(lambda d:0),ex_prev)
evaluate2('1〜3台用 5日内+3000除外',E_(lambda d:0),ex_5)
cur=X2[(X2.date>=LAY)&X2.d1.notna()]
print(cur.groupby([cur.mx5>3000, cur.prev>3000]).agg(yrel=('yrel','mean'),hit=('y',lambda s:(s>2000).mean()),n=('y','size')).round(3))
