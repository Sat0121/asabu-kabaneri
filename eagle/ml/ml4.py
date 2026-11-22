exec(open('ml3.py').read().split("print('--- ルール型")[0])
NEW=['dmax3','dmax5','dmax7','n1500_3','n1500_5','n1500_7','gm3','gm5','gm7','gm5_r','hol','we']
def ens(fe, extra):
    def f(mode,df,m=None):
        ml.FE=fe; g=gbm({})
        if mode=='fit': return g('fit',df)
        return pd.Series(g('pred',df,m),index=df.index).rank(pct=True)+base(df)+extra(df)
    return f
evaluate('E+1500+低G',ens(FE,lambda d:.5*d.n15+.5*low(d)))
evaluate('E+1500+低G+祝',ens(FE,lambda d:.5*d.n15+(.5+.5*d.hol)*low(d)))
evaluate('E+1500',ens(FE,lambda d:.5*d.n15))
evaluate('R 1500+低G+祝',R(lambda d: base(d)+.5*d.n15+(.5+.5*d.hol)*low(d)))
evaluate('R 1.0x1500',R(lambda d: base(d)+1.0*d.n15))
