#!/usr/bin/env python3
import json
import re
from pathlib import Path

root = Path(__file__).resolve().parents[1]
data_dir = root / 'data'
out_types = ['cards', 'relics', 'characters', 'keywords', 'builds']


def load(name):
    return json.loads((data_dir / f'{name}.json').read_text())


def slugify(s):
    return re.sub(r'(^-|-$)', '', re.sub(r'[^a-z0-9]+', '-', s.lower()))


def write_if_changed(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text() == content:
        return False
    path.write_text(content)
    return True


all_items = []
for t in out_types:
    for x in load(t):
        x['_routeType'] = t
        all_items.append(x)
idx = {x['id']: x for x in all_items}


def related_links(item, limit=12):
    links = []
    for sid in item.get('synergies', []):
        y = idx.get(sid)
        if not y:
            continue
        links.append((y['name'], f"/{y['_routeType']}/{y['id']}/"))
        if len(links) >= limit:
            break
    return links


def title_for(ptype, name):
    if ptype == 'cards':
        return f"{name} – Best Uses, Synergies & Tier | STS2 Guide"
    if ptype == 'relics':
        return f"{name} – How to Use & Best Builds | STS2 Guide"
    if ptype == 'builds':
        return f"{name} Build Guide – Strategy & Tips | STS2"
    if ptype == 'keywords':
        return f"{name} Guide – Strategy & Synergies | STS2"
    return f"{name} Guide | STS2 Guide"


def desc_for(ptype, name):
    if ptype == 'cards':
        return f"Learn best uses, top synergies, common mistakes, and tier context for {name} in Slay the Spire 2 runs and climbing routes."
    if ptype == 'relics':
        return f"Discover how to use {name}, strongest pairings, and best build paths in Slay the Spire 2 with practical tips for consistent wins."
    if ptype == 'builds':
        return f"{name} build guide for Slay the Spire 2: core plan, power spikes, key synergies, and mistakes to avoid through all acts."
    if ptype == 'keywords':
        return f"{name} keyword guide for Slay the Spire 2 with strategy tips, best synergies, and when it matters most in real runs."
    return f"Practical Slay the Spire 2 strategy guide for {name}."


def page_html(item, ptype):
    name = item['name']
    title = title_for(ptype, name)
    desc = desc_for(ptype, name)

    facts = []
    for k in ['type', 'rarity', 'cost', 'role', 'category', 'character', 'actFocus']:
        if k in item:
            facts.append(f"<span class='tag'>{k}: {item[k]}</span>")

    rel = related_links(item, 12)
    rel_html = ''.join([f"<li><a href='{u}'>{n}</a></li>" for n, u in rel]) or '<li>No related links yet.</li>'

    how = ''.join([f"<li>{x}</li>" for x in item.get('howToUse', [])]) or '<li>Not enough data yet — check back soon.</li>'
    mistakes = ''.join([f"<li>{x}</li>" for x in item.get('countersOrRisks', [])]) or '<li>Not enough data yet — check back soon.</li>'
    src = ''.join([f"<li><a target='_blank' rel='noopener' href='{s['url']}'>{s['label']}</a></li>" for s in item.get('sources', [])])

    breadcrumb = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": "https://slaythespire2guide.com/"},
            {"@type": "ListItem", "position": 2, "name": ptype.title(), "item": f"https://slaythespire2guide.com/{ptype}/"},
            {"@type": "ListItem", "position": 3, "name": name, "item": f"https://slaythespire2guide.com/{ptype}/{item['id']}/"},
        ],
    }
    article = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": desc,
        "author": {"@type": "Organization", "name": "STS2 Guide"},
        "dateModified": item.get('updatedAt', item.get('last_updated', '')),
    }

    return f"""<!doctype html><html lang='en'><head><meta charset='utf-8'/><meta name='viewport' content='width=device-width,initial-scale=1'/><title>{title}</title><meta name='description' content='{desc}'/><link rel='canonical' href='https://slaythespire2guide.com/{ptype}/{item['id']}/'/><link rel='stylesheet' href='../../style.css'/><script async src='https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=pub-7734599043419848' crossorigin='anonymous'></script><script type='application/ld+json'>{json.dumps(article)}</script><script type='application/ld+json'>{json.dumps(breadcrumb)}</script></head><body>
<nav><div class='nav-logo'>STS2 Guide</div><ul class='nav-links'><li><a href='/'>Home</a></li><li><a href='/cards/'>Cards</a></li><li><a href='/relics/'>Relics</a></li><li><a href='/builds/'>Builds</a></li><li><a href='/keywords/'>Keywords</a></li><li><a href='/updates.html'>Updates</a></li></ul></nav>
<div class='section'><div class='grid-2'><div>
<h1>{name}</h1><p class='section-sub detail-sub'>{item.get('shortSummary', '')}</p><p class='detail-facts'>{''.join(facts)}</p>
<div class='ad-slot' data-slot='2100000001' data-format='auto'></div>
<div class='card' id='how'><h2>How to use</h2><ul>{how}</ul></div>
<div class='ad-slot' data-slot='2100000002' data-format='rectangle'></div>
<div class='card' id='mistakes'><h2>Common mistakes</h2><ul>{mistakes}</ul></div>
<div class='card' id='spike'><h2>When it spikes</h2><p>{name} usually spikes when your deck has enough draw + energy support and your route gives room to scale before major elites/bosses.</p></div>
<div class='card' id='synergies'><h2>Best synergies</h2><ul>{rel_html}</ul></div>
<div class='card' id='related'><h2>Related</h2><ul>{rel_html}</ul></div>
<div class='grid-2'><div class='card'><h3>Related builds</h3><ul>{rel_html}</ul></div><div class='card'><h3>Best cards with this</h3><ul>{rel_html}</ul></div></div>
<div class='card'><h3>Sources</h3><ul>{src}</ul></div>
<div class='ad-slot' data-slot='2100000003' data-format='auto'></div>
<p><a class='btn' href='/{ptype}/'>Back to {ptype} hub</a> <a class='btn btn-outline' href='/updates.html'>Latest updates</a></p>
</div>
<aside class='card' style='height:fit-content;position:sticky;top:84px'><h3>Jump to</h3><ul><li><a href='#how'>How to use</a></li><li><a href='#mistakes'>Common mistakes</a></li><li><a href='#spike'>When it spikes</a></li><li><a href='#synergies'>Best synergies</a></li></ul></aside>
</div></div><script src='/components/ad-slot.js'></script></body></html>"""


for t in out_types:
    hub = root / t
    hub.mkdir(exist_ok=True)
    items = load(t)
    intro = {
        'cards': 'Best cards and practical play patterns for consistent runs.',
        'relics': 'Relic value, timing, and synergy tradeoffs.',
        'characters': 'Character gameplans, strengths, and route choices.',
        'keywords': 'Mechanic glossary with practical use cases.',
        'builds': 'Archetype playbooks for act progression and boss fights.',
    }[t]
    top_rows = ''.join([f"<li><a href='/{t}/{x['id']}/'>{x['name']}</a></li>" for x in items[:25]])
    rest_rows = ''.join([f"<li><a href='/{t}/{x['id']}/'>{x['name']}</a></li>" for x in items[25:]])
    hub_html = f"<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>STS2 {t.title()} Hub | STS2 Guide</title><meta name='description' content='{intro}'><link rel='canonical' href='https://slaythespire2guide.com/{t}/'><link rel='stylesheet' href='../style.css'><script async src='https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=pub-7734599043419848' crossorigin='anonymous'></script></head><body><nav><div class='nav-logo'>STS2 Guide</div><ul class='nav-links'><li><a href='/'>Home</a></li><li><a href='/updates.html'>Updates</a></li></ul></nav><div class='section'><h1>{t.title()} Hub</h1><p class='section-sub'>{intro}</p><div class='ad-slot' data-slot='2200000001' data-format='auto'></div><ul>{top_rows}</ul><div class='ad-slot' data-slot='2200000002' data-format='rectangle'></div><ul>{rest_rows}</ul></div><script src='/components/ad-slot.js'></script></body></html>"
    (hub / 'index.html').write_text(hub_html)

count = 0
for t in out_types:
    items = load(t)
    for it in items:
        d = root / t / it['id']
        d.mkdir(parents=True, exist_ok=True)
        (d / 'index.html').write_text(page_html(it, t))
        count += 1

(root / 'tier').mkdir(exist_ok=True)
(root / 'tier' / 'index.html').write_text("<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>STS2 Tier Hub</title><meta name='description' content='Tier snapshots for cards, relics, and build archetypes.'><link rel='stylesheet' href='../style.css'></head><body><nav><div class='nav-logo'>STS2 Guide</div></nav><div class='section'><h1>Tier Hub</h1></div></body></html>")

urls = ['https://slaythespire2guide.com/', 'https://slaythespire2guide.com/updates.html', 'https://slaythespire2guide.com/early-access.html']
for t in out_types + ['tier']:
    urls.append(f'https://slaythespire2guide.com/{t}/')
for t in out_types:
    for it in load(t):
        urls.append(f'https://slaythespire2guide.com/{t}/{it["id"]}/')

xml = ["<?xml version='1.0' encoding='UTF-8'?>", "<urlset xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'>"]
for u in urls:
    pr = '0.8'
    if any(u.endswith(f'/{h}/') for h in ['cards', 'relics', 'builds', 'keywords']):
        pr = '1.0'
    elif u.endswith('/tier/'):
        pr = '1.0'
    elif u.endswith('.com/') or u.endswith('updates.html') or u.endswith('early-access.html'):
        pr = '0.9'
    xml.append(f"<url><loc>{u}</loc><priority>{pr}</priority></url>")
xml.append("</urlset>")
(root / 'sitemap.xml').write_text(''.join(xml))
(root / 'robots.txt').write_text("User-agent: *\nAllow: /\nSitemap: https://slaythespire2guide.com/sitemap.xml\n")
print('generated pages', count, 'urls', len(urls))
