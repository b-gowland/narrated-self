// Minimal static server for ../site, so the tests need no extra dependencies.
// Local development only: it adds the local guess API (wrangler dev on 127.0.0.1:8787) to the page's
// connect-src, so the published pages never list a local address. site/app.js only calls it on localhost.
import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { extname, join, normalize } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = fileURLToPath(new URL("../site/", import.meta.url));
const PORT = Number(process.env.PORT || 4173);
const TYPES = {
  ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".json": "application/json",
  ".css": "text/css", ".png": "image/png", ".svg": "image/svg+xml", ".txt": "text/plain; charset=utf-8",
  ".xml": "application/xml", ".woff2": "font/woff2"
};
const LOCAL_API = "http://127.0.0.1:8787";
const withLocalApi = body => body.toString().replace(/(connect-src [^;"]*)/, `$1 ${LOCAL_API}`);

createServer(async (req, res) => {
  let path = decodeURIComponent(new URL(req.url, "http://x").pathname);
  if (path.endsWith("/")) path += "index.html";
  const file = normalize(join(ROOT, path));
  if (!file.startsWith(normalize(ROOT))) { res.writeHead(403).end(); return; }
  try {
    let body = await readFile(file);
    if (extname(file) === ".html") body = withLocalApi(body);
    res.writeHead(200, { "Content-Type": TYPES[extname(file)] || "application/octet-stream" }).end(body);
  } catch {
    const body = await readFile(join(ROOT, "404.html")).catch(() => "Not found");
    res.writeHead(404, { "Content-Type": "text/html; charset=utf-8" }).end(body);
  }
}).listen(PORT, "127.0.0.1", () => console.log(`site on http://localhost:${PORT}`));
