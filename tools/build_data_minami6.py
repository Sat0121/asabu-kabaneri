#!/usr/bin/env python3
"""プレイランドハッピー南6条 カバネリ海門決戦: minami6/minami6_kabaneri.csv から minami6.json(サイト用)を作る。
使い方: python3 tools/build_data_minami6.py   (リポジトリのルートで実行。pandas・holidays が必要)

データはみんレポ(min-repo.com)から 2026-11-14 以降。
データが2週間しかないので、機械学習・表は使わず、西町と同じ単純な決め方にする(この店での検証はまだできない)。
狙い度
  1〜3台用(v3) = 直近5日の差枚合計が少ない順
  5台以上用(v4) = 上 + 0.5×連続マイナス日数の順位
前日+3000枚超の台は候補から外す。直近5日に+3000枚超の日がある台は⚠表示のみ。
"""
import json, sys, pathlib
import numpy as np, pandas as pd
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from minami6_feat import load, build, LAY, COLS

CSV = ROOT / "minami6/minami6_kabaneri.csv"
EXCLUDE_PREV = 3000
df = load(CSV)
cur = df[df.date >= LAY]
asof = cur.date.max()
units_now = sorted(cur[cur.date == asof].machine.unique())
U = [str(u) for u in units_now]
pr = lambda s: s.rank(pct=True)

def score(td):
    """td: その日の行(machine が index)。(v3, v4) を返す"""
    w5 = 1 - pr(td.d5).fillna(.5)
    v3 = w5
    v4 = w5 + .5 * pr(td.sm)
    return v3, v4

nxt = asof + pd.Timedelta(days=1)
df2 = pd.concat([df, pd.DataFrame({"date": nxt, "machine": units_now, "diff": np.nan, "games": np.nan, "bb": np.nan, "rb": np.nan, "bona": np.nan})], ignore_index=True)
X = build(df2, keep_next=True)
te = X[X.date == nxt].set_index("machine").loc[units_now]
v3, v4 = score(te)
prevd = te.d1
NOTES = json.loads((ROOT / "minami6/notes.json").read_text(encoding="utf-8"))
note = {}
for d_, m_ in NOTES.items():
    if d_.startswith("_") or pd.Timestamp(d_) < asof: continue
    for u_, t_ in m_.items(): note[int(u_)] = t_
ex = [u for u in units_now if prevd[u] > EXCLUDE_PREV or u in note]
mx5 = cur[cur.date > asof - pd.Timedelta(days=5)].groupby("machine")["diff"].max()
r3 = [u for u in v3.sort_values(ascending=False, kind="stable").index if u not in ex]
r4 = [u for u in v4.sort_values(ascending=False, kind="stable").index if u not in ex]

import holidays as _h
jp = _h.Japan(years=[2025, 2026, 2027])
HOL = {str(d): n for d, n in sorted(jp.items()) if pd.Timestamp(d) > asof - pd.Timedelta(days=1) and pd.Timestamp(d) <= asof + pd.Timedelta(days=120)}
dayavg = cur.groupby("date")["diff"].mean()
kind = pd.Series(["祝日" if d in jp else ("土日" if d.dayofweek >= 5 else "平日") for d in dayavg.index], index=dayavg.index)
HSTAT = {k: {"mean": round(float(dayavg[kind == k].mean())), "median": round(float(dayavg[kind == k].median())), "n": int((kind == k).sum())} for k in ("祝日", "土日", "平日") if (kind == k).any()}
days = sorted(cur.date.unique())
piv = lambda k: cur.pivot(index="date", columns="machine", values=k).reindex(days)
D, G = piv("diff"), piv("games")
out = {
  "hall": "minami6",
  "asof": str(asof.date()),
  "days": [str(pd.Timestamp(d).date()) for d in days],
  "dayAvg": [round(v) for v in D.mean(axis=1)],
  # 島図(仮): 左の列=上から1017→1035、右の列=下から876→1003(1003と1017が向かい合う折り返し)
  "columns": [[str(u) for u in COLS[1] if str(u) in U], [str(u) for u in COLS[0][::-1] if str(u) in U]],
  "excludeThreshold": EXCLUDE_PREV,
  "candidates": len(r3),
  "holidays": HOL,
  "holStats": HSTAT,
  "units": {}
}
for u in units_now:
    out["units"][str(u)] = {
      "v3": round(float(v3[u]), 3), "rank3": (r3.index(u) + 1) if u in r3 else None,
      "v4": round(float(v4[u]), 3), "rank4": (r4.index(u) + 1) if u in r4 else None,
      "excluded": u in ex, "table": None,
      "g7": 0 if pd.isna(te.g7m[u]) else round(float(te.g7m[u])),
      "minus": int(te.sm[u]), "plus": int(te.sp[u]),
      "d5": None if pd.isna(te.d5[u]) else int(te.d5[u]),
      "exReason": note.get(u) or (f"前日{int(prevd[u]):+d}" if u in ex else None), "big5": bool(mx5.get(u, 0) > 3000), "max5": int(mx5.get(u, 0)),
      "g5": None if pd.isna(te.gm5[u]) else round(float(te.gm5[u])),
      "why": [],
      "diff": [None if pd.isna(x) else int(x) for x in D[u]],
      "g": [None if pd.isna(x) else int(x) for x in G[u]],
    }
# 過去日の推奨(その日より前のデータだけで順位付け)
past = []
for t in days[5:]:
    td = X[X.date == t].set_index("machine")
    if td.d1.isna().all(): continue
    a3, a4 = score(td)
    ok = [u for u in td.index if not (td.d1[u] > EXCLUDE_PREV)]
    past.append({"d": str(pd.Timestamp(t).date()), "r3": [str(u) for u in a3[ok].sort_values(ascending=False, kind="stable").index[:5]],
                 "r4": [str(u) for u in a4[ok].sort_values(ascending=False, kind="stable").index[:5]]})
out["past"] = past
(ROOT / "minami6.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("minami6.json を更新:", out["asof"], f"{len(days)}日 / {len(U)}台")
print("1〜3台用 上位5:", r3[:5], " 5台以上用 上位5:", r4[:5], " 除外:", [int(u) for u in ex])
