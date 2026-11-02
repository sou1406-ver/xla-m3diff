"""Pre-training label audit: remove unsupported location from camera-object labels."""
from pathlib import Path
import json,hashlib
HERE=Path(__file__).parent;data=HERE/'data'
records=json.loads((data/'train.json').read_text(encoding='utf-8'))
manifest=[json.loads(l) for l in (data/'synthetic_manifest.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
byid={r['id']:r for r in records};changes=[];grammar_fixes=[]
policyhash=hashlib.sha256((HERE/'CAPTION_POLICY.json').read_bytes()).hexdigest()
for r in manifest:
    if 'An new ' in r['caption']:
        grammar_fixes.append(r['id']);r['caption']=r['caption'].replace('An new ','A new ')
        r['word_count']=len(r['caption'].split());byid[r['id']]['conversations'][-1]['value']=r['caption']
    r['caption_policy_sha256']=policyhash
    meta=r['metadata']
    if r['kind']=='camera_object':
        category=meta['category'];prefix=meta['camera_prefix']
        article='An' if category[0].lower() in 'aeiou' else 'A'
        obj=f'{article} {category} has been added to the scene.' if meta['obj_change']=='add' else f'The {category} has been removed from the scene.'
        cap=prefix+' '+obj
        changes.append({'id':r['id'],'before':r['caption'],'after':cap,'reason':'Original generator hardcodes center despite variable placement; neutral scene location is grounded.'})
        r['caption']=cap;r['word_count']=len(cap.split());meta['object_caption']=obj
        byid[r['id']]['conversations'][-1]['value']=cap
    elif r['kind']=='camera_only':meta['object_caption']=''
assert len(changes)==100
old=(data/'train.json').read_bytes();(data/'train.json').write_text(json.dumps(records,ensure_ascii=False),encoding='utf-8')
(data/'synthetic_manifest.jsonl').write_text('\n'.join(json.dumps(r,ensure_ascii=False) for r in manifest)+'\n',encoding='utf-8')
audit=json.loads((HERE/'DATA_AUDIT.json').read_text());(HERE/'DATA_AUDIT_BEFORE_CAPTION_FIX.json').write_text(json.dumps(audit,indent=2))
audit['train_json_sha256']=hashlib.sha256((data/'train.json').read_bytes()).hexdigest();audit['camera_object_neutral_location_fix_count']=100
audit['grammar_An_new_fix_count']=len(grammar_fixes)
audit['postprocess_source_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
(HERE/'DATA_AUDIT.json').write_text(json.dumps(audit,indent=2))
(HERE/'PRETRAIN_CAPTION_FIX.json').write_text(json.dumps({'before_train_json_sha256':hashlib.sha256(old).hexdigest(),'after_train_json_sha256':audit['train_json_sha256'],'changes':changes,'grammar_fix_ids':grammar_fixes},ensure_ascii=False,indent=2),encoding='utf-8')
print('Fixed100camera-object captions before approval; no images/gates changed.')
