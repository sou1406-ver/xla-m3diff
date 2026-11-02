from pathlib import Path
import json,hashlib
HERE=Path(__file__).parent
lock=json.loads((HERE/'SELECTION_LOCK.json').read_text(encoding='utf-8'))
q=json.loads((HERE/'questions.json').read_text(encoding='utf-8'))
assert hashlib.sha256((HERE/'questions.json').read_bytes()).hexdigest()==lock['hashes']['questions.json']
assert len(q)==200 and len({r['id'] for r in q})==200
audits={};lengths={}
for arm in ['base','r64']:
    rows=[json.loads(l) for l in (HERE/f'{arm}.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
    assert [r['id'] for r in rows]==[r['id'] for r in q]
    assert all(r['caption'].strip() for r in rows)
    audits[arm]=json.loads((HERE/f'{arm}.jsonl.generation_audit.json').read_text())
    lengths[arm]={'mean_words':sum(len(r['caption'].split()) for r in rows)/200,'over_500_words':sum(len(r['caption'].split())>500 for r in rows)}
assert audits['base']['effective_explicit_overrides']==audits['r64']['effective_explicit_overrides']
assert audits['base']['mdp_projector_dtype_counts']==audits['r64']['mdp_projector_dtype_counts']
m=json.loads((HERE/'metrics.json').read_text());assert all(m[d][a]['n']==100 for d in ['real','render'] for a in ['base','r64'])
report={'n_pairs_each_arm':200,'same_generation_overrides':True,'same_mdp_projector_dtypes':True,'caption_lengths':lengths,'replay_increase_flag':any(m[d]['delta_r64_minus_base'] < -1 for d in ['real','render']),'note':'Precheck for recipe design, not proof of equivalence or an independent final validation.'}
(HERE/'VALIDATED.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
