"""Prepare a locked full-test run locally; does not upload, admit or launch it."""
from pathlib import Path
import ast, copy, hashlib, json, statistics

P = Path(__file__).parent
F = P / 'full1570'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
metrics = json.loads((P / 'val200/METRICS.json').read_text())
assert metrics['all_gates_passed']
questions, selection, counts, source_hashes = [], [], {}, {}
for domain, expected in [('Real', 803), ('Render', 767)]:
    qpath = F / f'OmniDiff_{domain}_test.json'
    refpath = F / f'OmniDiff_{domain}.json'
    qq = json.loads(qpath.read_text())
    ref = json.loads(refpath.read_text())
    assert len(qq) == expected == len({q['id'] for q in qq})
    assert {q['id'] for q in qq} == {r['id'] for r in ref['images']}
    # Generation inputs contain only images and the human question, no answers.
    for q in qq:
        questions.append({'id': q['id'], 'image': q['image'],
                          'conversations': [q['conversations'][0]]})
        assert q['conversations'][0]['from'] == 'human'
        selection.append({'id': q['id'], 'subset': domain.lower()})
    counts[domain] = expected
    source_hashes[qpath.name], source_hashes[refpath.name] = sha(qpath), sha(refpath)
assert len({q['id'] for q in questions}) == 1570
for name, obj in [('questions1570.json', questions), ('selection1570.json', selection)]:
    (F / name).write_text(json.dumps(obj, indent=2), encoding='utf-8')

source = (P / 'evaluate200.py').read_text()
source = source.replace(source.splitlines()[0], '"""Matched full-test generation; references are not generation inputs."""')
changes = {
    '/mbr_pilot_20261103/val200': '/mbr_pilot_20261103/full1570',
    "'VAL_ATTEMPT.json'": "'FULL_ATTEMPT.json'",
    "'budget_cap_usd':3.60": "'budget_cap_usd':18.00",
    'questions200.json': 'questions1570.json',
    'selection200.json': 'selection1570.json',
    'results200.jsonl': 'results1570.jsonl',
    '/r64_val_precheck_20261102/images/': '/baseline_cache/OmniDiff/',
    "'planned':200": "'planned':1570",
    'len(records)==200': 'len(records)==1570',
    'MBR200_PROGRESS': 'MBR1570_PROGRESS',
    'VAL_DONE': 'FULL_DONE',
}
for old, new in changes.items():
    assert old in source, old
    source = source.replace(old, new)
guard = """admission=json.loads((P/'ADMISSION.json').read_text())
assert admission['authorized'] is True and admission['cap_usd'] <= 18
assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==admission['generator_sha256']
assert hashlib.sha256((P/'questions1570.json').read_bytes()).hexdigest()==admission['questions_sha256']
"""
source = source.replace("assert not (P/'FULL_ATTEMPT.json').exists()", guard + "assert not (P/'FULL_ATTEMPT.json').exists()")
preflight = """preflight_questions=json.loads((P/'questions1570.json').read_text())
image_root=Path('/mnt/m3diff/baseline_cache/OmniDiff').resolve()
for q in preflight_questions:
    for name in q['image']:
        image_path=(image_root/name).resolve()
        assert image_root in image_path.parents and image_path.is_file(),str(image_path)
"""
source = source.replace('disable_torch_init();base=', preflight + '\ndisable_torch_init();base=')
ast.parse(source)
(P / 'evaluate1570.py').write_text(source, encoding='utf-8')
nb = json.loads((P / 'val200.ipynb').read_text())
nb['cells'][-1]['source'] = ''.join(nb['cells'][-1]['source']).replace('evaluate200.py', 'evaluate1570.py').splitlines(True)
(P / 'full1570.ipynb').write_text(json.dumps(nb, indent=1), encoding='utf-8')
runner = (P / 'val200_modal.py').read_text()
for old, new in {
    'm3diff-mbr-val200': 'm3diff-mbr-full1570',
    'evaluate200.py': 'evaluate1570.py', 'val200.ipynb': 'full1570.ipynb',
    "gpu='A10'": "gpu='A100-80GB'", 'timeout=7200': 'timeout=19200',
    '/mbr_pilot_20261103/val200': '/mbr_pilot_20261103/full1570',
    "'VAL_ATTEMPT.json'": "'FULL_ATTEMPT.json'", 'start+6900': 'start+18900',
    'timeout=7170': 'timeout=19170', 'VAL_ERROR': 'FULL_ERROR',
    'VAL_JOB_TIMING': 'FULL_JOB_TIMING',
}.items():
    assert old in runner, old
    runner = runner.replace(old, new)
ast.parse(runner)
(P / 'full1570_modal.py').write_text(runner, encoding='utf-8')

protocol = {
    'status': 'PREPARED_NOT_ADMITTED_NOT_LAUNCHED',
    'counts': counts, 'source_file_hashes': source_hashes,
    'sampling_protocol_sha256': sha(P / 'PROTOCOL.json'),
    'questions_sha256': sha(F / 'questions1570.json'),
    'generator_sha256': sha(P / 'evaluate1570.py'),
    'runner_sha256': sha(P / 'full1570_modal.py'),
    'notebook_sha256': sha(P / 'full1570.ipynb'),
    'scorer_sha256': sha(P / 'score1570_cpu.py'),
    'scorer_runner_sha256': sha(P / 'score1570_modal.py'),
    'same_config_as_val200': True, 'effective_sample_batch_size': 2,
    'same_gpu_session_fresh_greedy_and_samples': True,
    'train_idf_only_selection': True, 'no_training': True,
    'oracle_on_full_test': False,
    'hardware_selection': 'cost and parity only; A100 candidates not scored against references',
    'hard_timeout_seconds': 19200, 'soft_timeout_seconds': 18900,
    'proposed_cap_usd': 18, 'gpu_rate_upper_hour': '3.24',
    'gpu_reservation_including180startup_usd': '17.45',
    'cpu_scoring_and_misc_allowance_usd': '.25',
    'total_proposed_reservation_usd': '17.70',
    'stop': 'No automatic retry/resume; partial run is not a completed benchmark.',
    'promotion': 'Base remains default until full paired evidence and factual review support a change.',
    'limitation': 'Historically exposed benchmark; not claimed to be an untouched blind test.',
}
(F / 'PROPOSED_PROTOCOL.json').write_text(json.dumps(protocol, indent=2), encoding='utf-8')
print('Prepared full1570 scripts and hashes; no ADMISSION.json created and no dispatch.')
