"""Conservative exact sentence cleanup, including joined '.The' model loops.

No paraphrase or semantic/ordinal similarity deletion. Frozen v1 remains intact.
"""
import re

ABBREVIATIONS={'mr','mrs','ms','dr','prof','st','no','vs','etc','jan','feb','mar','apr','jun','jul','aug','sep','sept','oct','nov','dec'}
def sentence_spans(text):
 result=[];start=0;quote=None;i=0
 while i<len(text):
  ch=text[i];apostrophe=ch=="'" and i>0 and i+1<len(text) and text[i-1].isalnum() and text[i+1].isalnum();closed=False
  if ch in ['"',"'"] and not apostrophe:
   if quote==ch:quote=None;closed=True
   elif quote is None:quote=ch
  following=text[i+1:];joined=following.startswith(('The ','A ','An '))
  boundary=quote is None and (ch in '.!?' or closed and i>0 and text[i-1] in '.!?') and (i+1==len(text) or text[i+1].isspace() or joined)
  if boundary and ch=='.':
   prefix=text[start:i+1];word=re.search(r'([A-Za-z]+)\.$',prefix)
   if word and word.group(1).lower() in ABBREVIATIONS or re.search(r'(?:[A-Z]\.){2,}$',prefix):boundary=False
  if boundary:
   part=text[start:i+1].strip()
   if part:result.append(part)
   start=i+1
  i+=1
 tail=text[start:].strip()
 if tail:result.append(tail)
 return result

def deduplicate_caption(caption):
 seen=set();kept=[];removed=0;repeated=[]
 for part in sentence_spans(caption):
  key=re.sub(r'\s+',' ',part).strip();eligible=len(re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?",part))>=3
  if eligible and key in seen:removed+=1;repeated.append(key)
  else:seen.add(key);kept.append(part)
 trimmed=False
 if removed>=2 and kept and kept[-1][-1:] not in '.!?"\'':
  tail=re.sub(r'\s+',' ',kept[-1]).strip()
  if len(tail)<=80 and any(s.startswith(tail) and len(s)>len(tail) for s in repeated):kept.pop();trimmed=True
 result=' '.join(kept) if removed or trimmed else caption
 return result,{'version':2,'removed_exact_sentences':removed,'trimmed_repetition_fragment':trimmed,'changed':result!=caption,'semantic_similarity_used':False}
