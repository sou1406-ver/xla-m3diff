"""Correct a derived recognition counter without changing any error/fact judgment."""
import copy,hashlib,json
from pathlib import Path
HERE=Path(__file__).parent;changes={}
for stage in ['initial','new']:
    p=HERE/(stage+'_assessments.json');original=p.read_bytes();data=json.loads(original)
    backup=HERE/(stage+'_assessments_before_ack_derivation.json')
    if not backup.exists():backup.write_bytes(original)
    old=copy.deepcopy(data);count=0
    for row in data['cases']:
        if not row['id'].endswith('__brightness'):continue
        for label in ['candidate_1','candidate_2']:
            s=row[label];value=int(s['false_light']==0 and any(w in s['caption'].lower() for w in ['bright','illumin','lit up','light in']))
            count+=value!=s['ack'];s['ack']=value
    def without_ack(d):
        d=copy.deepcopy(d)
        for row in d['cases']:
            for label in ['candidate_1','candidate_2']:row[label].pop('ack',None)
        return d
    assert without_ack(old)==without_ack(data)
    p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
    changes[stage]={'changed_ack_fields':count,'original_sha256':hashlib.sha256(backup.read_bytes()).hexdigest(),
        'all_error_fact_uncertainty_labels_unchanged':True}
(HERE/'ACK_DERIVATION_AUDIT.json').write_text(json.dumps({'reason':'Correct brightness acknowledgement is counted even if the same caption has another false claim. Initial helper incorrectly required the entire caption to be error-free. Secondary counter only; no gate/error/fact labels changed. Correction made after decoding; original masked assessments retained.','changes':changes},indent=2))
print(changes)
