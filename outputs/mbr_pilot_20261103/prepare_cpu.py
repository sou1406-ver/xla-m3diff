from pathlib import Path
import json,pickle,hashlib,collections,math,time
from pycocoevalcap.tokenizer.ptbtokenizer import PTBTokenizer
from pycocoevalcap.cider.cider import Cider
from utility import document_frequency,pair_score
P=Path('/mnt/m3diff/mbr_pilot_20261103');P.mkdir(exist_ok=True)
assert not (P/'CPU_READY.json').exists()
t=time.time()
# Independent numeric cross-check against the benchmark scorer, including clipping/length penalty.
docs=[['a red dog sits on the table','a small dog is sitting'],['a blue car moved to the left'],['nothing has changed in the room']]
hyps=['a red dog sits on the table','a blue car moved moved to the left','the room has no change']
cache=document_frequency(docs);g={i:d for i,d in enumerate(docs)};h={i:[s] for i,s in enumerate(hyps)}
_,expected=Cider().compute_score(g,h);actual=[sum(pair_score(hyps[i],r,cache) for r in refs)/len(refs) for i,refs in enumerate(docs)]
assert max(abs(float(a)-float(b)) for a,b in zip(expected,actual))<1e-10,(expected,actual)
groups={}
for line in Path('/root/annotation.jsonl').read_text().splitlines():
 r=json.loads(line)
 if r['split']=='train':groups.setdefault(r['id'],[]).append({'caption':r['caption']})
assert len(groups)==12452
tokenized=PTBTokenizer().tokenize(groups);cache=document_frequency(list(tokenized.values()))
with (P/'train_idf.pkl').open('wb') as f:pickle.dump(cache,f,protocol=4)
for n in ['questions20.json','selection20.json','PROTOCOL.json']: (P/n).write_bytes(Path('/root/'+n).read_bytes())
info={'train_documents':len(groups),'train_reference_captions':sum(len(x) for x in groups.values()),'unique_ngrams':len(cache['df']),'train_idf_sha256':hashlib.sha256((P/'train_idf.pkl').read_bytes()).hexdigest(),'source_annotation_sha256':hashlib.sha256(Path('/root/annotation.jsonl').read_bytes()).hexdigest(),'tokenizer':'PTBTokenizer from pycocoevalcap','utility_numeric_validation_max_abs_error':max(abs(float(a)-float(b)) for a,b in zip(expected,actual)),'validation_cases':3,'wall_seconds':time.time()-t,'no_val_or_test_labels_used_for_idf':True}
(P/'CPU_READY.json').write_text(json.dumps(info,indent=2));print(json.dumps(info),flush=True)
