from pathlib import Path
import json
from pycocotools.coco import COCO
from pycocoevalcap.tokenizer.ptbtokenizer import PTBTokenizer
from pycocoevalcap.cider.cider import Cider
p=Path('/mnt/m3diff/r64_v2_final_round/evaluation');result={};per=[]
for domain in ['real','render']:
    coco=COCO(str(p/f'{domain}_reference.json'));ids=coco.getImgIds();result[domain]={}
    for arm in ['base','v2']:
        rows=[json.loads(l) for l in (p/f'{arm}.jsonl').read_text().splitlines() if l.strip()]
        rows=[{'image_id':r['id'],'caption':r['caption']} for r in rows if r['id'] in ids]
        assert len(rows)==100
        res=coco.loadRes(rows);tok=PTBTokenizer()
        gts=tok.tokenize({i:coco.imgToAnns[i] for i in ids});pred=tok.tokenize({i:res.imgToAnns[i] for i in ids})
        score,scores=Cider().compute_score(gts,pred);result[domain][arm]={'n':100,'CIDEr_x100':float(score)*100}
        per += [{'domain':domain,'arm':arm,'id':i,'CIDEr_x100':float(s)*100} for i,s in zip(ids,scores)]
    result[domain]['delta_v2_minus_base']=result[domain]['v2']['CIDEr_x100']-result[domain]['base']['CIDEr_x100']
(p/'metrics.json').write_text(json.dumps(result,indent=2));(p/'per_pair_cider.json').write_text(json.dumps(per,indent=2))
print(json.dumps(result,indent=2))
