#!/usr/bin/env python3
"""クラブイーグル麻生 カバネリ海門決戦: eagle/eagle_kabaneri.csv から eagle.json(サイト用)を作る。
使い方: python3 tools/build_data_eagle.py   (リポジトリのルートで実行。pandas と scikit-learn が必要)

狙い度(検証は ml/ と README を参照)
  1〜3台用(v3) = 勾配ブースティングの予測順位 + 1年表スコア順位 + 0.5×前日差枚1位の隣 + 0.5×前日ボーナス回数の少なさ順位
  5台以上用(v4) = 1年表スコア順位 + 0.5×前日差枚1位の隣 + 0.5×前日ボーナス回数の少なさ順位
前日+3000枚超の台は候補から外す。
"""
import json, sys, pathlib, statistics as st, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import picker_eagle as p
from eagle_feat import load, build, LAY
from sklearn.ensemble import HistGradientBoostingRegressor as HGR

CSV = ROOT / "eagle/eagle_kabaneri.csv"
EXCLUDE_PREV = 3000
df = load(CSV)
cur = df[df.date >= LAY]
asof = cur.date.max()
units_now = sorted(cur[cur.date == asof].machine.unique())
nxt = asof + pd.Timedelta(days=1)
df2 = pd.concat([df, pd.DataFrame({"date": nxt, "machine": units_now, "diff": np.nan, "games": np.nan, "bb": np.nan, "rb": np.nan, "bona": np.nan})], ignore_index=True)
X = build(df2, keep_next=True)
FE = [c for c in X.columns if c not in ("date", "machine", "y", "yrel", "layout")]
tr = X[(X.date < nxt) & X.y.notna() & X.d1.notna()]
gbm = HGR(max_iter=150, learning_rate=0.05, max_leaf_nodes=15, min_samples_leaf=40, l2_regularization=1.0, random_state=0)
gbm.fit(tr[FE], tr.yrel.clip(-8000, 12000))
te = X[X.date == nxt].set_index("machine")

# 1年表スコア(picker_eagle の表と同じ当てはめ)
data = {}
for r in cur.itertuples():
    g = None if pd.isna(r.games) else int(r.games)
    data.setdefault(r.date.date(), {})[str(r.machine)] = dict(g=g, diff=int(r.diff))
hist = p.contiguous(sorted(data))
ts, why = p.table_score(data, hist)
U = [str(u) for u in units_now]
pr = lambda s: s.rank(pct=True)
tab = pr(pd.Series({u: ts[str(u)] for u in units_now}))
nb = te.nb_best1.reindex(units_now).fillna(0)
bw = 1 - te.b1_r.reindex(units_now).fillna(.5)
g = pr(pd.Series(gbm.predict(te.loc[units_now, FE]), index=units_now))
v3 = g + tab + .5 * nb + .5 * bw
v4 = tab + .5 * nb + .5 * bw
prevd = te.d1.reindex(units_now)
ex = [u for u in units_now if prevd[u] > EXCLUDE_PREV]
r3 = [u for u in v3.sort_values(ascending=False).index if u not in ex]
r4 = [u for u in v4.sort_values(ascending=False).index if u not in ex]

days = sorted(cur.date.unique())
piv = lambda k: cur.pivot(index="date", columns="machine", values=k).reindex(days)
D, G, B = piv("diff"), piv("games"), piv("bona")
out = {
  "hall": "eagle",
  "asof": str(asof.date()),
  "days": [str(pd.Timestamp(d).date()) for d in days],
  "dayAvg": [round(v) for v in D.mean(axis=1)],
  "columns": [[u for u in U if int(u) <= 56], [u for u in U if int(u) >= 57]],  # 46〜56 と 57〜68 は別の島
  "excludeThreshold": EXCLUDE_PREV,
  "candidates": len(r3),
  "units": {}
}
for u in units_now:
    m, pl = p.streaks(data, hist, str(u))
    out["units"][str(u)] = {
      "v3": round(float(v3[u]), 3), "rank3": (r3.index(u) + 1) if u in r3 else None,
      "v4": round(float(v4[u]), 3), "rank4": (r4.index(u) + 1) if u in r4 else None,
      "excluded": u in ex, "table": round(ts[str(u)], 1), "g7": round(float(te.g7m.get(u, np.nan))) if not np.isnan(te.g7m.get(u, np.nan)) else 0,
      "minus": m, "plus": pl, "nbBest1": bool(nb[u]), "bona1": None if pd.isna(B[u].iloc[-1]) else int(B[u].iloc[-1]),
      "ai": round(float(g[u]), 3),
      "why": [[n, r] for n, r in why[str(u)]],
      "diff": [None if pd.isna(x) else int(x) for x in D[u]],
      "g": [None if pd.isna(x) else int(x) for x in G[u]],
    }
(ROOT / "eagle.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("eagle.json を更新:", out["asof"], f"{len(days)}日 / {len(U)}台")
print("1〜3台用 上位5:", r3[:5], " 5台以上用 上位5:", r4[:5], " 除外:", [int(u) for u in ex])
