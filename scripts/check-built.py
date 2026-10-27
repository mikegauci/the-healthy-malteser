"""Focused release checks for the static output; run after npm run build."""
import json,sys,re
from pathlib import Path
from urllib.parse import urlparse,unquote,urljoin
from xml.etree import ElementTree as ET
from bs4 import BeautifulSoup
root=Path(__file__).resolve().parent.parent
routes=json.loads((root/'src/content/routes.json').read_text());config=json.loads((root/'vercel.json').read_text());redirects={x['source']:x['destination'] for x in config['redirects'] if not x.get('has')};paths={r['path'] for r in routes};errors=[]
assert sum(x['kind']=='post' for x in routes)==28
assert sum(x['kind']=='page' for x in routes)==4
assert sum(x['kind']=='print' for x in routes)==27
for route in routes:
 path=route['path'];file=root/'dist'/path.strip('/')/'index.html' if path!='/' else root/'dist/index.html'
 if not file.exists():errors.append('Missing output '+path);continue
 s=BeautifulSoup(file.read_text(),'html.parser')
 if not s.title or not s.title.get_text(strip=True):errors.append('Missing title '+path)
 if not s.select_one('meta[name=description]'):errors.append('Missing description '+path)
 if not route['noindex']:
  c=s.select_one('link[rel=canonical]')
  if not c or c['href']!='https://thehealthymalteser.com'+path:errors.append('Wrong canonical '+path)
 if s.select('form'):errors.append('Unexpected form '+path)
 for script in s.select('script[type="application/ld+json"]'):
  try:json.loads(script.text)
  except ValueError:errors.append('Invalid JSON-LD '+path)
 for el,attr in [(e,'src') for e in s.select('img[src],script[src],video[src]')]+[(e,'href') for e in s.select('link[rel=stylesheet],link[rel=icon]')]:
  url=el.get(attr,'')
  if url.startswith(('http:','https:','//')):errors.append('Unexpected remote asset '+url)
  elif url.startswith('/') and not (root/'dist'/unquote(url.lstrip('/'))).is_file():errors.append('Missing asset '+url)
 for a in s.select('a[href]'):
  u=urlparse(urljoin('https://thehealthymalteser.com'+path,a['href']))
  if u.hostname!='thehealthymalteser.com':continue
  target=u.path
  if target not in paths and target not in redirects and not (root/'dist'/unquote(target.lstrip('/'))).is_file():errors.append('Broken link '+path+' -> '+target)
 if s.select('iframe'):errors.append('Eager third-party player '+path)
 if not s.select_one('h1'):errors.append('Missing primary heading '+path)
sitemap=ET.parse(root/'dist/sitemap.xml').getroot();urls={e.text for e in sitemap.iter() if e.tag.endswith('loc')};expected={'https://thehealthymalteser.com'+r['path'] for r in routes if not r['noindex'] and r['kind']!='print'}
if urls!=expected:errors.append('Sitemap membership mismatch')
error=BeautifulSoup((root/'dist/404.html').read_text(),'html.parser')
if 'noindex' not in error.select_one('meta[name=robots]')['content']:errors.append('404 not noindex')
for f in ['robots.txt','llms.txt']:
 if not (root/'dist'/f).is_file():errors.append('Missing '+f)
for f in (root/'dist/styles').glob('*.css'):
 for u in re.findall(r'url\([\"\']?([^\)]+?)[\"\']?\)',f.read_text()):
  u=u.strip('"\' ')
  if u.startswith('/') and not (root/'dist'/u.lstrip('/')).is_file():errors.append('Missing CSS asset '+u)
if errors:
 print('\n'.join(sorted(set(errors))));sys.exit(1)
print(f'PASS: {len(routes)} routes; 28 posts, 4 pages, 27 print pages; {len(urls)} sitemap URLs; local links/assets, metadata/JSON-LD, no forms/eager players, 404 noindex, robots.txt and llms.txt.')
