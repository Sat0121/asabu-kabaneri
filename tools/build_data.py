#!/usr/bin/env python3
"""kabaneri_history.txt から data.json(サイト用)を作る。
使い方: python3 tools/build_data.py   (リポジトリのルートで実行)
"""
import json, statistics as st, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import picker as p

data = p.load(ROOT / "kabaneri_history.txt")
days = sorted(data)
hist = p.contiguous(days)                 # 最新日から空白なく続く区間(新しい順)
v3, ts, g7, _, why = p.hybrid(data, hist, wide=False)
v4 = p.hybrid(data, hist, wide=True)[0]
units = sorted(v3, key=p.num)
r3 = sorted(units, key=lambda u: -v3[u]); r4 = sorted(units, key=lambda u: -v4[u])
out = {
  "asof": str(days[-1]),
  "days": [str(d) for d in days],
  "dayAvg": [round(st.mean(v["diff"] for v in data[d].values())) for d in days],
  "columns": p.COLUMNS,
  "units": {}
}
for u in units:
    m, pl = p.streaks(data, hist, u)
    out["units"][u] = {
      "v3": round(v3[u], 3), "rank3": r3.index(u) + 1,
      "v4": round(v4[u], 3), "rank4": r4.index(u) + 1,
      "table": round(ts[u], 1), "g7": round(g7[u]), "minus": m, "plus": pl,
      "why": [[n, r] for n, r in why[u]],
      "diff": [data[d][u]["diff"] if u in data[d] else None for d in days],
      "g": [data[d][u]["g"] if u in data[d] else None for d in days],
    }
(ROOT / "data.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print("data.json を更新:", out["asof"], f"{len(days)}日 / {len(units)}台")
print("v3 上位5:", r3[:5], " v4 上位5:", r4[:5])
