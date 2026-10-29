#!/usr/bin/env python3
"""Generates the Elite Consulting podcast library (static site) from the Spreaker RSS feed.
Usage: python3 generate.py   (downloads feed + Apple lookup, writes ./docs)"""
import os, re, json, html, shutil, urllib.request, datetime, email.utils
from collections import OrderedDict
from group import load, bookkey
from summaries import S
HERE=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.join(HERE,'docs')
FEED='https://www.spreaker.com/show/5835231/episodes/feed'
SITE='https://podcast.eliteconsult.eu'
SHOW='SECRETS OF SUCCESS & WEALTH: Hidden Laws of Money, Power & Success'
APPLE='https://podcasts.apple.com/ca/podcast/secrets-of-success-wealth-hidden-laws-of-money/id1797271143'
SPOTIFY='https://open.spotify.com/show/2NNblMHxoxCLs9TtRtr12T'
SPREAKER='https://www.spreaker.com/organization/elite-consulting--12099961'
LOGO=os.environ.get('LOGO','/workspace/branding/original_motto_1024.jpg')
AUTHORS=['William Walker Atkinson','Orison Swett Marden','Napoleon Hill','Neville Goddard','Albert Pike','Arthur Schopenhauer','Manly P. Hall','Ernest S. Holmes','Robert Collier','Prentice Mulford','James Allen','Wallace D. Wattles','Charles F. Haanel','Florence Scovel Shinn','Joseph Murphy','Ralph Waldo Emerson','Henry Ford','Andrew Carnegie','John D. Rockefeller','P. T. Barnum','Egon Caesar Corti','Max Heindel','Arthur Edward Waite','Sigmund Freud','Hugh Hefner','Edward E. Beals','Frank Channing Haddock','René Descartes','Marcus Aurelius','Edward L. Bernays','John Reeves','William George Jordan','Richard A. Werner','Emile Coué','George S. Clason','W. L. Wilmshurst','Swami Sivananda','Florence Scovel Shinn','Henry Thomas Hamblin','Claude M. Bristol','Thomas Troward','Basil King','J. D. Buck','Genevieve Behrend','Glenn Clark','Aristotle','John McDonald','C. G. Jung','Napoleon Bonaparte','Carl von Clausewitz','Abraham Lincoln','Sun Tzu','Niccolò Machiavelli','Carl Jung']
ALIASES={'Marden':'Orison Swett Marden','Atkinson':'William Walker Atkinson','Goddard':'Neville Goddard','Schopenhauer':'Arthur Schopenhauer','Haanel':'Charles F. Haanel','Bristol':'Claude M. Bristol','Coué':'Emile Coué','Corti':'Egon Caesar Corti','Conti':'Egon Caesar Corti','Barnum':'P. T. Barnum','Machiavelli':'Niccolò Machiavelli','Jung':'C. G. Jung','Kybalion':'Three Initiates','J.P. MORGAN':'Carl Hovey','Rockefeller':'John D. Rockefeller','Carnegie':'Andrew Carnegie','Murphy':'Joseph Murphy','Wilmshurst':'W. L. Wilmshurst','WILMSHURST':'W. L. Wilmshurst','Clausewitz':'Carl von Clausewitz','Descartes':'René Descartes','Aristotle':'Aristotle','Lincoln':'Abraham Lincoln','Napoleon Bonaparte':'Napoleon Bonaparte','NAPOLEON BONAPARTE':'Napoleon Bonaparte','Ford':'Henry Ford','Emerson':'Ralph Waldo Emerson','Collier':'Robert Collier','Hill':'Napoleon Hill','Freud':'Sigmund Freud','Hefner':'Hugh Hefner','Heindel':'Max Heindel','Holmes':'Ernest S. Holmes','Hall':'Manly P. Hall','SUN TZU':'Sun Tzu','MARCUS AURELIUS':'Marcus Aurelius'}
KEY_AUTHOR={'J P MORGAN':'J. P. Morgan','KYBALION':'Three Initiates','FINANCIAL RULERS OF NATIONS':'John Reeves','LIFE OF P T BARNUM':'Joel Benton','INCREDIBLE SUCCESS':'Andrew Carnegie','ALCHEMY OF SUCCESS':'John D. Rockefeller','JOHN D ROCKEFELLER':'John D. Rockefeller','STORY OF SUCCESS':'Henry Ford','HOW THEY SUCCEEDED':'Orison Swett Marden','SUCCESS SECRETS OF GREAT AMERICANS':'Orison Swett Marden','NAPOLEON BONAPARTE MEMOIRS':'Napoleon Bonaparte','MASTERY OF BEING':'William Walker Atkinson'}
def author_of(key,title,desc):
    if key in KEY_AUTHOR: return KEY_AUTHOR[key]
    if title.upper().startswith('NAPOLEON HILL'): return 'Napoleon Hill'
    for a in sorted(AUTHORS,key=len,reverse=True):
        if a.lower() in title.lower(): return a
    for k,v in ALIASES.items():
        if re.search(r'\b'+re.escape(k)+r'\b',title): return v
    plain=re.sub('<[^>]+>',' ',desc)
    for a in sorted(AUTHORS,key=len,reverse=True):
        if a.lower() in plain.lower(): return a
    return 'Various'
PREFIX=re.compile(r'^(ATKINSON|O\.S\.\s?MARDEN|GODDARD|NAPOLEON HILL|EMERSON|P\.T\.\s?BARNUM|ROTHSCHILDS|HENRY FORD|JOHN D\. ROCKEFELLER|ANDREW CARNEGIE|SCHOPENHAUER|RENE DESCARTES|C\.G\.JUNG|HUGH HEFNER|SIGMUND FREUD|Neville Goddard)\s*[-–—]\s*',re.I)
SMALL={'a','an','and','as','at','by','for','in','of','on','or','the','to','vs','is'}
def tcase(s):
    w=s.lower().split(); o=[]
    for i,x in enumerate(w):
        o.append(x if (i and x in SMALL) else (x[:1].upper()+x[1:]))
    s=' '.join(o)
    return re.sub(r"\b(Ii|Iii|Iv|Vi)\b",lambda m:m.group(0).upper(),s).replace("P. t.","P. T.").replace("J.p.","J.P.")
def book_title(key,t):
    if key=='MORALS AND DOGMA': return 'Morals and Dogma of Freemasonry'
    t=PREFIX.sub('',t)
    if key=='SUN TZU': return 'The Art of War'
    h=re.split(r':| [-–—] ',t)[0].strip()
    h=re.sub(r'\s+\d+$','',h); h=re.sub(r'\s*\(\d{4}\)$','',h)
    h={'SECRET TEACHING':'Arcane Teaching','ATKINSON - ARCANE TEACHING':'Arcane Teaching'}.get(h,h)
    if key=='ARCANE TEACHING': h='Arcane Teaching'
    if key=='DESIRE POWER': h='Desire Power'
    if key=='LAW OF ATTRACTION': h='Thought Vibration or the Law of Attraction in the Thought World'
    if key=='ARISTOTLE S NICOMACHEAN ETHICS': h="Aristotle's Nicomachean Ethics"
    if key=='JOHN D ROCKEFELLER': h='The Life of John D. Rockefeller'
    h={'METHAPHYSICAL MEDITATIONS':'Meditations on First Philosophy','CLAUSEWITZ’S ON WAR':'On War','J.P. MORGAN':'J. P. Morgan: Master of Money'}.get(h,h)
    h=re.sub(r'- Glenn Clark.*','',h)
    if key=='GOLDEN RULES': h='The Golden Rules'
    return tcase(h).replace("'S ","'s ").replace("’S ","’s ")
def slugify(s):
    s=html.unescape(s); import unicodedata
    s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()
    return re.sub(r'-+','-',re.sub(r'[^a-z0-9]+','-',s)).strip('-')[:70].strip('-')
CH=re.compile(r'\((\d{2}:\d{2}:\d{2})\)\s*([^<]+)')
def chapters(desc): return [(a,html.unescape(b).strip()) for a,b in CH.findall(desc)]
def about(desc,maxp=5):
    d=re.sub(r'\(\d{2}:\d{2}:\d{2}\)[^<]*<br\s*/?>','',desc)
    d=re.split(r'Become a supporter',d)[0]
    paras=[re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]+>','',p))).strip() for p in re.split(r'(?:<br\s*/?>\s*){2,}',d)]
    paras=[p for p in paras if len(p)>60 and not p.startswith('#') and 'http' not in p]
    return paras[:maxp]
HEAD_RE=re.compile(r"^(?:(?:LESSON|PART|CHAPTER|KAPITEL|TEIL|BOOK|SECTION)\b.*|[IVXLC]+\.\s.{1,90}|\d{1,3}[.)]\s.{1,90}|(?=[^a-z]*[A-Z]{3})[^a-z]{4,120})$")
INLINE_HEAD=re.compile(r"(?<=[a-z.!?:;)\"”])\s*(?=(?:LESSON|PART|CHAPTER|KAPITEL)\s+[IVXLC\d]+\b)")
def fmt_desc(desc):
    d=re.sub(r'^\s*<!\[CDATA\[|\]\]>\s*$','',desc.strip())
    d=re.split(r'Become a supporter',d)[0]
    d=re.sub(r'\(\d{2}:\d{2}:\d{2}\)[^<\n]*(?:<br\s*/?>)?','',d)
    d=re.sub(r'(?i)</?(?:p|div|li|h\d)[^>]*>|<br\s*/?>','\n',d)
    bold=set(html.unescape(re.sub(r'\s+',' ',re.sub('<[^>]+>','',b))).strip() for b in re.findall(r'(?is)<(?:b|strong)>(.*?)</(?:b|strong)>',d))
    d=html.unescape(re.sub('<[^>]+>','',d))
    d=INLINE_HEAD.sub('\n',d)
    d=re.sub(r'(?<=[a-z][.!?])(?=[A-Z][a-z])',' ',d)
    out=[]
    for ln in d.split('\n'):
        ln=re.sub(r'\s+',' ',ln).strip()
        if not ln or 'http' in ln: continue
        if ln in bold: out.append(f'<p class="dh"><strong>{E(ln)}</strong></p>')
        elif HEAD_RE.match(ln) and len(ln)<=120: out.append(f'<h4>{E(ln)}</h4>')
        else: out.append(f'<p>{E(ln)}</p>')
    return ''.join(out)
def secs(t):
    h,m,s=map(int,t.split(':')); return h*3600+m*60+s
def hms(d):
    try: d=int(d)
    except: return ''
    h,m=d//3600,(d%3600)//60; return f'{h} h {m} min' if h else f'{m} min'
def iso_dur(d):
    try: d=int(d); return f'PT{d//3600}H{(d%3600)//60}M{d%60}S'
    except: return None
E=html.escape
def fetch(url,dst):
    try:
        req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
        open(dst,'wb').write(urllib.request.urlopen(req,timeout=60).read())
    except Exception as ex: print('fetch failed, using cached',dst,ex)
CSS='''*{box-sizing:border-box}body{margin:0;font-family:Georgia,'Times New Roman',serif;background:#faf6ee;color:#2a1a1a;line-height:1.65}
a{color:#4A0A10}h1,h2,h3,.brand{font-family:'Cinzel',Georgia,serif;letter-spacing:.03em}
header.top{background:#4A0A10;color:#D4A24C;padding:.6rem 1rem;display:flex;align-items:center;gap:.8rem;border-bottom:2px solid #D4A24C}
header.top a{color:#D4A24C;text-decoration:none}header.top img{width:40px;height:40px;border-radius:50%}
.brand{font-size:1rem}.wrap{max-width:1080px;margin:0 auto;padding:1.2rem}
.hero{background:radial-gradient(circle at 50% 30%,#6b141c,#4A0A10 70%);color:#f3e6cc;text-align:center;padding:2.5rem 1rem 2rem;border-bottom:3px solid #D4A24C}
.hero img{width:200px;height:200px;border-radius:50%;border:3px solid #D4A24C;box-shadow:0 6px 30px rgba(0,0,0,.4)}
.hero h1{color:#D4A24C;font-size:clamp(1.4rem,4vw,2.3rem);margin:.8rem 0 .3rem}.hero p{max-width:720px;margin:.6rem auto}
.btns{display:flex;flex-wrap:wrap;gap:.6rem;justify-content:center;margin:1.2rem 0}
.btn{display:inline-block;padding:.6rem 1.2rem;border:2px solid #D4A24C;border-radius:30px;color:#D4A24C;text-decoration:none;font-family:'Cinzel',serif;font-size:.9rem;background:rgba(0,0,0,.15)}
.btn:hover,.btn.solid{background:#D4A24C;color:#4A0A10}
.light .btn{color:#4A0A10;border-color:#4A0A10;background:none}.light .btn:hover{background:#4A0A10;color:#D4A24C}
h2.author{color:#4A0A10;border-bottom:1px solid #D4A24C;padding-bottom:.3rem;margin-top:2.2rem}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:1rem}
.card{background:#fff;border:1px solid #e6d6b4;border-radius:10px;padding:1rem;text-decoration:none;color:inherit;display:flex;gap:.8rem;align-items:center;transition:.15s}
.card:hover{border-color:#D4A24C;box-shadow:0 4px 14px rgba(74,10,16,.12)}.card img{width:64px;height:64px;border-radius:6px;flex:none}
.card b{font-family:'Cinzel',serif;color:#4A0A10;font-size:.92rem;display:block}.card span{font-size:.8rem;color:#7a5a3a}
.toc{columns:2 220px;font-size:.92rem}.toc a{text-decoration:none}
article h1{color:#4A0A10;font-size:clamp(1.4rem,4vw,2.2rem);margin:.2rem 0}.by{color:#8a6a3a;font-style:italic;margin:0 0 1rem}
.cover{float:right;width:180px;margin:0 0 1rem 1rem;border-radius:8px;border:2px solid #D4A24C}
.ideas li{margin:.3rem 0}.part{background:#fff;border:1px solid #e6d6b4;border-radius:10px;padding:1rem;margin:1.2rem 0}
.part h3{margin-top:0;color:#4A0A10;font-size:1rem}ol.ch{list-style:none;padding-left:0;font-size:.92rem}ol.ch li{margin:.15rem 0}ol.ch time{color:#8a6a3a;font-family:monospace;margin-right:.4rem}
iframe{width:100%;height:200px;border:0;border-radius:8px}.crumb{font-size:.85rem}
footer{background:#4A0A10;color:#D4A24C;text-align:center;padding:1.5rem;margin-top:3rem;font-size:.85rem}footer a{color:#D4A24C}
.desc{margin-top:1rem;font-size:.95rem}.desc summary{font-family:'Cinzel',serif;color:#4A0A10;cursor:pointer;font-weight:700}.desc h4{font-family:'Cinzel',serif;color:#4A0A10;margin:1.1rem 0 .3rem;font-size:.95rem}.desc p{margin:.5rem 0}.desc p.dh{margin-top:.8rem}
@media(max-width:600px){.cover{float:none;display:block;margin:0 auto 1rem;width:60%}}'''
def page(title,desc,path,body,img,jsonld,extra_head=''):
    url=SITE+path
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title><meta name="description" content="{E(desc)}"><link rel="canonical" href="{url}">
<meta property="og:type" content="website"><meta property="og:title" content="{E(title)}"><meta property="og:description" content="{E(desc)}"><meta property="og:url" content="{url}"><meta property="og:image" content="{E(img)}"><meta property="og:site_name" content="Elite Consulting Podcast Library">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{E(title)}"><meta name="twitter:description" content="{E(desc)}"><meta name="twitter:image" content="{E(img)}">
<link rel="icon" href="/assets/logo-192.jpg"><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@500;700&display=swap" rel="stylesheet"><link rel="stylesheet" href="/assets/style.css">
<script type="application/ld+json">{json.dumps(jsonld,ensure_ascii=False)}</script>{extra_head}</head><body>
<header class="top"><a href="/"><img src="/assets/logo-192.jpg" alt="Elite Consulting logo" width="40" height="40"></a><a class="brand" href="/">Elite Consulting · Podcast Library</a></header>
{body}
<footer><p>© {datetime.date.today().year} Elite Consulting · <a href="{APPLE}">Apple Podcasts</a> · <a href="{SPOTIFY}">Spotify</a> · <a href="{SPREAKER}">Spreaker</a> · <a href="https://www.eliteconsult.eu">eliteconsult.eu</a></p><p>Full readings of public-domain classics on success, wealth and mindset.</p></footer></body></html>'''
def apple_search(e):
    import urllib.parse
    w=re.sub(r'[^A-Za-z0-9 ]',' ',e['title']).split()
    for term in (' '.join(w[:12]),' '.join(w[:6])):
      try:
        r=json.load(urllib.request.urlopen('https://itunes.apple.com/search?media=podcast&entity=podcastEpisode&limit=50&term='+urllib.parse.quote(term),timeout=30))
        for x in r['results']:
            if x.get('episodeGuid')==e['guid']: return x['trackViewUrl'].split('&uo')[0].split('?uo')[0]
      except Exception as ex: print('apple search failed',ex)
def main():
    os.chdir(HERE)
    fetch(FEED,'feed.xml'); fetch('https://itunes.apple.com/lookup?id=1797271143&entity=podcastEpisode&limit=300','apple.json')
    apple={r.get('episodeGuid'):r['trackViewUrl'].split('&uo')[0].split('?uo')[0] for r in json.load(open('apple.json'))['results'] if r.get('wrapperType')=='podcastEpisode'}
    eps=load('feed.xml'); books=OrderedDict()
    for e in eps: books.setdefault(e['key'],[]).append(e)
    if os.path.exists(OUT): shutil.rmtree(OUT)
    os.makedirs(OUT+'/assets')
    open(OUT+'/assets/style.css','w').write(CSS)
    from PIL import Image
    im=Image.open(LOGO).convert('RGB'); im.resize((512,512)).save(OUT+'/assets/logo-512.jpg',quality=85); im.resize((192,192)).save(OUT+'/assets/logo-192.jpg',quality=85)
    LOGOURL=SITE+'/assets/logo-512.jpg'
    entries=[]; unmatched=[]; used=set()
    for key,lst in books.items():
        lst.sort(key=lambda e:(int(m.group(1)) if (m:=re.search(r'(?:DOGMA OF FREEMASONRY|Freemasonry)\s*[-–]\s*(\d+)',e['title'])) else 0, re.search(r'\d+\.\d',e['title']) and float(re.search(r'(\d+)\.(\d)',e['title']).group(0)) or 0, email.utils.parsedate_to_datetime(e['date'])))
        first=lst[0]; title=book_title(key,first['title']); author=author_of(key,first['title'],first['desc'])
        slug=slugify(title+' '+author.split()[-1]); 
        while slug in used: slug+='-2'
        used.add(slug)
        img=first['img'] or LOGOURL
        summ=S.get(key)
        intro=summ[0][0] if summ else (about(first['desc'],1) or [title])[0]
        mdesc=(f'Listen free to the full audiobook reading of {title} by {author}. '+intro)[:300].rsplit(' ',1)[0]+'…'
        parts=[]; ld_eps=[]
        for i,e in enumerate(lst):
            am=apple.get(e['guid']) or apple_search(e)
            if not am: unmatched.append(e['title'])
            chs=chapters(e['desc'])
            ch_html=''.join(f'<li><time>{a}</time>{E(b)}</li>' for a,b in chs)
            pl=f'<iframe loading="lazy" title="{E(e["title"])}" src="https://widget.spreaker.com/player?episode_id={e["id"]}&amp;theme=dark" allow="autoplay"></iframe>'
            links=f'<div class="btns light" style="justify-content:flex-start">{f"<a class=btn href={E(am)!r}>Apple Podcasts</a>" if am else f"<a class=btn href={APPLE!r}>Apple Podcasts</a>"}<a class="btn" href="{SPOTIFY}">Spotify</a><a class="btn" href="{E(e["link"] or SPREAKER)}">Spreaker</a></div>'
            parts.append(f'<section class="part" id="part-{i+1}"><h3>{E(e["title"])}</h3><p class="by">{hms(e["dur"])}</p>{pl}{links}'+(f'<h3>Chapters</h3><ol class="ch">{ch_html}</ol>' if chs else '')+(f'<details class="desc" open><summary>Episode description</summary>{dh}</details>' if (dh:=fmt_desc(e['desc'])) else '')+'</section>')
            ld_eps.append({'@type':'PodcastEpisode','name':e['title'],'url':SITE+f'/books/{slug}/#part-{i+1}','datePublished':email.utils.parsedate_to_datetime(e['date']).date().isoformat(),
              'timeRequired':iso_dur(e['dur']),'associatedMedia':{'@type':'MediaObject','embedUrl':f'https://widget.spreaker.com/player?episode_id={e["id"]}'},'partOfSeries':{'@type':'PodcastSeries','name':SHOW,'url':SITE+'/'},'sameAs':[x for x in [am,e['link']] if x]})
        if summ:
            sm='<h2>Summary</h2>'+''.join(f'<p>{E(p)}</p>' for p in summ[0])+'<h2>Key ideas</h2><ul class="ideas">'+''.join(f'<li>{E(x)}</li>' for x in summ[1])+'</ul>'
        else:
            sm=''
        ld={'@context':'https://schema.org','@graph':[{'@type':'Book','name':title,'author':{'@type':'Person','name':author},'inLanguage':'en','image':img,'url':SITE+f'/books/{slug}/','description':mdesc},*ld_eps]}
        body=f'''<main class="wrap"><p class="crumb"><a href="/">Library</a> › <a href="/#{slugify(author)}">{E(author)}</a></p><article>
<img class="cover" src="{E(img.replace('t_rss_itunes_square_1400','t_rss_itunes_square_1400'))}" alt="{E(title)} cover" width="180" height="180" loading="lazy">
<h1>{E(title)}</h1><p class="by">by {E(author)} · {len(lst)} episode{'s' if len(lst)>1 else ''} · full audiobook reading</p>
<div class="btns light" style="justify-content:flex-start"><a class="btn" href="#part-1">▶ Listen now</a></div>
{sm}<h2>Listen{'' if len(lst)==1 else ' – all parts'}</h2>{''.join(parts)}<section id="comments" style="margin-top:2.5em"><h2>Kommentare / Comments</h2><p style="opacity:.8">Fragen oder Gedanken zu diesem Buch? Schreib uns hier (GitHub-Login nötig). · Questions or thoughts? Leave a comment.</p><script src="https://giscus.app/client.js" data-repo="EliteConsultingPodcast/podcast-library" data-repo-id="R_kgDOVF1Ywg" data-category="Announcements" data-category-id="DIC_kwDOVF1Yws4DJ5f_" data-mapping="pathname" data-strict="0" data-reactions-enabled="1" data-emit-metadata="0" data-input-position="top" data-theme="dark" data-lang="de" data-loading="lazy" crossorigin="anonymous" async></script></section></article></main>'''
        os.makedirs(f'{OUT}/books/{slug}')
        open(f'{OUT}/books/{slug}/index.html','w').write(page(f'{title} – {author} | Full Audiobook Podcast',mdesc,f'/books/{slug}/',body,img,ld))
        entries.append(dict(title=title,author=author,slug=slug,img=img,n=len(lst),date=max(email.utils.parsedate_to_datetime(x['date']) for x in lst)))
    # index
    byA=OrderedDict()
    for a in sorted({x['author'] for x in entries},key=lambda a:(-sum(1 for x in entries if x['author']==a),a)): byA[a]=sorted([x for x in entries if x['author']==a],key=lambda x:x['title'])
    nav=''.join(f'<li><a href="#{slugify(a)}">{E(a)}</a> ({len(v)})</li>' for a,v in byA.items())
    grids=''.join(f'<h2 class="author" id="{slugify(a)}">{E(a)}</h2><div class="grid">'+''.join(f'<a class="card" href="/books/{x["slug"]}/"><img src="{E(x["img"].replace("t_rss_itunes_square_1400","t_rss_itunes_square_1400"))}" alt="" width="64" height="64" loading="lazy"><div><b>{E(x["title"])}</b><span>{x["n"]} episode{"s" if x["n"]>1 else ""}</span></div></a>' for x in v)+'</div>' for a,v in byA.items())
    latest=sorted(entries,key=lambda x:x['date'],reverse=True)[:6]
    lat='<h2 class="author">Latest additions</h2><div class="grid">'+''.join(f'<a class="card" href="/books/{x["slug"]}/"><img src="{E(x["img"])}" alt="" width="64" height="64" loading="lazy"><div><b>{E(x["title"])}</b><span>{E(x["author"])}</span></div></a>' for x in latest)+'</div>'
    body=f'''<section class="hero"><img src="/assets/logo-512.jpg" alt="Elite Consulting crest" width="200" height="200"><h1>Secrets of Success &amp; Wealth</h1>
<p><em>Hidden Laws of Money, Power &amp; Success</em></p><p>Complete, unabridged readings of the timeless classics on success, wealth, mindset and power – Napoleon Hill, James Allen, Orison Swett Marden, William Walker Atkinson, Neville Goddard, Carnegie, Ford and many more. {len(entries)} books, {len(eps)} episodes, free to listen.</p>
<div class="btns"><a class="btn solid" href="{APPLE}">Apple Podcasts</a><a class="btn" href="{SPOTIFY}">Spotify</a><a class="btn" href="{SPREAKER}">Spreaker</a></div></section>
<main class="wrap">{lat}<h2 class="author">Authors</h2><ul class="toc">{nav}</ul>{grids}</main>'''
    ld={'@context':'https://schema.org','@type':'PodcastSeries','name':SHOW,'url':SITE+'/','image':LOGOURL,'author':{'@type':'Organization','name':'Elite Consulting','url':'https://www.eliteconsult.eu'},'webFeed':FEED,'sameAs':[APPLE,SPOTIFY,SPREAKER]}
    open(OUT+'/index.html','w').write(page('Secrets of Success & Wealth – Free Full Audiobooks of Success Classics | Elite Consulting','Free full audiobook readings of the great success and wealth classics: Think and Grow Rich, As a Man Thinketh, The Science of Getting Rich and '+str(len(entries))+' more books, with summaries and chapter lists.','/',body,LOGOURL,ld))
    today=datetime.date.today().isoformat()
    sm='<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+f'<url><loc>{SITE}/</loc><lastmod>{today}</lastmod></url>\n'+''.join(f'<url><loc>{SITE}/books/{x["slug"]}/</loc><lastmod>{x["date"].date().isoformat()}</lastmod></url>\n' for x in entries)+'</urlset>\n'
    open(OUT+'/sitemap.xml','w').write(sm)
    open(OUT+'/robots.txt','w').write(f'User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n')
    open(OUT+'/CNAME','w').write('podcast.eliteconsult.eu\n'); open(OUT+'/.nojekyll','w').write('')
    open(OUT+'/404.html','w').write(page('Not found','Page not found','/404.html','<main class="wrap"><h1>Page not found</h1><p><a href="/">Back to the library</a></p></main>',LOGOURL,{}))
    json.dump(dict(books=len(entries),episodes=len(eps),custom_summaries=sum(1 for k in books if S.get(k)),unmatched=unmatched),open(HERE+'/build_report.json','w'),indent=1)
    print(open(HERE+'/build_report.json').read())
if __name__=='__main__': main()
