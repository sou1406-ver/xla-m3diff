"""One-time pre-training cleanup of coarse HSV colour names; no image/gate edits."""
from pathlib import Path
import json,re,hashlib,datetime
P=Path(__file__).parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not (P/'FINAL_LABEL_AUDIT.json').exists(), 'Do not silently reapply'
records=json.loads((P/'data/train.json').read_text(encoding='utf-8'))
syn=[json.loads(x) for x in (P/'data/synthetic_manifest.jsonl').read_text(encoding='utf-8').splitlines()]
byid={r['id']:r for r in records}; changes=[]
before=sha(P/'data/train.json')
(P/'data/train_before_color_label_audit.json').write_bytes((P/'data/train.json').read_bytes())
colors=r'(?:black|white|red|blue|green|yellow|gray|grey|brown|pink|purple|orange|cyan)'
for r in syn:
    if r['kind'] not in ['single_color','multi_object']:continue
    old=r['caption']; sentences=old.split('. ')
    if r['kind']=='single_color':
        category=r['metadata']['category']
        location=next((loc for loc in ['on the right side of the scene','on the left side of the scene','in the center of the scene'] if loc in old),'in the scene')
    else:category=r['metadata']['categories'][0];location='on the left side of the scene'
    first=f'The color of the {category} {location} has changed.'
    tail='. '.join(sentences[1:]) if r['kind']=='multi_object' else ''
    tail=re.sub(r'\b'+colors+r' ', '',tail)
    tail=re.sub(r'\bAn? (?=(?:new|bowl|chair|cup|suitcase|cat|dog|teddy|potted|vase|clock|banana|bottle)\b)','A ',tail)
    tail=re.sub(r'\bA (?=umbrella\b)','An ',tail)
    cap=first+(' '+tail if tail else '')
    if not cap.endswith('.'):cap+='.'
    r['caption']=cap;r['word_count']=len(cap.split())
    byid[r['id']]['conversations'][-1]['value']=cap
    changes.append({'id':r['id'],'before':old,'after':cap})
assert len(changes)==600
(P/'data/train.json').write_text(json.dumps(records,ensure_ascii=False),encoding='utf-8')
(P/'data/synthetic_manifest.jsonl').write_text('\n'.join(json.dumps(r,ensure_ascii=False) for r in syn)+'\n',encoding='utf-8')
audit=json.loads((P/'DATA_AUDIT.json').read_text());audit['train_json_sha256']=sha(P/'data/train.json');audit['coarse_color_label_cleanup_records']=600
(P/'DATA_AUDIT.json').write_text(json.dumps(audit,indent=2))
result={'stage':'BEFORE_FIRST_TRAINING_ATTEMPT','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reason':'Assistant visual audit found coarse HSV colour names sometimes disagree with perceived colours. Retain grounded colour-change/category/location claims; remove coarse colour adjectives from generated multi-object claims. Original official replay untouched. This is a package of data changes, not an isolated colour ablation.','before_train_sha256':before,'after_train_sha256':audit['train_json_sha256'],'changes':changes}
(P/'FINAL_LABEL_AUDIT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(audit['train_json_sha256'])
