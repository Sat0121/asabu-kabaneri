/* 台選び(麻生ハッピー・イーグル麻生)をオフラインでも開けるようにする。
   通信できるときは常に最新を取りに行き(ネットワーク優先)、取れた内容を保存する。
   通信できないときは最後に保存した内容を返す。 */
const CACHE = "kabaneri-picker-v4";  // 中身を大きく変えたら番号を上げる
const CORE = ["./", "index.html", "eagle.html", "n24.html", "nishi.html", "data.json", "eagle.json", "n24.json", "nishi.json", "posters.json"];
self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => Promise.all(CORE.map(u => c.add(new Request(u, { cache: "reload" })).catch(() => {})))).then(() => self.skipWaiting()));
});
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", e => {
  const req = e.request, url = new URL(req.url);
  if (req.method !== "GET" || url.origin !== location.origin) return;
  e.respondWith((async () => {
    const cache = await caches.open(CACHE);
    try {
      const res = await fetch(req, { cache: "no-cache" });
      if (res.ok) cache.put(req, res.clone()).catch(() => {});
      return res;
    } catch (err) {
      const hit = await cache.match(req, { ignoreSearch: true }) || (req.mode === "navigate" ? await cache.match(url.pathname.endsWith("eagle.html") ? "eagle.html" : url.pathname.endsWith("n24.html") ? "n24.html" : url.pathname.endsWith("nishi.html") ? "nishi.html" : "index.html") : null);
      if (hit) {  // 保存分を返したことをページに知らせる印を付ける
        const h = new Headers(hit.headers); h.set("X-KB-Offline", "1");
        return new Response(await hit.blob(), { status: 200, statusText: "OK", headers: h });
      }
      throw err;
    }
  })());
});
