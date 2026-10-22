import json,os,re,functools
from urllib.parse import urlencode
from pathlib import Path
CATALOG=Path(os.getenv('VIDEO_CATALOG','/data/teaching_videos.json'))
URL=re.compile(r'^https://www\.bilibili\.com/video/BV[A-Za-z0-9]{10}/(?:\?p=[1-9]\d*)?$')
def normalize(s):return re.sub(r'[\s，。、：:（）()·-]','',s).lower().replace('的','')
def recommend(subject,grade,knowledge):
 topic=re.sub(r'[<>\r\n]',' ',knowledge).strip()[:80]
 clean=normalize(topic)
 candidates=[]
 try: rows=json.loads(CATALOG.read_text())
 except (OSError,ValueError): rows=[]
 # Determine specificity before grade filtering, so a younger pupil's fraction
 # question does not silently receive an unrelated basic integer-addition video.
 strongest=max((len(normalize(a)) for x in rows if x.get('subject')==subject and URL.fullmatch(x.get('url','')) for a in x.get('aliases',[]) if normalize(a) and normalize(a) in clean),default=0)
 for x in rows:
  if x.get('subject')!=subject or x.get('grade_min',1)>grade or not URL.fullmatch(x.get('url','')):continue
  aliases=[a for a in x.get('aliases',[]) if normalize(a) and normalize(a) in clean]
  if not aliases:continue
  longest=max(aliases,key=lambda a:len(normalize(a)))
  strength=len(normalize(longest))
  if strength<2 or strength<strongest-1:continue
  age=2 if x.get('grade_min',1)<=grade<=x.get('grade_max',6) else 0
  candidates.append((strength,age,x,longest))
 candidates.sort(key=lambda a:(a[0],a[1]),reverse=True)
 selected=[];seen=set()
 for strength,age,x,tag in candidates:
  if strength < (candidates[0][0] if candidates else 0)-1:continue
  if x['url'] in seen:continue
  seen.add(x['url']);selected.append({k:x.get(k,'') for k in ('title','url','author','duration','source')} | {'reason':'相关知识点：'+tag,'match_type':'同知识点讲解'})
  if len(selected)==3:break
 keyword=f'小学{grade}年级 {subject} {topic[:40]} 讲解'.strip()
 return {'videos':selected,'search_url':'https://search.bilibili.com/video?'+urlencode({'keyword':keyword}),'keyword':keyword,'notice':'推荐同知识点讲解，并非这道题的逐题答案。'}
