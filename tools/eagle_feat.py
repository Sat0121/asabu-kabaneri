import numpy as np, pandas as pd
LAY=pd.Timestamp('2026-07-09')
def load(path):
    df=pd.read_csv(path,parse_dates=['date'])
    df.loc[(df.games>=10000)|(df.games<=0),'games']=np.nan
    df['bona']=df.bb.fillna(0)+df.rb.fillna(0)
    return df
def build(df, keep_next=False):
    parts=[]
    for lay,sub in ((0,df[df.date<LAY]),(1,df[df.date>=LAY])):
        days=sorted(sub.date.unique())
        D=sub.pivot(index='date',columns='machine',values='diff').reindex(days)
        G=sub.pivot(index='date',columns='machine',values='games').reindex(days)
        B=sub.pivot(index='date',columns='machine',values='bona').reindex(days)
        F={}
        roll=lambda X,n: X.shift(1).rolling(n,min_periods=n).sum()
        for n in (1,2,3,5,7,9):
            F[f'd{n}']=roll(D,n); F[f'b{n}']=roll(B,n)
            F[f'g{n}']=G.shift(1).rolling(n,min_periods=max(1,n//2)).mean()
        F['g7m']=G.shift(1).rolling(7,min_periods=2).mean()
        F['dm30']=D.shift(1).rolling(30,min_periods=5).mean()
        F['dmax30']=D.shift(1).rolling(30,min_periods=5).max()
        def streak(c):
            out=np.zeros(D.shape); cur=np.zeros(D.shape[1])
            for i in range(len(D)): out[i]=cur; cur=np.where(c[i],cur+1,0)
            return pd.DataFrame(out,index=D.index,columns=D.columns)
        F['sm']=streak((D<0).values); F['sp']=streak((D>0).values)
        P=D.shift(1); cols=sorted(D.columns)
        L=P[cols].shift(1,axis=1); R=P[cols].shift(-1,axis=1)
        # 番号の連続しない境界(134-143 / 162-173)では隣扱いしない
        for i,c in enumerate(cols):
            if i>0 and cols[i-1]!=c-1: L[c]=np.nan
            if i<len(cols)-1 and cols[i+1]!=c+1: R[c]=np.nan
        F['nbL']=L; F['nbR']=R; F['nbmax']=np.fmax(L,R)
        rk=P.rank(axis=1,ascending=False)
        F['nb_best1']=((rk.shift(1,axis=1)==1)|(rk.shift(-1,axis=1)==1)).astype(float)
        rel=D.sub(D.mean(axis=1),axis=0)
        F['kuse']=rel.shift(1).expanding(min_periods=10).mean()
        F['prevavg']=pd.DataFrame(np.repeat(D.mean(axis=1).shift(1).values[:,None],D.shape[1],1),index=D.index,columns=D.columns)
        X=pd.concat({k:v.stack(future_stack=True) for k,v in F.items()},axis=1)
        X.index.names=['date','machine']
        X=X.join(D.stack().rename('y')).reset_index()
        if not keep_next: X=X[X.y.notna()]
        X['yrel']=X.y-X.groupby('date').y.transform('mean')
        X['layout']=lay
        parts.append(X)
    X=pd.concat(parts,ignore_index=True)
    for c in ['d1','d2','d3','d5','d7','d9','b1','b3','b9','g1','g3','g7','dm30','kuse']:
        X[c+'_r']=X.groupby('date')[c].rank(pct=True)
    X['dom']=X.date.dt.day; X['tail']=X.machine%10; X['tm']=(X.tail==X.dom%10).astype(int)
    X['prev']=X.d1
    return X
