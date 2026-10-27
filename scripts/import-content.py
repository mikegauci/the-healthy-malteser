"""One-time migration of verified local WordPress exports to standalone Astro content.
Install scripts/requirements-import.txt, then set MIGRATION_SOURCE_DIR to the
archive containing routes.json, asset-map.json, css-map.json and fetched HTML.
No source website or CMS is contacted by the application or production build.
"""
import os,json,re,hashlib,html,copy
from pathlib import Path
from urllib.parse import urlparse,urljoin,unquote,urlunparse
from bs4 import BeautifulSoup,Comment
from PIL import Image
ROOT=Path(__file__).resolve().parent.parent
SOURCE=Path(os.environ.get('MIGRATION_SOURCE_DIR','/workspace/migration-source'))
DEST=ROOT/'src/content';DEST.mkdir(parents=True,exist_ok=True);(DEST/'pages').mkdir(exist_ok=True)
MEDIA=json.loads((SOURCE/'asset-map.json').read_text());CSS=json.loads((SOURCE/'css-map.json').read_text());SOURCES=json.loads((SOURCE/'routes.json').read_text())
ORIGIN='https://thehealthymalteser.com'
posts=json.loads((SOURCE/'posts-1.json').read_text());pages=json.loads((SOURCE/'pages-1.json').read_text());by_path={urlparse(x['link']).path:x for x in posts+pages}
missing=set();print_routes={};routes=[];reference=Path('/workspace/migration-reference');reference.mkdir(exist_ok=True)
def asset_key(u):
 p=urlparse(urljoin(ORIGIN,u))
 if p.hostname in ['thehealthymalteser.com','www.thehealthymalteser.com'] and p.path.startswith(('/wp-content/','/wp-includes/')):return ORIGIN+p.path
 return None
def local(u,absolute=False):
 k=asset_key(u)
 if k in MEDIA:return (ORIGIN if absolute else '')+MEDIA[k]['path']
 return u

def css_urls(text):
 return re.sub(r'url\([\"\']?([^\)]+?)[\"\']?\s*\)',lambda m:'url("'+local(m.group(1).strip('"\' '))+'")' if asset_key(m.group(1).strip('"\' ')) in MEDIA else m.group(0),text)

def style_file(text):
 text=css_urls(text)
 name='page-'+hashlib.sha256(text.encode()).hexdigest()[:12]+'.css';(ROOT/'public/styles'/name).write_text(text);return '/styles/'+name

def decode_email(v):
 b=bytes.fromhex(v);return ''.join(chr(x^b[0]) for x in b[1:])

def clean_fragment(fragment,path,poster=None):
 s=BeautifulSoup(str(fragment),'html.parser')
 for signup in s.select('.wpcf7'):
  section=signup.find_parent('section')
  if section:section.decompose()
 for x in s.find_all(string=lambda x:isinstance(x,Comment)):x.extract()
 for x in s.select('script, link, #respond, .comment-respond, .reply, .wpcf7, form, .wprm-comment-rating, .comment-form-rating, .wprm-recipe-rating'):
  x.decompose()
 # No signup form or inactive signup promise, per owner instruction.
 for x in s.find_all(['p','h2','h3']):
  if 'Subscribe here to receive' in x.get_text() or 'Want to make the switch to a healthier lifestyle?' in x.get_text():x.decompose()
 for x in s.select('[data-cfemail]'):
  email=decode_email(x['data-cfemail']);x['href']='mailto:'+email;x.string=email;del x['data-cfemail'];x.attrs.pop('class',None)
 for x in s.select('a[href]'):
  href=x['href']
  if '/cdn-cgi/l/email-protection#' in href:
   email=decode_email(href.split('#',1)[1]);x['href']='mailto:'+email;x['aria-label']='Email '+email
  elif '/cdn-cgi/l/email-protection' in href:x.decompose();continue
  else:
   u=urlparse(urljoin(ORIGIN,href))
   if u.hostname in ['thehealthymalteser.com','www.thehealthymalteser.com']:
    if asset_key(href) in MEDIA:x['href']=local(href)
    elif u.path.startswith('/wprm_print/'):
     print_path=u.path.rstrip('/')+'/';print_routes[print_path]=path;x['href']=print_path
    else:x['href']=u.path+('?' + u.query if u.query else '')+('#'+u.fragment if u.fragment else '')
  if 'href' not in x.attrs:continue
  if x['href'].endswith('#respond'):
   if x.get_text(strip=True).lower().startswith('leave'):
    x.decompose();continue
   x['href']=x['href'].replace('#respond','#comments')
  if x.get('target')=='_blank':x['rel']=list(set(x.get('rel',[])+['noopener','noreferrer']))
  if 'wprm-recipe-pin' in x.get('class',[]):x.attrs.pop('role',None)
 for img in s.select('img'):
  src=img.get('src','')
  if 's.w.org/images/core/emoji/' in src:
   img.replace_with(img.get('alt',''));continue
  key=asset_key(src);r=MEDIA.get(key)
  if r and r['path'].endswith('.mp4'):
   video=s.new_tag('video',attrs={'src':r['path'],'poster':r['poster'],'width':str(r['width']),'height':str(r['height']),'controls':'','muted':'','loop':'','playsinline':'','preload':'none','class':'recipe-animation','aria-label':img.get('alt') or 'Recipe preparation animation'})
   video.string='Your browser cannot play this animation.'
   img.replace_with(video);continue
  if r:
   img['src']=r['path']
   if r.get('width'):
    # Preserve intended rendered dimensions while correcting corrupt ratios.
    w=img.get('width');h=img.get('height')
    if not w or not str(w).isdigit():w=r['width']
    w=min(int(w),r['width']);img['width']=str(w);img['height']=str(round(w*r['height']/r['width']))
  elif src.startswith(('http:','https:','//')):missing.add(src)
  parts=[]
  for item in img.get('srcset','').split(','):
   bits=item.strip().split()
   if not bits:continue
   k=asset_key(bits[0]);rec=MEDIA.get(k)
   if rec:
    descriptor=bits[1] if len(bits)>1 else ''
    if descriptor.endswith('w') and rec.get('width'):descriptor=str(rec['width'])+'w'
    parts.append(rec['path']+' '+descriptor)
  if parts:img['srcset']=', '.join(dict.fromkeys(parts));img['sizes']=img.get('sizes','(max-width: 921px) 100vw, 780px').replace('auto, ','')
  else:img.attrs.pop('srcset',None)
  img['alt']=img.get('alt','')
  if not img['alt'] and ('logo' in src):img['alt']='The Healthy Malteser'
  if not img['alt'] and 'Me-about' in src:img['alt']='Geraldine, creator of The Healthy Malteser'
  img['decoding']='async';img['loading']='lazy';img.attrs.pop('fetchpriority',None)
  if 'custom-logo' in img.get('class',[]):img['loading']='eager'
 for iframe in s.select('iframe'):
  src=iframe.get('src','');m=re.search(r'(?:youtube(?:-nocookie)?\.com/embed/|youtu\.be/)([A-Za-z0-9_-]+)',src)
  if not m:
   iframe.decompose();continue
  title=iframe.get('title','Recipe video');button=s.new_tag('button',attrs={'type':'button','class':'video-placeholder','data-video-id':m.group(1),'data-title':title,'aria-label':'Play '+title})
  if poster:
   img=s.new_tag('img',src=poster,alt='',loading='lazy',width='780',height='439');button.append(img)
  for cls,text in [('video-play','▶'),('video-label',title),('video-disclosure','Play video · loads YouTube on request')]:
   span=s.new_tag('span',attrs={'class':cls});span.string=text
   if cls=='video-play':span['aria-hidden']='true'
   button.append(span)
  iframe.replace_with(button)
 for el in s.select('blockquote.instagram-media'):
  url=el.get('data-instgrm-permalink','');link=el.select_one('a[href]')
  if not url and link:url=link['href']
  if not url:el.decompose();continue
  card=s.new_tag('div',attrs={'class':'instagram-card'});label=s.new_tag('p');label.string='@thehealthymalteser';card.append(label)
  button=s.new_tag('button',attrs={'type':'button','data-instagram-url':url,'class':'instagram-load'});button.string='Load Instagram post';card.append(button)
  a=s.new_tag('a',href=url,target='_blank',rel='noopener noreferrer');a.string='View this post on Instagram';card.append(a);el.replace_with(card)
 for a in s.select('[data-media]'):a['data-media']=local(a['data-media'],absolute=True)
 for el in s.select('[style]'):el['style']=css_urls(el['style'])
 for st in s.select('style'):st.decompose()
 for el in s.find_all(True):
  for k in list(el.attrs):
   if k.lower().startswith('on') or k in ['data-elementor-setting-key','data-pen-placeholder']:del el[k]
 # Menu links must have discernible labels even on the formerly blank sample page.
 for a in s.select('nav a'):
  if not a.get_text(strip=True) and not a.get('aria-label'):a.string='About Me'
 return s

def schema_local(value):
 if isinstance(value,list):return [schema_local(v) for v in value]
 if isinstance(value,dict):return {k:schema_local(v) for k,v in value.items() if k!='potentialAction'}
 if isinstance(value,str):
  value=value.replace('http://thehealthymalteser.com','https://thehealthymalteser.com')
  return local(value,absolute=True)
 return value
home=BeautifulSoup((SOURCE/'home.html').read_text(),'html.parser')
header=clean_fragment(home.select_one('#masthead'),'/');footer=clean_fragment(home.footer,'/')
# Keep a single consistent primary navigation on desktop and mobile.
desktop=header.select_one('#ast-hf-menu-1')
mobile=header.select_one('#ast-hf-mobile-menu > ul')
if mobile and desktop:
 mobile.clear()
 for li in desktop.find_all('li',recursive=False):
  clone=copy.copy(li);clone.attrs.pop('id',None);clone['class']=['menu-item'];mobile.append(clone)
for a in header.select('[aria-current]'):del a['aria-current']
for li in header.select('li'):li['class']=[c for c in li.get('class',[]) if c not in ['current-menu-item','current_page_item']]
(DEST/'header.html').write_text(str(header));(DEST/'footer.html').write_text(str(footer))
for path,file in SOURCES.items():
 if path=='/author/geraldine/':continue
 s=BeautifulSoup((SOURCE/file).read_text(),'html.parser')
 title=s.title.get_text(strip=True)
 if path=='/sample-page/':title='About Me - The Healthy Malteser'
 pagination=re.search(r'/page/(\d+)/$',path)
 if pagination and 'Page '+pagination.group(1) not in title:title+=' — Page '+pagination.group(1)
 desc=s.select_one('meta[name=description]');description=desc.get('content','') if desc else ''
 if not description:
  paragraph=s.select_one('#content .entry-content p')
  text=paragraph.get_text(' ',strip=True) if paragraph else f'Explore {title.split(" - The Healthy")[0]} on The Healthy Malteser: healthy, plant-based Maltese recipes and guilt-free treats.'
  description=text[:157].rsplit(' ',1)[0]+'…' if len(text)>160 else text
 image=s.select_one('meta[property="og:image"]');image=local(image['content']) if image else None
 raw_content=s.select_one('#content')
 if not raw_content:raise RuntimeError('Missing content: '+path)
 content=clean_fragment(raw_content,path,image)
 if not content.select_one('h1'):
  main=content.select_one('main')
  if main:
   h=content.new_tag('h1',attrs={'class':'screen-reader-text'});h.string=title.split(' - The Healthy')[0];main.insert(0,h)
 # Load the first article's visual promptly, while leaving below-fold photos lazy.
 first=content.select_one('.post-thumb img') or content.select_one('#primary img')
 if first and path!='/':first['loading']='eager';first['fetchpriority']='high'
 styles=[]
 for el in s.head.select('link[rel=stylesheet], style'):
  if el.name=='link':
   key=asset_key(el.get('href',''))
   if key in CSS:styles.append(CSS[key])
  elif el.get('id')!='wp-emoji-styles-inline-css':styles.append(style_file(el.get_text()))
 for el in s.body.select('style'):styles.append(style_file(el.get_text()))
 schemas=[]
 for el in s.select('script[type="application/ld+json"]'):
  try:schemas.append(schema_local(json.loads(el.string or el.text)))
  except json.JSONDecodeError:raise RuntimeError('Invalid JSON-LD '+path)
 robots=s.select_one('meta[name=robots]');noindex=bool(robots and 'noindex' in robots.get('content',''))
 slug='index' if path=='/' else path.strip('/').replace('/','__')
 htmlfile='pages/'+slug+'.html';(DEST/htmlfile).write_text(str(content))
 item=by_path.get(path,{})
 routes.append({'path':path,'file':htmlfile,'kind':item.get('type','archive'),'sourceId':item.get('id'),'title':title,'description':description,'image':image,'noindex':noindex,'styles':list(dict.fromkeys(styles)),'bodyClass':' '.join(s.body.get('class',[])),'schemas':schemas,'modified':item.get('modified_gmt')})
 # Offline original for visual comparison: only downloaded assets and original CSS.
 ref=BeautifulSoup(str(s),'html.parser')
 for st in ref.select('script'):st.decompose()
 for l in ref.select('link[rel=stylesheet]'):
  key=asset_key(l.get('href',''))
  if key in CSS:l['href']=CSS[key]
  else:l.decompose()
 for st in ref.select('style'):st.string=css_urls(st.get_text())
 for img in ref.select('img'):
  img['src']=local(img.get('src',''));img.attrs.pop('srcset',None)
  if 's.w.org/' in img.get('src',''):img.replace_with(img.get('alt',''))
 for el in ref.select('[style]'):el['style']=css_urls(el['style'])
 for iframe in ref.select('iframe'):iframe.decompose()
 # Original PT Sans font is mirrored; undeclared Lato/Great Vibes remain as on source.
 font=ref.new_tag('style');font.string="@font-face{font-family:'PT Sans';src:url('/fonts/pt-sans-latin-400-normal.woff2')}";ref.head.append(font)
 dest=reference/('index.html' if path=='/' else path.strip('/')+'/index.html');dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(str(ref))
for path,source in print_routes.items():
 parent=next(r for r in routes if r['path']==source)
 soup=BeautifulSoup((DEST/parent['file']).read_text(),'html.parser');recipe=soup.select_one('.wprm-recipe-container')
 if not recipe:raise RuntimeError('No print recipe '+path)
 heading=recipe.select_one('.wprm-recipe-name')
 if heading:heading.name='h1'
 slug=path.strip('/').replace('/','__');file='pages/'+slug+'.html'
 (DEST/file).write_text('<main id="main" class="print-page"><div class="print-toolbar"><a href="'+source+'">← Back to recipe</a><button type="button" data-print>Print recipe</button></div>'+str(recipe)+'</main>')
 routes.append({'path':path,'file':file,'kind':'print','title':'Print recipe | '+parent['title'],'description':parent['description'],'image':parent['image'],'noindex':True,'styles':parent['styles'],'bodyClass':'print-view','schemas':[]})
(DEST/'routes.json').write_text(json.dumps(routes,ensure_ascii=False,indent=2))
recipes=[x['recipe'] for x in json.loads((SOURCE/'recipes-data.json').read_text())]
(DEST/'recipes.json').write_text(json.dumps(schema_local(recipes),ensure_ascii=False,indent=2))
# Keep the actual original publication IDs and exact URL membership reviewable.
inventory={'source':'https://thehealthymalteser.com','posts':len(posts),'pages':len(pages),'recipes':len(recipes),'routes':len(routes),'assets':len(MEDIA),'missingRemoteImages':sorted(missing),'content':[{'id':x['id'],'type':x['type'],'path':urlparse(x['link']).path,'title':html.unescape(x['title']['rendered'])} for x in posts+pages],'paths':[r['path'] for r in routes]}
(ROOT/'docs/content-inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2))
# Permanent legacy media and WordPress ID redirects. No changed content slugs.
redirects=[{'source':'/home/','destination':'/','statusCode':301},{'source':'/author/geraldine/','destination':'/mystory/','statusCode':301}]
for x in posts+pages:
 param='p' if x['type']=='post' else 'page_id';redirects.append({'source':'/','has':[{'type':'query','key':param,'value':str(x['id'])}],'destination':urlparse(x['link']).path,'statusCode':301})
for path in ['/sitemap_index.xml','/post-sitemap.xml','/page-sitemap.xml','/category-sitemap.xml','/post_tag-sitemap.xml','/wp-sitemap.xml']:
 redirects.append({'source':path,'destination':'/sitemap.xml','statusCode':301})
for u,data in MEDIA.items():redirects.append({'source':unquote(urlparse(u).path),'destination':data['path'],'statusCode':301})
config={'$schema':'https://openapi.vercel.sh/vercel.json','framework':'astro','buildCommand':'npm run build','outputDirectory':'dist','cleanUrls':False,'trailingSlash':True,'redirects':redirects,'headers':[{'source':'/_astro/(.*)','headers':[{'key':'Cache-Control','value':'public, max-age=31536000, immutable'}]},{'source':'/media/(.*)','headers':[{'key':'Cache-Control','value':'public, max-age=31536000, immutable'}]},{'source':'/fonts/(.*)','headers':[{'key':'Cache-Control','value':'public, max-age=31536000, immutable'}]},{'source':'/styles/site-:hash.css','headers':[{'key':'Cache-Control','value':'public, max-age=31536000, immutable'}]},{'source':'/styles/page-:hash.css','headers':[{'key':'Cache-Control','value':'public, max-age=31536000, immutable'}]},{'source':'/(.*)','headers':[{'key':'X-Content-Type-Options','value':'nosniff'},{'key':'Referrer-Policy','value':'strict-origin-when-cross-origin'}]}]}
(ROOT/'vercel.json').write_text(json.dumps(config,indent=2))
print('Imported',len(posts),'posts,',len(pages),'pages,',len(routes),'routes including',len(print_routes),'print pages; missing images:',sorted(missing))
