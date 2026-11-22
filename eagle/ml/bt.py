"""イーグル麻生: 表ベース(v3/v4)のウォークフォワード検証。配置ごと・空白ごとに区切る"""
import sys, statistics as st, math
sys.path.insert(0,'/home/claude/asabu-kabaneri/tools')
import picker_eagle as p
from datetime import date
data=p.load('/home/claude/eagle/eagle_history.txt')
LAY=date(2026,7,9)
def segs():
    out=[]
    for part in ([d for d in sorted(data) if d<LAY],[d for d in sorted(data) if d>=LAY]):
        out+=p.segments(part)
    return out
def run(scorer, start=9, label=''):
    res={'old':{1:[],3:[],5:[]},'cur1':{1:[],3:[],5:[]},'cur2':{1:[],3:[],5:[]}}
    for seg in segs():
        for i in range(start,len(seg)):
            t=seg[i]; hist=seg[:i][::-1]
            ok=scorer(hist)
            us=list(data[t]); avg=st.mean(data[t][u]['diff'] for u in us)
            o=[u for u in ok if u in data[t]]
            key='old' if t<LAY else ('cur1' if t<date(2026,9,20) else 'cur2')
            for k in (1,3,5): res[key][k].append(st.mean(data[t][u]['diff'] for u in o[:k])-avg)
    s=f'{label:10s}'
    for key,v in res.items():
        s+=f' | {key}({len(v[1])}d) '+' '.join(f'{st.mean(v[k]):+5.0f}' for k in (1,3,5))
    print(s); return res
if __name__=='__main__':
    run(lambda h: p.ranking(data,h,False)[0],label='v3')
    run(lambda h: p.ranking(data,h,True)[0],label='v4')
    import random
    def rnd(h):
        ok,ex,sc=p.ranking(data,h,False); r=ok[:]; random.Random(str(h[0])).shuffle(r); return r
    run(rnd,label='random')
    run(lambda h: sorted(p.ranking(data,h,False)[0], key=lambda u:-p.table_score(data,h)[0][u]),label='tableonly')
