from ml_n24 import *
evaluate('低Gのみ',lambda d,g:LG(d))
evaluate('低G+凹み-前日+1000',lambda d,g:LG(d)+.5*PN(d)-.5*P1(d))
evaluate('低G+凹み-前日+1000-M5',lambda d,g:LG(d)+.5*PN(d)-.5*P1(d)-.5*M5(d))
evaluate('低G+ボナ少+凹み-前日+1000',lambda d,g:LG(d)+.5*BW(d)+.5*PN(d)-.5*P1(d))
W=lambda d:1-d.d5.rank(pct=True).fillna(.5)  # 直近5日の差枚ワースト寄り
evaluate('低G+5日差枚少',lambda d,g:LG(d)+W(d))
evaluate('低G+5日差枚少-前日+1000',lambda d,g:LG(d)+W(d)-.5*P1(d))
evaluate('GBM+低G',lambda d,g:g+LG(d),use_gbm=True)
evaluate('GBM+低G+5日差枚少',lambda d,g:g+LG(d)+W(d),use_gbm=True)
evaluate('GBM+低G+凹み-前日+1000',lambda d,g:g+LG(d)+.5*PN(d)-.5*P1(d),use_gbm=True)
