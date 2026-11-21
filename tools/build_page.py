#!/usr/bin/env python3
"""tools/index.template.html にアイコン(vendor/icons/*.svg)を埋め込んで index.html を作る。"""
import re, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
syms = ""
for f in sorted((ROOT / "vendor/icons").glob("*.svg")):
    paths = "".join(re.findall(r"<path[^>]*/>", f.read_text()))
    syms += f'<symbol id="i-{f.stem}" viewBox="0 -960 960 960">{paths}</symbol>'
sprite = f'<svg width="0" height="0" style="position:absolute" aria-hidden="true">{syms}</svg>'
html = (ROOT / "tools/index.template.html").read_text(encoding="utf-8").replace("__SPRITE__", sprite)
used = set(re.findall(r'#i-([\w-]+)', html)) | set(re.findall(r'icon\("([\w-]+)"', html))
have = {f.stem for f in (ROOT / "vendor/icons").glob("*.svg")}
missing = {u for u in used if u not in have and "$" not in u}
assert not missing, f"アイコンが足りません: {missing}"
(ROOT / "index.html").write_text(html, encoding="utf-8")
print("index.html を作成", len(html), "bytes")
