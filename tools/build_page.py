#!/usr/bin/env python3
"""tools/kabaneri.template.html と VVV2 の共通CSS から index.html(麻生ハッピー) と eagle.html(イーグル麻生) を作る。"""
import re, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
syms = ""
for f in sorted((ROOT / "vendor/icons").glob("*.svg")):
    paths = "".join(re.findall(r"<path[^>]*/>", f.read_text()))
    syms += f'<symbol id="i-{f.stem}" viewBox="0 -960 960 960">{paths}</symbol>'
sprite = f'<svg width="0" height="0" style="position:absolute" aria-hidden="true">{syms}</svg>'
import json
HALLS = [
  dict(id="asabu", out="index.html", data="data.json", name="麻生ハッピー", short="ハッピー",
       whereL="781側の列", whereR="756側の列", headL="781〜815", headR="756〜780", top="", counter="カウンター側", aisle="通路", emptyL="", **{"from": "カウンター側から"}, about="about2_asabu.html"),
  dict(id="eagle", out="eagle.html", data="eagle.json", name="クラブイーグル麻生", short="イーグル",
       whereL="46〜56の島", whereR="57〜68の島", headL="46〜56の島", headR="57〜68の島", top="道路側", counter="中央通路側", aisle="", emptyL="←喫煙所", **{"from": "中央通路側から"}, about="about2_eagle.html"),
  dict(id="n24", out="n24.html", data="n24.json", name="ハッピー二十四軒", short="ハッピー二十四軒",
       whereL="1156〜1165の列", whereR="1133〜1155の列", headL="1156〜1165", headR="1133〜1155", top="", counter="", aisle="通路", emptyL="", **{"from": "下から"}, about="about2_n24.html"),
]
for h in HALLS: h.setdefault("short", h["name"])
HALLS[0]["short"] = "麻生ハッピー"; HALLS[1]["short"] = "イーグル麻生"
PAGES = {h["id"]: (h["out"] if h["out"] != "index.html" else "./?h=asabu") for h in HALLS}
base_css = (ROOT / "tools/vvv2_base.css.html").read_text(encoding="utf-8")
tpl = (ROOT / "tools/kabaneri.template.html").read_text(encoding="utf-8").replace("__BASE_CSS__", base_css)
for H in HALLS:
    sw = "".join(f'<option value="{PAGES[h["id"]]}" data-id="{h["id"]}"{" selected" if h is H else ""}>{h["short"]}</option>' for h in HALLS)
    html = (tpl.replace("__HALL_NAME__", H["name"]).replace("__HALL_SWITCH__", sw)
              .replace("__ABOUT__", (ROOT / "tools" / H["about"]).read_text(encoding="utf-8"))
              .replace("__HALL__", json.dumps({**{k: H.get(k, "") for k in ("id","data","whereL","whereR","headL","headR","top","counter","aisle","emptyL","from")}, "pages": PAGES}, ensure_ascii=False)))
    assert "__" not in html.replace("__proto__", ""), "置換漏れ"
    (ROOT / H["out"]).write_text(html, encoding="utf-8")
    print(H["out"], "を作成", len(html), "bytes")
