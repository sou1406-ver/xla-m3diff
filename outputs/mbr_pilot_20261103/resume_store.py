"""Validate and retain complete pairs without choosing by caption quality."""
from pathlib import Path
import hashlib, json, os, uuid

def seed_for(pair_id, seed=20261105):
    return seed + int(hashlib.sha256(pair_id.encode()).hexdigest()[:8], 16) % 1000000

def validate(row, question):
    assert row['id'] == question['id']
    assert row['greedy']['caption'].strip()
    method = row['methods']['batch8']
    assert len(method['samples']) == 8 and all(c.strip() for c in method['samples'])
    assert method['seed'] == seed_for(question['id'])
    return row

def prefix(questions, directory):
    directory = Path(directory)
    known = {q['id']: q for q in questions}
    records = {}
    for path in directory.glob('*.json'):
        row = json.loads(path.read_text())
        assert path.stem == row['id'] and row['id'] in known
        records[row['id']] = validate(row, known[row['id']])
    result = []
    for q in questions:
        if q['id'] not in records:
            break
        result.append(records[q['id']])
    assert len(result) == len(records), 'Non-prefix records: stop rather than discard or reselect.'
    return result

def save(directory, row):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / (row['id'] + '.json')
    assert not target.exists(), 'Never overwrite a completed pair.'
    temp = directory / (row['id'] + '.' + uuid.uuid4().hex + '.tmp')
    temp.write_text(json.dumps(row), encoding='utf-8')
    os.replace(temp, target)
