from pathlib import Path
import json,ast
ROOT=Path(__file__).parent;cells=[]
def md(s):cells.append({'cell_type':'markdown','metadata':{},'source':s.splitlines(keepends=True)})
def code(s):
 ast.parse(s);cells.append({'cell_type':'code','metadata':{},'execution_count':None,'outputs':[],'source':s.splitlines(keepends=True)})
md('''# M3Diff đã fine-tune — chạy trên máy GPU khác

Không train lại. Giải nén toàn bộ gói, chọn kernel **Python3.10 trên Linux/WSL2/server GPU**, sửa hai đường dẫn ảnh rồi chạy lần lượt.

Adapter trong gói là bản nghiên cứu, giảm điểm caption trên full test và chưa sửa được xoay/zoom tổng thể. Mặc định `USE_ADAPTER=False` chạy checkpoint gốc; đổi thành `True` để thử weights đã fine-tune, không train lại. GPU đã kiểm tra: A10 khoảng24GB và A100. Base khoảng14GB và vision tower tải riêng lần đầu; có thể chuẩn bị các file này trước khi thuê GPU.
''')
code('''from pathlib import Path
import sys, subprocess, json, hashlib
ROOT = Path.cwd()
assert (ROOT / 'code/run_caption.py').is_file(), 'Mở notebook trong thư mục gói đã giải nén.'
assert sys.version_info[:2] == (3, 10), 'Chọn kernel Python3.10 cho đúng môi trường đã kiểm tra.'

BEFORE = ROOT / 'before.jpg'  # Sửa ảnh trước
AFTER = ROOT / 'after.jpg'    # Sửa ảnh sau
BASE = ROOT / 'M3Diff-base'   # Có thể trỏ tới model gốc đã tải sẵn
USE_ADAPTER = False
EXACT_IDENTITY_GUARD = True
MAX_NEW_TOKENS = 1024
''')
md('''## Cài thư viện và source một lần

Cell này cài môi trường inference; không thực hiện training. Nếu kernel đã import phiên bản torch/transformers khác, khởi động lại kernel sau khi cài.
''')
code('''subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', str(ROOT / 'requirements-linux.txt')])
repo = ROOT / 'M3Diff-code'
commit = '4e346e52185620ec6fa17235d93b0c26a9d47a71'
if not repo.exists():
    subprocess.check_call(['git', 'clone', 'https://github.com/Yuan-Liu-01/M3Diff.git', str(repo)])
    subprocess.check_call(['git', '-C', str(repo), 'checkout', commit])
else:
    actual = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', 'HEAD'], text=True).strip()
    assert actual == commit, 'Thư mục source đang ở commit khác; dùng thư mục gói mới để giữ đúng bản.'
subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--no-deps', '-e', str(repo)])
''')
md('## Tải base đúng revision nếu chưa có\n\nTải weights chỉ là chuẩn bị để chạy, không phải train lại.')
code('''if not (BASE / 'config.json').is_file():
    subprocess.check_call([sys.executable, str(ROOT / 'download_base.py'), '--output', str(BASE)])
assert (ROOT / 'model/m3diff-mixed-lora/adapter_model.bin').is_file(), 'Gói thiếu file adapter weights.'
''')
md('''## Chạy hai ảnh

Guard chỉ nhận hai ảnh có RGB trùng từng pixel; ảnh gần giống/xoay/zoom vẫn đưa vào model. Guard được ghi riêng trong kết quả. File kết quả tự đổi khi ảnh hoặc cấu hình đổi để tránh lấy nhầm caption cũ.
''')
code('''assert BEFORE.is_file() and AFTER.is_file(), 'Sửa BEFORE/AFTER tới hai ảnh thật.'
def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(4 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()
settings = {'before': str(BEFORE.resolve()), 'after': str(AFTER.resolve()),
            'before_sha': sha(BEFORE), 'after_sha': sha(AFTER), 'base': str(BASE.resolve()),
            'adapter': USE_ADAPTER, 'guard': EXACT_IDENTITY_GUARD, 'max_new_tokens': MAX_NEW_TOKENS}
run_key = hashlib.sha256(json.dumps(settings, sort_keys=True).encode()).hexdigest()[:12]
results = ROOT / 'results'; results.mkdir(exist_ok=True)
questions = results / f'questions_{run_key}.json'
answers = results / f'captions_{run_key}.jsonl'
subprocess.check_call([sys.executable, str(ROOT / 'make_question.py'), '--before', str(BEFORE),
                       '--after', str(AFTER), '--output', str(questions)])
cmd = [sys.executable, str(ROOT / 'code/run_caption.py'), '--question-file', str(questions),
       '--answers-file', str(answers), '--image-folder', str(ROOT),
       '--max-new-tokens', str(MAX_NEW_TOKENS), '--load-audit', str(results / f'load_{run_key}.json')]
if USE_ADAPTER:
    cmd += ['--model-path', str(ROOT / 'model/m3diff-mixed-lora'), '--model-base', str(BASE)]
else:
    cmd += ['--model-path', str(BASE)]
if EXACT_IDENTITY_GUARD:
    cmd += ['--exact-identity-guard']
subprocess.check_call(cmd)
''')
code('''rows = [json.loads(line) for line in answers.read_text().splitlines() if line.strip()]
for row in rows:
    print('Nguồn:', row.get('caption_source', 'M3Diff model'))
    print(row['caption'])
print('Kết quả:', answers)
''')
md('''## Lọc lặp tùy chọn

Lọc chỉ xóa câu lặp nguyên văn, không xác minh ảnh và không sửa phát biểu sai. Giữ file raw để đối chiếu.
''')
code('''clean = answers.with_name(answers.stem + '_clean.jsonl')
subprocess.check_call([sys.executable, str(ROOT / 'code/clean_captions.py'), '--input', str(answers), '--output', str(clean)])
print(clean.read_text())
''')
notebook={'nbformat':4,'nbformat_minor':5,'metadata':{'kernelspec':{'display_name':'Python3.10','language':'python','name':'python3'},'language_info':{'name':'python','version':'3.10'}},'cells':cells}
for i,c in enumerate(cells):c['id']=f'm3diff-{i:02d}'
path=ROOT/'m3diff-inference-portable.ipynb';path.write_text(json.dumps(notebook,ensure_ascii=False,indent=2),encoding='utf8');print({'notebook':str(path),'cells':len(cells),'code_cells_syntax_checked':True,'training_cells':0})
