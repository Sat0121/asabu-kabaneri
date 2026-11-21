#!/usr/bin/env python3
"""麻生ハッピー カバネリ海門決戦 狙い台スコアラー v3
入力: 蓄積データ(1行1日「YYYY-MM-DD: 台=差枚/G ...」) または CSV(date,unit,games,diff)
  回転数が10000G以上の日は「データなし」として扱う(slot-eyeの回転数は加算バグの疑い)。差枚は全日使う。
  最新日から途切れずに続く区間だけを使う(9/24〜10/19のような空白をまたがない)。
使い方:
  python3 picker.py kabaneri_history.txt              # 1〜3台狙い向け(v3)
  python3 picker.py kabaneri_history.txt --wide       # 5台以上を押さえる場合(v4)
  python3 picker.py kabaneri_history.txt --backtest   # 区間ごとのウォークフォワード検証
"""
import csv, math, argparse, statistics as st
from collections import defaultdict
from datetime import date

GCAP = 10000
BASE = 101.6
_ = None
T = {
 "連続差枚マイナス": [101.5,101.6,101.9,102.9,100.7,_,_,_,_],
 "連続差枚プラス":   [101.9,101.4,102.0,99.4,101.7,_,_,_,_],
 "差枚ワースト1":   [99.2,100.6,100.2,101.9,102.1,102.6,99.9,101.6,101.2],
 "差枚ワースト2":   [101.4,100.5,102.2,102.4,102.9,100.5,104.0,101.4,102.8],
 "回転数ワースト1": [105.3,102.4,102.8,101.7,104.2,103.9,106.2,106.9,103.2],
 "回転数ワースト2": [101.0,100.4,104.1,103.8,103.3,105.5,105.1,103.9,106.4],
 "差枚ベスト1":     [100.8,102.5,101.3,100.3,99.9,99.9,100.1,101.5,99.1],
 "差枚ベスト2":     [103.0,100.6,101.1,101.2,100.9,100.8,102.0,100.2,101.1],
 "回転数ベスト1":   [104.0,100.7,99.1,98.2,99.1,98.6,98.5,101.0,98.1],
 "回転数ベスト2":   [99.0,100.4,100.5,100.3,99.1,100.7,99.4,99.6,99.4],
 "差枚-10000〜-5001":[99.1,100.7,101.0,102.3,102.0,102.3,102.1,101.4,101.7],
 "差枚-5000〜-2001": [101.1,101.6,102.0,101.8,101.4,_,_,_,_],
 "差枚-2000〜-1001": [102.0,102.2,_,_,_,_,_,_,_],
 "差枚-1000〜-1":    [102.1,_,_,_,_,_,_,_,_],
 "差枚0〜1000":      [101.7,_,_,_,_,_,_,_,_],
 "差枚1001〜2000":   [102.6,102.3,_,_,_,_,_,_,_],
 "差枚2001〜5000":   [101.2,101.6,101.8,101.6,101.9,_,_,_,_],
 "差枚5001〜10000":  [99.9,100.3,100.2,100.9,100.2,101.0,100.7,101.7,101.3],
 "差枚10001以上":    [102.9,102.3,102.3,101.3,101.6,101.1,100.6,100.6,100.4],
}
SINGLE = {
 "差枚2000以上の隣(番号小)":101.5, "差枚2000以上の隣(番号大)":102.0,
 "差枚5000以上の隣(番号小)":100.1, "差枚5000以上の隣(番号大)":102.4,
 "差枚ベスト1の隣(番号小)":101.6, "差枚ベスト1の隣(番号大)":99.3,
 "差枚ベスト2の隣(番号小)":102.7, "差枚ベスト2の隣(番号大)":101.1,
 "高稼働マイナス(7000G以上)":101.3, "高稼働マイナス(5000G以上)":101.4,
 "高稼働プラス(7000G以上)":101.2, "高稼働プラス(5000G以上)":101.4,
}
TAIL = {"1":100.1,"2":100.8,"3":100.7,"5":100.4,"6":100.1,"7":100.4,"8":100.6,"0":99.9}
BANDS = [(-10000,-5001,"差枚-10000〜-5001"),(-5000,-2001,"差枚-5000〜-2001"),(-2000,-1001,"差枚-2000〜-1001"),
 (-1000,-1,"差枚-1000〜-1"),(0,1000,"差枚0〜1000"),(1001,2000,"差枚1001〜2000"),(2001,5000,"差枚2001〜5000"),
 (5001,10000,"差枚5001〜10000"),(10001,10**9,"差枚10001以上")]
FAMS = ("連続差枚マイナス","連続差枚プラス","差枚ワースト","回転数ワースト","差枚ベスト","回転数ベスト","隣","高稼働","末尾")
num = lambda u: int("".join(c for c in u if c.isdigit()) or 0)
# 実際の島図(HAPPY麻生 島図・スマスロ③通路): 2列が通路をはさんで向かい合う。各列はカウンター側から順に並ぶ
COLUMNS = ["781 782 783 785 786 787 788 800 801 802 803 805 806 807 808 810 811 812 813 815".split(),
           "780 778 777 776 775 773 772 771 770 768 767 766 765 763 762 761 760 758 757 756".split()]
def neighbors(u):
    """同じ列で物理的に隣り合う台 (番号小側, 番号大側)"""
    for col in COLUMNS:
        if u in col:
            i = col.index(u); adj = [col[j] for j in (i-1, i+1) if 0 <= j < len(col)]
            return [a for a in adj if num(a) < num(u)], [a for a in adj if num(a) > num(u)]
    return [], []

def load(path):
    data = defaultdict(dict)
    txt = open(path, encoding="utf-8-sig").read()
    if not txt.startswith("date"):  # 圧縮形式: 「YYYY-MM-DD: 台=差枚/G 台=差枚/G ...」
        txt = "date,unit,games,diff\n" + "\n".join(f"{l.split(':')[0]},{c.split('=')[0]},{c.split('/')[1]},{c.split('=')[1].split('/')[0]}"
               for l in txt.splitlines() if ":" in l for c in l.split(":",1)[1].split())
    for r in csv.DictReader(txt.splitlines()):
        g = int(float(r["games"] or 0))
        data[date.fromisoformat(r["date"].strip())][r["unit"].strip()] = dict(g=g if g < GCAP else None, diff=int(float(r["diff"])))
    return data

def table_score(data, hist):
    """90日表の条件に当てはめた期待機械割(%) と 根拠"""
    units = sorted({u for d in hist for u in data[d]}, key=num)
    hits = defaultdict(list)
    def add(u, n, r):
        if r is not None: hits[u].append((n, r))
    for n in range(1, min(9, len(hist)) + 1):
        win = hist[:n]
        for key, label in (("diff","差枚"), ("g","回転数")):
            tot = {}
            for u in units:
                v = [data[d][u][key] for d in win if u in data[d]]
                if len(v) == n and None not in v: tot[u] = sum(v)
            if len(tot) < 10: continue  # 欠損で比較台が少ない窓は捨てる
            for u, v in tot.items():
                rl = sum(x < v for x in tot.values()) + 1; rh = sum(x > v for x in tot.values()) + 1
                if rl <= 2: add(u, f"{label}ワースト{rl}(過去{n}日)", T[f"{label}ワースト{rl}"][n-1])
                if rh <= 2: add(u, f"{label}ベスト{rh}(過去{n}日)", T[f"{label}ベスト{rh}"][n-1])
        for u in units:
            v = [data[d][u]["diff"] for d in win if u in data[d]]
            if len(v) == n:
                for lo, hi, nm in BANDS:
                    if lo <= sum(v) <= hi: add(u, f"{nm}(過去{n}日)", T[nm][n-1])
    for u in units:
        for sign, nm in ((-1,"連続差枚マイナス"), (1,"連続差枚プラス")):
            L = 0
            for d in hist:
                if u in data[d] and data[d][u]["diff"] * sign > 0: L += 1
                else: break
            if 1 <= L <= 9: add(u, f"{nm}{L}日", T[nm][L-1])
    y = data[hist[0]]; order = sorted(y, key=num); ranked = sorted(y, key=lambda u: -y[u]["diff"])
    def neigh(src, tag):
        lo, hi = neighbors(src)
        for v in lo:   # 良挙動台の番号小側の隣
            if v in y: add(v, tag+"の隣(番号小)", SINGLE[tag+"の隣(番号小)"])
        for v in hi:   # 良挙動台の番号大側の隣
            if v in y: add(v, tag+"の隣(番号大)", SINGLE[tag+"の隣(番号大)"])
    for u in order:
        if y[u]["diff"] >= 5000: neigh(u, "差枚5000以上")
        elif y[u]["diff"] >= 2000: neigh(u, "差枚2000以上")
        g = y[u]["g"]
        if g is not None and g >= 5000:
            side = "マイナス" if y[u]["diff"] < 0 else "プラス"
            add(u, f"高稼働{side}({7000 if g>=7000 else 5000}G以上)", SINGLE[f"高稼働{side}({7000 if g>=7000 else 5000}G以上)"])
    for k, src in enumerate(ranked[:2]): neigh(src, f"差枚ベスト{k+1}")
    for u in units: add(u, f"末尾{str(num(u))[-1]}", TAIL.get(str(num(u))[-1]))
    score, why = {}, {}
    for u in units:
        fam = defaultdict(list)
        for n_, r in hits[u]:
            f = next((k for k in FAMS if k in n_ and not (k=="差枚ベスト" and "隣" in n_)), "差枚レンジ")
            fam[f].append(r - BASE)
        lifts = [sum(v)/len(v) for v in fam.values()]
        pos = sorted([l for l in lifts if l > 0], reverse=True); neg = sorted(l for l in lifts if l < 0)
        score[u] = BASE + sum(l*.5**i for i,l in enumerate(pos)) + sum(l*.5**i for i,l in enumerate(neg))
        why[u] = sorted(hits[u], key=lambda x: -abs(x[1]-BASE))[:3]
    return score, why

def own_feats(data, hist):
    """自前データ由来: 直近7日の平均回転数(1万G以上除外)、台の通算クセ(日平均との差枚差の平均)"""
    units = sorted(data[hist[0]], key=num)
    dm = {d: st.mean(v["diff"] for v in data[d].values()) for d in hist}
    gmed = st.median([v["g"] for d in hist[:7] for v in data[d].values() if v["g"] is not None] or [5000])
    g7, kuse = {}, {}
    for u in units:
        gs = [data[d][u]["g"] for d in hist[:7] if u in data[d] and data[d][u]["g"] is not None]
        g7[u] = st.mean(gs) if gs else gmed
        rel = [data[d][u]["diff"] - dm[d] for d in hist if u in data[d]]
        kuse[u] = st.mean(rel) if rel else 0
    return g7, kuse

def pct(dct, reverse=False):
    xs = list(dct.values()); n = len(xs)
    r = {u: (sum(v < x for v in xs) + .5*sum(v == x for v in xs))/n - .5 for u, x in dct.items()}
    return {u: -v for u, v in r.items()} if reverse else r

def streaks(data, hist, u):
    m = p_ = 0
    for d in hist:
        if u in data[d] and data[d][u]["diff"] < 0: m += 1
        else: break
    for d in hist:
        if u in data[d] and data[d][u]["diff"] > 0: p_ += 1
        else: break
    return m, p_

def hybrid(data, hist, wide=False):
    ts, why = table_score(data, hist); g7, kuse = own_feats(data, hist)
    a, b = pct(ts), pct(g7, reverse=True)
    if not wide:   # v3: 表 + 直近7日の低稼働(等重み)。上位1〜3台が最も強い
        sc = {u: a[u] + b.get(u,0) for u in a}
    else:          # v4: 表 + 0.5×低稼働 + 0.5×連続マイナス − 0.5×連続プラス。上位5〜10台が強い
        st_ = {u: streaks(data, hist, u) for u in a}
        m, pl = pct({u: v[0] for u, v in st_.items()}), pct({u: v[1] for u, v in st_.items()})
        sc = {u: a[u] + .5*b.get(u,0) + .5*m[u] - .5*pl[u] for u in a}
    return sc, ts, g7, kuse, why

def contiguous(days_sorted):
    """最新日から空白(2日以上の欠け)なく続く区間"""
    out = [days_sorted[-1]]
    for d in reversed(days_sorted[:-1]):
        if (out[-1] - d).days > 2: break
        out.append(d)
    return out  # 新しい順

def spearman(a, b):
    def rk(x):
        return [sum(v < xi for v in x) + .5*(sum(v == xi for v in x)-1) for xi in x]
    ra, rb = rk(a), rk(b); ma, mb = st.mean(ra), st.mean(rb)
    den = math.sqrt(sum((x-ma)**2 for x in ra) * sum((y-mb)**2 for y in rb))
    return sum((x-ma)*(y-mb) for x, y in zip(ra, rb))/den if den else 0

def segments(days):
    segs, cur = [], [days[0]]
    for d in days[1:]:
        if (d - cur[-1]).days > 2: segs.append(cur); cur = [d]
        else: cur.append(d)
    return segs + [cur]

def backtest(data, wide=False, start=9):
    se = lambda x: st.stdev(x)/math.sqrt(len(x)) if len(x) > 1 else float("nan")
    for seg in segments(sorted(data)):
        if len(seg) <= start + 1: continue
        tops = {1: [], 3: [], 5: []}; rho = []
        for i in range(start, len(seg)):
            t = seg[i]; sc = hybrid(data, seg[:i][::-1], wide)[0]
            us = [u for u in sc if u in data[t]]; avg = st.mean(data[t][u]["diff"] for u in us)
            o = sorted(us, key=lambda u: -sc[u])
            rho.append(spearman([sc[u] for u in us], [data[t][u]["diff"] for u in us]))
            for k in tops: tops[k].append(st.mean(data[t][u]["diff"] for u in o[:k]) - avg)
        print(f"検証 {seg[start]}〜{seg[-1]} ({len(rho)}日)  順位相関 {st.mean(rho):+.3f}")
        for k, v in tops.items():
            print(f"  上位{k}台: その日の平均比 {st.mean(v):+.0f}枚/台 (±{se(v):.0f})")

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("csv")
    ap.add_argument("--backtest", action="store_true"); ap.add_argument("--wide", action="store_true")
    a = ap.parse_args(); data = load(a.csv)
    if a.backtest: return backtest(data, a.wide)
    days = contiguous(sorted(data))
    sc, ts, g7, kuse, why = hybrid(data, days, a.wide)
    rows = sorted(sc, key=lambda u: -sc[u])
    print(f"# 前日={days[0]} の翌日向け (使用{len(days)}日)")
    print("| 順位 | 台 | 総合 | 表の期待割 | 7日平均G | 連続(−/+) | 表の主な根拠 |\n|---|---|---|---|---|---|---|")
    for i, u in enumerate(rows, 1):
        w = " / ".join(f"{n} {r:.1f}" for n, r in why[u]) or "-"
        m, pl = streaks(data, days, u)
        print(f"| {i} | {u} | {sc[u]:+.2f} | {ts[u]:.1f}% | {g7[u]:.0f} | {m}/{pl} | {w} |")

if __name__ == "__main__":
    main()
