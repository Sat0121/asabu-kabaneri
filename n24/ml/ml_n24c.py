from ml_n24 import *
rnd=lambda d,g: pd.Series(np.random.RandomState(int(d.date.iloc[0].value%1e6)).rand(len(d)),index=d.index)
evaluate('ランダム',rnd)
evaluate('5台以上用 表+低G',lambda d,g:T(d)+LG(d))
evaluate('1〜3台用 GBM+表+低G',lambda d,g:g+T(d)+LG(d),use_gbm=True)
evaluate('参考 表を使わない 低G+凹み-前日+1000-M5',lambda d,g:LG(d)+.5*PN(d)-.5*P1(d)-.5*M5(d))
