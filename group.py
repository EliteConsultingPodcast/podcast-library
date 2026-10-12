import re, html, xml.etree.ElementTree as ET, unicodedata
NS={'itunes':'http://www.itunes.com/dtds/podcast-1.0.dtd'}
PREFIX=r'^(ATKINSON|O\.S\.\s?MARDEN|GODDARD|NAPOLEON HILL|EMERSON|P\.T\.\s?BARNUM|ROTHSCHILDS|HENRY FORD|JOHN D\. ROCKEFELLER|ANDREW CARNEGIE|SCHOPENHAUER|RENE DESCARTES|C\.G\.JUNG|HUGH HEFNER|SIGMUND FREUD|Neville Goddard)\s*[-–—]\s*'
ALIAS={ # normalized key -> canonical key
 'SECRET TEACHING':'ARCANE TEACHING','DESIRE POWER YOUR ENERGIZING FORCES':'DESIRE POWER',
 'LAW OF ATTRACTION IN THOUGHT WORLD':'LAW OF ATTRACTION','AS A MAN THINKETH JAMES ALLEN 1902 HQ FULL BOOK LAW OF ATTRACTION':'AS A MAN THINKETH',
 'THE MASTERY OF DESTINY JAMES ALLEN 1909 HQ FULL BOOK':'THE MASTERY OF DESTINY','SECRET DOCTRINE OF ROSICRUCIANS':'SECRET DOCTRINE OF ROSICRUCIANS',
 'VIRTUE HAPPINESS GOOD LIFE':'ARISTOTLES NICOMACHEAN ETHICS','AT YOUR COMMAND 1939 HIGH QUALITY FULL BOOK NEW THOUGHT':'AT YOUR COMMAND',
 'THE SOULS SINCERE DESIRE GLENN CLARK 1925 HQ FULL BOOK':'THE SOULS SINCERE DESIRE','NAPOLEON HILL GOLDEN RULES':'GOLDEN RULES',
 'THE GOD IN YOU':None, # handled by author
}
def norm(s):
    s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode()
    return re.sub(r'\s+',' ',re.sub(r'[^A-Za-z0-9 ]',' ',s)).strip().upper()
def bookkey(t):
    t=re.sub(PREFIX,'',t,flags=re.I)
    if re.search(r'morals\s*&\s*dogma',t,re.I): return 'MORALS AND DOGMA'
    head=re.split(r':| [-–—] ',t)[0]
    head=re.sub(r'\s+\d+$','',head.strip())
    k=norm(head); k=re.sub(r'^THE ','',k)
    k={'SECRET TEACHING':'ARCANE TEACHING','DESIRE POWER YOUR ENERGIZING FORCES':'DESIRE POWER','LAW OF ATTRACTION IN THOUGHT WORLD':'LAW OF ATTRACTION',
       'VIRTUE HAPPINESS GOOD LIFE':'ARISTOTLE S NICOMACHEAN ETHICS','ARISTOTLES NICOMACHEAN ETHICS':'ARISTOTLE S NICOMACHEAN ETHICS',
       'NAPOLEON HILL GOLDEN RULES':'GOLDEN RULES','DYNAMIC THOUGHT OR LAW OF VIBRANT ENERGY':'DYNAMIC THOUGHT ATKINSON',
       'NEW PSYCHOLOGY':None}.get(k,k) or k
    if k=='GOD IN YOU' and 'Mulford' in t: k='GOD IN YOU MULFORD'
    if k=='NEW PSYCHOLOGY': k+=' HAANEL' if 'Haanel' in t else ' ATKINSON'
    if k=='CONQUEST OF FEAR': k+=' '+('MARDEN' if 'Marden' in t else 'SIVANANDA' if 'Sivananda' in t else 'KING')
    if k=='DYNAMIC THOUGHT' : k+=' HAMBLIN'
    if k=='CREATIVE MIND SUCCESS': k='CREATIVE MIND AND SUCCESS'
    return k
def load(path='feed.xml'):
    r=ET.parse(path).getroot(); eps=[]
    for i in r.findall('.//item'):
        g=i.findtext('guid'); eid=g.rsplit('/',1)[1]
        d=i.findtext('description') or ''
        im=i.find('itunes:image',NS)
        eps.append(dict(id=eid,guid=g,title=html.unescape(i.findtext('title')).strip(),desc=d,link=i.findtext('link'),
            date=i.findtext('pubDate'),dur=i.findtext('itunes:duration',namespaces=NS),img=im.get('href') if im is not None else None,key=bookkey(html.unescape(i.findtext('title')))))
    return eps
if __name__=='__main__':
    from collections import OrderedDict
    g=OrderedDict()
    for e in load(): g.setdefault(e['key'],[]).append(e['title'])
    print(len(g))
    for k,v in g.items(): print(k,'=>',len(v),'|',v[0][:90])
