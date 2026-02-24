#!/usr/bin/env python3
import json
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
CACHE = DATA / "cache"
CACHE.mkdir(parents=True, exist_ok=True)
RAW = DATA / "raw_sources.json"
META = CACHE / "http_meta.json"

SOURCES = {
    "sts2_data": "https://cdn.jsdelivr.net/gh/bertgoldstein1969-sys/sts2-data@main/sts2-data.json",
    "steam_news": "https://store.steampowered.com/feeds/news/app/2868840/",
    "reddit_sts": "https://www.reddit.com/r/slaythespire/new/.rss"
}


def load_meta():
    if META.exists():
        return json.loads(META.read_text())
    return {}


def save_meta(m):
    META.write_text(json.dumps(m, indent=2))


def fetch(url, key, meta, retries=3, timeout=20):
    headers = {"User-Agent": "STS2-AutoUpdater/1.0"}
    c = meta.get(key, {})
    if c.get("etag"):
        headers["If-None-Match"] = c["etag"]
    if c.get("last_modified"):
        headers["If-Modified-Since"] = c["last_modified"]

    for i in range(retries):
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                body = r.read().decode("utf-8", errors="replace")
                meta[key] = {
                    "etag": r.headers.get("ETag"),
                    "last_modified": r.headers.get("Last-Modified"),
                    "fetched_at": int(time.time())
                }
                return {"status": "ok", "body": body}
        except urllib.error.HTTPError as e:
            if e.code == 304:
                return {"status": "not_modified", "body": None}
            if i == retries - 1:
                return {"status": "error", "error": f"HTTP {e.code}"}
            time.sleep(2 ** i)
        except Exception as e:
            if i == retries - 1:
                return {"status": "error", "error": str(e)}
            time.sleep(2 ** i)


def parse_rss(xml_text, limit=40):
    out = []
    try:
        root = ET.fromstring(xml_text)
        for it in root.findall('.//item')[:limit]:
            out.append({
                "title": (it.findtext("title") or "").strip(),
                "url": (it.findtext("link") or "").strip(),
                "publishedAt": (it.findtext("pubDate") or "").strip(),
                "summary": (it.findtext("description") or "").strip(),
            })
    except Exception:
        pass
    return out


def main():
    meta = load_meta()
    raw = {"generatedAt": int(time.time()), "sources": {}, "errors": []}

    for key, url in SOURCES.items():
        res = fetch(url, key, meta)
        if res["status"] == "error":
            raw["errors"].append({"source": key, "error": res.get("error")})
            continue

        if res["status"] == "not_modified" and RAW.exists():
            prev = json.loads(RAW.read_text())
            if key in prev.get("sources", {}):
                raw["sources"][key] = prev["sources"][key]
            continue

        body = res.get("body") or ""
        if key == "sts2_data":
            try:
                raw["sources"][key] = json.loads(body)
            except Exception:
                raw["errors"].append({"source": key, "error": "invalid json"})
        else:
            raw["sources"][key] = parse_rss(body)

    RAW.write_text(json.dumps(raw, indent=2))
    save_meta(meta)
    print("raw_sources_updated=1")


if __name__ == "__main__":
    main()
