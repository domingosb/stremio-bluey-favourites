"""Builds a static Stremio addon listing favourite Bluey episodes.

Episode data comes from Cinemeta. Each episode keeps its real IMDb video id
(tt7678620:season:episode), so your usual stream and subtitle addons find it.
"""
import json
import os
import urllib.request

SHOW = 'tt7678620'
META_ID = 'blueyfavourites'
HERE = os.path.dirname(os.path.abspath(__file__))


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

videos = []
for title, pin in read_favourites():
    found = [v for v in episodes if (v.get('name') or v.get('title') or '').strip().lower() == title.lower()]
    if pin:
        found = [v for v in found if f"{v['season']}:{v['episode']}" == pin]
    if len(found) != 1:
        raise SystemExit(f'"{title}": {len(found)} matches, pin it with "| season:episode"')
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
