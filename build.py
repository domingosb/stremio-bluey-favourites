"""Builds a static Stremio addon listing favourite Bluey episodes.

Episode data comes from Cinemeta. Each episode keeps its real IMDb video id
(tt7678620:season:episode), so your usual stream and subtitle addons find it.
"""
import json
import os
import re
import sys
import urllib.request

SHOW = 'tt7678620'
META_ID = 'blueyfavourites'
HERE = os.path.dirname(os.path.abspath(__file__))
# --lenient: skip titles that don't match (listing them in unmatched.txt) instead of stopping
LENIENT = '--lenient' in sys.argv


def norm(s):
    return re.sub(r'[^a-z0-9]', '', s.lower())


def write(path, data):
    path = os.path.join(HERE, *path.split('/'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


def read_favourites():
    with open(os.path.join(HERE, 'favourites.txt'), encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            title, _, pin = (p.strip() for p in line.partition('|'))
            yield title, pin


url = f'https://v3-cinemeta.strem.io/meta/series/{SHOW}.json'
show = json.load(urllib.request.urlopen(url, timeout=30))['meta']
episodes = [v for v in show['videos'] if v.get('season')]  # skip specials (season 0)

videos, unmatched = [], []
for title, pin in read_favourites():
    found = [v for v in episodes if norm(v.get('name') or v.get('title') or '') == norm(title)]
    if pin:  # "3:49" or "S3E49"
        m = re.fullmatch(r'[sS]?(\d+)[:eE](\d+)', pin)
        found = [v for v in found if m and (v['season'], v['episode']) == (int(m[1]), int(m[2]))]
    if len(found) != 1:
        problem = f'"{title}": {"no episode with that title" if not found else "several episodes match, add | season:episode"}'
        if not LENIENT:
            raise SystemExit(problem)
        unmatched.append(problem)
        continue
    v = found[0]
    videos.append({
        'id': v['id'],
        'title': f"{v.get('name') or v.get('title')} (S{v['season']}E{v['episode']})",
        'season': 1,
        'episode': len(videos) + 1,
        'released': v.get('released'),
        'thumbnail': v.get('thumbnail'),
        'overview': v.get('overview') or v.get('description'),
    })

description = 'My favourite Bluey episodes.'
meta = {
    'id': META_ID,
    'type': 'series',
    'name': 'Bluey: Favourites',
    'poster': show.get('poster'),
    'background': show.get('background'),
    'logo': show.get('logo'),
    'description': description,
    'genres': show.get('genres'),
    'videos': videos,
}

write('manifest.json', {
    'id': 'community.bluey.favourites',
    'version': '1.0.0',
    'name': 'Bluey Favourites',
    'description': description,
    'logo': show.get('logo'),
    'resources': ['catalog', {'name': 'meta', 'types': ['series'], 'idPrefixes': [META_ID]}],
    'types': ['series'],
    'idPrefixes': [META_ID],
    'catalogs': [{'type': 'series', 'id': 'bluey-favourites', 'name': 'Bluey Favourites'}],
})
write('catalog/series/bluey-favourites.json', {'metas': [
    {k: meta[k] for k in ('id', 'type', 'name', 'poster', 'background', 'logo', 'description', 'genres')}]})
write(f'meta/series/{META_ID}.json', {'meta': meta})
print(f'Built {len(videos)} episodes:')
for v in videos:
    print(f"  {v['episode']:2}. {v['title']}")
if LENIENT:
    with open(os.path.join(HERE, 'unmatched.txt'), 'w', encoding='utf-8') as f:
        f.write(''.join(u + '\n' for u in unmatched))
for u in unmatched:
    print('Skipped', u)
