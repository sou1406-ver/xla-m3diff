
import json,sys
from pycocoevalcap.tokenizer.ptbtokenizer import PTBTokenizer
from pycocoevalcap.cider.cider import Cider
r=json.load(open(sys.argv[1]));p=[json.loads(l) for l in open(sys.argv[2]) if l.strip()]
g={x['id']:[] for x in r['images']}
for x in r['annotations']:g[x['image_id']].append({'caption':x['caption']})
h={x['id']:[{'caption':x['caption']}] for x in p}
t=PTBTokenizer();g=t.tokenize(g);h=t.tokenize(h)
_,scores=Cider().compute_score(g,h)
json.dump(dict(zip(g,map(float,scores))),open(sys.argv[3],'w'))
