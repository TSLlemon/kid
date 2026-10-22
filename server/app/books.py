import asyncio,hashlib,json,os,re
from pathlib import Path
from fastapi import HTTPException
ROOT=Path(os.getenv('BOOKS_PATH','/data/books'))
AUDIO=Path('/data/book_audio')
_sem=None
_locks={}
def load_book(book_id):
 if not re.fullmatch(r'[a-z0-9_-]{1,40}',book_id):raise HTTPException(404,'读物不存在')
 p=ROOT/(book_id+'.json')
 try:return json.loads(p.read_text())
 except (OSError,ValueError):raise HTTPException(404,'读物不存在')
def metadata(b):
 return {k:b.get(k,'') for k in ('id','title','author','translator','edition','description','source_url','license','illustrator')} | {'chapter_count':len(b['chapters']),'complete':b.get('complete',False)}
def list_books():
 return [metadata(json.loads(p.read_text())) for p in sorted(ROOT.glob('*.json')) if p.name!='manifest.json'] if ROOT.exists() else []
def chapter(book_id,index):
 b=load_book(book_id)
 if index<0 or index>=len(b['chapters']):raise HTTPException(404,'章节不存在')
 c=b['chapters'][index]
 return {'book':metadata(b),'index':index,'title':c['title'],'paragraphs':c['paragraphs'],'images':c.get('images',[]),'segment_count':len(segments(c['paragraphs']))}
def segments(paragraphs):
 result=[]
 for para in paragraphs:
  # Keep each request comfortably below transport limits; no text is omitted.
  for i in range(0,len(para),500):
   text=para[i:i+500]
   if text.strip():result.append(text)
 return result
async def prepare_audio(book_id,index,segment):
 global _sem
 c=chapter(book_id,index);texts=segments(c['paragraphs'])
 if not 0<=segment<len(texts):raise HTTPException(404,'朗读段落不存在')
 text=texts[segment];key=hashlib.sha256(('zh-CN-XiaoxiaoNeural|-5%|'+text).encode()).hexdigest();p=AUDIO/(key+'.mp3')
 if p.exists():return {'url':'/api/book_audio/'+key+'.mp3','segment':segment,'segment_count':len(texts)}
 import edge_tts
 if _sem is None:_sem=asyncio.Semaphore(3)
 lock=_locks.setdefault(key,asyncio.Lock())
 async with lock:
  if not p.exists():
   async with _sem:
    AUDIO.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.partial')
    try:
     await asyncio.wait_for(edge_tts.Communicate(text,'zh-CN-XiaoxiaoNeural',rate='-5%').save(str(tmp)),timeout=90)
     if tmp.stat().st_size<500:raise ValueError('Empty audio')
     tmp.replace(p)
    except Exception as e:
     tmp.unlink(missing_ok=True)
     raise HTTPException(503,'朗读生成暂时失败，请点击重试') from e
 return {'url':'/api/book_audio/'+key+'.mp3','segment':segment,'segment_count':len(texts)}
