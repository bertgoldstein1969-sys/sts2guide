#!/usr/bin/env python3
import json
import os
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
    tmp = META.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(m, indent=2))
    tmp.replace(META)


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
    if os.getenv("STS2_SIMULATE_FETCH_FAIL") == "1":
        raise SystemExit("simulated fetch failure")

    meta = load_meta()
    prev = {}
    if RAW.exists():
        try:
            prev = json.loads(RAW.read_text())
        except Exception:
            prev = {}

    raw = {"generatedAt": int(time.time()), "sources": {}, "errors": []}
    source_changed = False

    ok_sources = 0
    for key, url in SOURCES.items():
        res = fetch(url, key, meta)
        if res["status"] == "error":
            raw["errors"].append({"source": key, "error": res.get("error")})
            if key in prev.get("sources", {}):
                raw["sources"][key] = prev["sources"][key]
            continue

        if res["status"] == "not_modified":
            if key in prev.get("sources", {}):
                raw["sources"][key] = prev["sources"][key]
                ok_sources += 1
            continue

        body = res.get("body") or ""
        if key == "sts2_data":
            try:
                parsed = json.loads(body)
                raw["sources"][key] = parsed
                ok_sources += 1
                if parsed != prev.get("sources", {}).get(key):
                    source_changed = True
            except Exception:
                raw["errors"].append({"source": key, "error": "invalid json"})
                if key in prev.get("sources", {}):
                    raw["sources"][key] = prev["sources"][key]
        else:
            parsed = parse_rss(body)
            raw["sources"][key] = parsed
            ok_sources += 1
            if parsed != prev.get("sources", {}).get(key):
                source_changed = True

    # fail-safe: if everything failed and no previous sources were retained, do not overwrite RAW
    if ok_sources == 0 and not raw["sources"]:
        raise SystemExit("fetch failed for all sources; preserving last known good raw_sources.json")

    # if nothing changed, keep previous generatedAt and avoid churn
    prev_errors = prev.get("errors", []) if isinstance(prev, dict) else []
    if not source_changed and raw["errors"] == prev_errors and prev.get("sources"):
        raw["generatedAt"] = prev.get("generatedAt", raw["generatedAt"])
        if RAW.exists():
            save_meta(meta)
            print(f"raw_sources_updated=0 sources_ok={ok_sources} errors={len(raw['errors'])}")
            return

    tmp = RAW.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(raw, indent=2))
    tmp.replace(RAW)
    save_meta(meta)
    print(f"raw_sources_updated=1 sources_ok={ok_sources} errors={len(raw['errors'])}")


if __name__ == "__main__":
    main()
