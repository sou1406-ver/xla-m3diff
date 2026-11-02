from pathlib import Path
import csv,json,re,ast,collections
HERE=Path(__file__).parent
cam_source=(HERE.parent/'checkpoint_audit_20261102/ft/code/ft_common.py').read_text(encoding='utf-8')
tree=ast.parse(cam_source)
cam=None
for node in tree.body:
    if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='CAM' for t in node.targets):cam=re.compile(ast.literal_eval(node.value.args[0]),re.I)
assert cam is not None
truth=lambda v:str(v).lower()=='true'
raw={a:[json.loads(l) for l in (HERE/f'{a}.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()] for a in ['base','r64']}
scores={a:list(csv.DictReader((HERE/f'{a}_scores/per_pair.csv').open(encoding='utf-8'))) for a in raw}
for a in raw:
    assert len(raw[a])==len(scores[a])==600
assert {r['id'] for r in raw['base']}=={r['id'] for r in raw['r64']}
summary={'n':600,'arms':{},'types':{},'gates':{},'full_omnidiff_run':False,'gate_is_keyword_proxy':True}
for a in raw:
    caps={r['id']:r['caption'] for r in raw[a]};flagged=[]
    for row in scores[a]:
        s=caps[row['pair_id']]
        if cam.search(s) or truth(row['m_view']):flagged.append({'id':row['pair_id'],'condition':row['cond'],'caption':s,'CAM':bool(cam.search(s)),'m_view':truth(row['m_view'])})
    summary['arms'][a]={'camera_union':len(flagged),'CAM':sum(bool(cam.search(r['caption'])) for r in raw[a]),'m_view':sum(truth(r['m_view']) for r in scores[a]),'camera_union_by_condition':dict(collections.Counter(r['condition'] for r in flagged))}
    (HERE/f'{a}_camera_flags.json').write_text(json.dumps(flagged,ensure_ascii=False,indent=2),encoding='utf-8')
for cond in ['add','remove','color','move','size','light']:
    d={}
    for a in raw:
        rows=[r for r in scores[a] if r['cond']==cond]
        d[a]={'n':len(rows),'correct_type_keyword':sum(truth(r['type_ok']) for r in rows),'correct_type_and_name_keyword':sum(truth(r.get('joint_ok','')) for r in rows)}
    d['pass_type_retention']=d['r64']['correct_type_keyword']>=d['base']['correct_type_keyword']
    summary['types'][cond]=d
summary['gates']['camera_union_le_30']=summary['arms']['r64']['camera_union']<=30
summary['gates']['all_six_types_preserved']=all(r['pass_type_retention'] for r in summary['types'].values())
summary['gates']['passed']=all(summary['gates'].values())
summary['decision']='Wait for user review; do not automatically run full test.' if summary['gates']['passed'] else 'Failed locked gate. Stop and do not run full test.'
(HERE/'gate_result.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
