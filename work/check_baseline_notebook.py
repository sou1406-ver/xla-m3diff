import ast
import json
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
nb = json.loads((root / 'outputs/m3diff-baseline-full.ipynb').read_text(encoding='utf-8'))
sources = [c['source'] for c in nb['cells'] if c['cell_type'] == 'code']
for s in sources:
    ast.parse(s)
for marker in ['download_script', 'score_script', 'resume']:
    found = False
    for s in sources:
        for node in ast.walk(ast.parse(s)):
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == marker for t in node.targets):
                value = ast.literal_eval(node.value)
                ast.parse(('def runner():\n' + value) if marker == 'resume' else value)
                found = True
    assert found, marker

ns = {'json': json, 'Path': Path}
source = next(s for s in sources if 'def completed(' in s)
fn = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == 'completed')
exec(compile(ast.Module(body=[fn], type_ignores=[]), '<completed>', 'exec'), ns)
check = ns['completed']
qs = [{'id': 'a'}, {'id': 'b'}]
def row(i):
    return json.dumps({'id': i, 'image_id': i, 'caption': 'A valid caption.'})
with tempfile.TemporaryDirectory() as d:
    path = Path(d) / 'answers.jsonl'
    assert check(path, qs) == set()
    path.write_text(row('a') + '\n')
    assert check(path, qs) == {'a'}
    path.write_text(row('a') + '\n' + '{"id":')
    assert check(path, qs, True) == {'a'}
    try:
        check(path, qs)
    except json.JSONDecodeError:
        pass
    else:
        raise AssertionError('truncated row accepted for scoring')
    for text in [row('a')+'\n'+row('a'), row('unknown')]:
        path.write_text(text)
        try:
            check(path, qs)
        except AssertionError:
            pass
        else:
            raise AssertionError('invalid IDs accepted')
    path.write_text(row('a')+'\n'+row('b'))
    assert check(path, qs) == {'a', 'b'}

# Execute the resume block itself: retain valid rows, remove only an interrupted final row.
patch_source = next(s for s in sources if 'source_path = REPO' in s)
tree = ast.parse(patch_source)
resume = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
              and any(isinstance(t, ast.Name) and t.id == 'resume' for t in n.targets))
exec(compile('def resume_test(questions, answers_file, model):\n'+resume+
             '    ans_file.close()\n    return questions\n', '<resume>', 'exec'), ns)
import os
ns['os'] = os
class Model:
    def eval(self):
        pass
with tempfile.TemporaryDirectory() as d:
    p = Path(d) / 'pred.jsonl'
    p.write_text(row('a')+'\n{"id":')
    assert ns['resume_test'](qs, str(p), Model()) == [{'id': 'b'}]
    assert check(p, qs) == {'a'}
assert all(not c.get('outputs') for c in nb['cells'])
print('PASS: notebook JSON, all code cells, embedded scripts, missing/partial/full results, duplicate/foreign IDs, interrupted-write repair.')
