"""Score a complete matched benchmark. Selection precedes reading test references."""
from pathlib import Path
import hashlib, json, pickle, random, statistics
import numpy as np
from pycocoevalcap.tokenizer.ptbtokenizer import PTBTokenizer
from pycocoevalcap.cider.cider import Cider
from pycocoevalcap.bleu.bleu import Bleu
from pycocoevalcap.meteor.meteor import Meteor
from pycocoevalcap.rouge.rouge import Rouge
from utility import select

ROOT = Path('/mnt/m3diff/mbr_pilot_20261103')
P = ROOT / 'resume1020_v1' / 'combined_full1570'
assert json.loads((P / 'FULL_DONE.json').read_text())['complete']
records = [json.loads(x) for x in (P / 'results1570.jsonl').read_text().splitlines() if x.strip()]
questions = json.loads((P / 'questions1570.json').read_text())
assert len(records) == len({r['id'] for r in records}) == 1570
assert [r['id'] for r in records] == [q['id'] for q in questions]
assert hashlib.sha256((ROOT / 'train_idf.pkl').read_bytes()).hexdigest() == json.loads((ROOT / 'CPU_READY.json').read_text())['train_idf_sha256']
cache = pickle.load((ROOT / 'train_idf.pkl').open('rb'))
caps = {r['id']: [r['greedy']['caption']] + r['methods']['batch8']['samples'] for r in records}
assert all(len(cs) == 9 for cs in caps.values())
ptb = PTBTokenizer()
tokenized = ptb.tokenize({f'{i}|{j}': [{'caption': c}] for i, cs in caps.items() for j, c in enumerate(cs)})
selected = {i: select([tokenized[f'{i}|{j}'][0] for j in range(9)], cache) for i in caps}
(P / 'SELECTION.json').write_text(json.dumps({i: {'index': j, 'utilities': u} for i, (j, u) in selected.items()}, indent=2))
# Test references are opened only after every MBR selection is final.
parent = {}
def find(x):
    parent.setdefault(x, x)
    if parent[x] != x:
        parent[x] = find(parent[x])
    return parent[x]
for q in questions:
    roots = [find(i) for i in q['image']]
    for x in roots[1:]:
        parent[find(x)] = find(roots[0])
components = {q['id']: find(q['image'][0]) for q in questions}
summary, per = {}, []
rng = random.Random(20261109)
for domain, expected in [('real', 803), ('render', 767)]:
    rr = [r for r in records if r['domain'] == domain]
    ref = json.loads((P / f'OmniDiff_{domain.capitalize()}.json').read_text())
    g = {i['id']: [] for i in ref['images']}
    for a in ref['annotations']:
        g[a['image_id']].append({'caption': a['caption']})
    assert len(rr) == len(g) == expected
    assert {r['id'] for r in rr} == set(g)
    g = ptb.tokenize(g)
    scores, pair_scores = {}, {}
    for arm in ['greedy', 'MBR']:
        pred = {i: tokenized[f"{i}|{0 if arm == 'greedy' else selected[i][0]}"] for i in g}
        cid, pairs = Cider().compute_score(g, pred)
        pair_scores[arm] = dict(zip(g, map(float, pairs)))
        score = {'CIDEr': float(cid)}
        bleu, _ = Bleu(4).compute_score(g, pred)
        score.update({f'Bleu_{j+1}': float(v) for j, v in enumerate(bleu)})
        for scorer, name in [(Meteor(), 'METEOR'), (Rouge(), 'ROUGE_L')]:
            value, _ = scorer.compute_score(g, pred)
            score[name] = float(value)
        scores[arm] = {k: v * 100 for k, v in score.items()}
    rows = []
    for r in rr:
        i = r['id']; j = selected[i][0]
        row = {'id': i, 'domain': domain, 'image_component': components[i],
               'selected_index': j, 'greedy': caps[i][0], 'MBR': caps[i][j],
               'greedy_CIDEr_x100': pair_scores['greedy'][i]*100,
               'MBR_CIDEr_x100': pair_scores['MBR'][i]*100,
               'delta': (pair_scores['MBR'][i]-pair_scores['greedy'][i])*100,
               'unique_captions': len(set(caps[i]))}
        rows.append(row); per.append(row)
    groups = {}
    for r in rows:
        groups.setdefault(r['image_component'], []).append(r['delta'])
    keys = sorted(groups)
    boot = [statistics.mean(v for k in rng.choices(keys, k=len(keys)) for v in groups[k]) for _ in range(5000)]
    words = lambda arm: [len(r[arm].split()) for r in rows]
    summary[domain] = {'n': expected, 'scores_x100': scores,
        'delta_CIDEr_x100': scores['MBR']['CIDEr']-scores['greedy']['CIDEr'],
        'image_components': len(groups), 'descriptive_cluster_fixedDF_CI95': np.percentile(boot, [2.5,97.5]).tolist(),
        'words': {a: {'mean': statistics.mean(words(a)), 'median': statistics.median(words(a))} for a in ['greedy','MBR']},
        'changed': sum(r['greedy'] != r['MBR'] for r in rows)}
result = {'domains': summary, 'no_training': True, 'full_test_run': True,
          'selection_trainIDF_only': True, 'oracle_test_not_computed': True,
          'CI_limit': 'Descriptive image-component bootstrap conditional on fixed domain-reference DF, not a full DF recomputation.',
          'promotion': 'No automatic default-model change or factual-improvement claim.'}
(P/'METRICS.json').write_text(json.dumps(result, indent=2))
(P/'PER_PAIR.json').write_text(json.dumps(per, indent=2))
print(json.dumps(result, indent=2), flush=True)
