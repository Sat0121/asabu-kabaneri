#!/usr/bin/env python3
"""tools/index.template.html にアイコン(vendor/icons/*.svg)を埋め込んで index.html を作る。"""
import re, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
syms = ""
for f in sorted((ROOT / "vendor/icons").glob("*.svg")):
    paths = "".join(re.findall(r"<path[^>]*/>", f.read_text()))
    syms += f'<symbol id="i-{f.stem}" viewBox="0 -960 960 960">{paths}</symbol>'
sprite = f'<svg width="0" height="0" style="position:absolute" aria-hidden="true">{syms}</svg>'
import json
HALLS = [
  dict(id="asabu", out="index.html", data="data.json", name="麻生ハッピー", short="ハッピー", sub="麻生ハッピー・スマスロ③",
       whereL="781側の列", whereR="756側の列", headL="781〜815", headR="756〜780", counter="カウンター側", aisle="通路", about="about_asabu.html"),
  dict(id="eagle", out="eagle.html", data="eagle.json", name="クラブイーグル麻生", short="イーグル", sub="クラブイーグル麻生",
       whereL="46〜56の島", whereR="57〜68の島", headL="46〜56の島", headR="57〜68の島", counter="番号の小さい台を手前に表示（向きは未確認）", aisle="", about="about_eagle.html"),
]
tpl = (ROOT / "tools/index.template.html").read_text(encoding="utf-8").replace("__SPRITE__", sprite)
for H in HALLS:
    sw = "".join(f'<a href="{h["out"] if h["out"]!="index.html" else "./"}"{" aria-current=page" if h is H else ""}>{h["short"]}</a>' for h in HALLS)
    html = (tpl.replace("__HALL_NAME__", H["name"]).replace("__HALL_SUB__", H["sub"]).replace("__HALL_SWITCH__", sw)
              .replace("__ABOUT__", (ROOT / "tools" / H["about"]).read_text(encoding="utf-8"))
              .replace("__HALL__", json.dumps({k: H[k] for k in ("id","data","sub","whereL","whereR","headL","headR","counter","aisle")}, ensure_ascii=False)))
    (ROOT / H["out"]).write_text(html, encoding="utf-8")
    print(H["out"], "を作成", len(html), "bytes")
used = set(re.findall(r'#i-([\w-]+)', html)) | set(re.findall(r'icon\("([\w-]+)"', html))
have = {f.stem for f in (ROOT / "vendor/icons").glob("*.svg")}
missing = {u for u in used if u not in have and "$" not in u}
assert not missing, f"アイコンが足りません: {missing}"

