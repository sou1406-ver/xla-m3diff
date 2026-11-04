import ast
import json
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[1]
old = json.loads((ROOT / 'notebooks' / 'archive' / 'm3diff-modal-eval.ipynb').read_text(encoding='utf-8'))
cells = []

def md(s):
    cells.append({'cell_type': 'markdown', 'metadata': {}, 'source': dedent(s).strip() + '\n'})

def code(s):
    s = dedent(s).strip() + '\n'
    ast.parse(s)
    cells.append({'cell_type': 'code', 'execution_count': None, 'metadata': {}, 'outputs': [], 'source': s})

md('''
# M³Diff — Dựng lại baseline từ đầu đến cuối

**Chạy trên Modal Notebook, Linux, 1 GPU A10/L4/A100 có ít nhất 24 GB VRAM, RAM hệ thống nên từ 32 GB.**
Gắn Volume tên `m3diff` tại `/mnt/m3diff`, dành khoảng 40 GB dung lượng trống trở lên.
Sau đó chọn **Run all**. Không cần notebook cũ, không fine-tune, không căn chỉnh, không tạo dữ liệu tổng hợp.

Notebook tải checkpoint M³Diff đã công bố, chạy **toàn bộ test OmniDiff-Real và OmniDiff-Render**, rồi tính
BLEU-1…4, METEOR, ROUGE-L, CIDEr bằng bộ chấm COCO. SPICE không nằm trong lần chạy mặc định này.
Đây là tái lập inference/đánh giá; không huấn luyện lại từ backbone.

Kết quả và cache nằm trên Volume. Nếu phiên bị ngắt, mở lại với cùng Volume rồi **Run all**;
các ID hoàn tất sẽ được giữ lại. Không trộn kết quả từ các notebook cũ.
Thời gian tùy GPU và mạng; cần dành vài giờ cho tải dữ liệu, inference và tính điểm.

Repo: https://github.com/Yuan-Liu-01/M3Diff
Checkpoint: https://huggingface.co/IVC-liuyuan/M3Diff
Dataset: https://huggingface.co/datasets/IVC-liuyuan/OmniDiff
''')

md('## 1. Cấu hình và kiểm tra GPU / Volume')
code('''
import os, sys, json, shutil, subprocess, time, hashlib, csv, platform, datetime, zipfile
from pathlib import Path

VOL = Path('/mnt/m3diff')
RUN_NAME = 'baseline_reproduction_v1'  # đổi tên nếu muốn một lần chạy độc lập
RUN = VOL / RUN_NAME
REPO = RUN / 'repo'
VENV = Path('/root/m3diff-baseline-venv')
PY = str(VENV / 'bin/python')
CKPT = VOL / 'baseline_cache' / 'M3Diff'
IMG = VOL / 'baseline_cache' / 'OmniDiff'
HF_CACHE = VOL / 'baseline_cache' / 'huggingface'
CODE = RUN / 'code'
SPLITS = ('Real', 'Render')
SEED = 42
MAX_NEW_TOKENS = 1024  # giữ mặc định script đánh giá gốc

if platform.system() != 'Linux':
    raise RuntimeError('Notebook này dành cho Modal/Linux GPU, không chạy trực tiếp trên Windows.')
if not VOL.is_dir():
    raise RuntimeError('Chưa gắn Volume tại /mnt/m3diff. Gắn Volume rồi Run all lại.')
for p in (RUN, CODE, CKPT, IMG, HF_CACHE, RUN / 'logs'):
    p.mkdir(parents=True, exist_ok=True)
os.environ['HF_HOME'] = str(HF_CACHE)
os.environ['HF_HUB_DISABLE_XET'] = '1'
os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
os.environ['PYTHONHASHSEED'] = str(SEED)
# Nếu cần xác thực, đặt HF_TOKEN trong Secrets của Modal; không dán token vào notebook.

def run(cmd, *, cwd=None, env=None, log=None):
    print('Chạy:', ' '.join(map(str, cmd)), flush=True)
    fp = open(log, 'a', encoding='utf-8') if log else None
    try:
        with subprocess.Popen(list(map(str, cmd)), cwd=cwd, env=env,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              text=True, bufsize=1) as proc:
            for line in proc.stdout:
                print(line, end='', flush=True)
                if fp:
                    fp.write(line); fp.flush()
            rc = proc.wait()
        if rc:
            raise RuntimeError(f'Lệnh thất bại (exit {rc}). Xem log ở cell này; sửa lỗi rồi Run all lại.')
    finally:
        if fp:
            fp.close()

def capture(cmd, cwd=None):
    return subprocess.check_output(list(map(str, cmd)), cwd=cwd, text=True).strip()

gpu = capture(['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader'])
print(gpu)
memory_mb = int(gpu.splitlines()[0].rsplit(',', 1)[1].strip().split()[0])
if memory_mb < 22000:
    raise RuntimeError('Chọn A10/L4/A100 >=24 GB. Baseline này dùng BF16, không lượng tử hóa.')
print('Dung lượng trống Volume (GiB):', round(shutil.disk_usage(VOL).free / 2**30, 1))
print('Thư mục kết quả:', RUN)
''')

md('## 2. Tạo Python 3.10 riêng và cài môi trường\nDùng `uv` có sẵn trong Modal; mọi lệnh cài đặt đều kiểm tra mã thoát.')
code('''
UV = shutil.which('uv')
if UV is None:
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'uv'], check=True)
    UV = shutil.which('uv')
if UV is None:
    raise RuntimeError('Không thấy uv sau khi cài. Cài uv trong môi trường Modal rồi Run all lại.')

if not (REPO / '.git').is_dir():
    run(['git', 'clone', 'https://github.com/Yuan-Liu-01/M3Diff.git', REPO])
if not Path(PY).exists():
    run([UV, 'venv', VENV, '--python', '3.10'])
run([UV, 'pip', 'install', '--python', PY, '-e', str(REPO) + '[eval]',
     'numpy<2', 'accelerate==0.29.1', 'bitsandbytes==0.43.3', 'install-jdk'])
run([PY, '-c', "import torch, transformers, numpy; print('torch',torch.__version__,'transformers',transformers.__version__,'numpy',numpy.__version__); assert torch.cuda.is_available(); assert torch.cuda.is_bf16_supported(), 'GPU không hỗ trợ BF16'; print(torch.cuda.get_device_name(0))"])
(RUN / 'environment_freeze.txt').write_text(capture([UV, 'pip', 'freeze', '--python', PY]) + '\\n')
REPO_COMMIT = capture(['git', 'rev-parse', 'HEAD'], cwd=REPO)
print('Repo commit:', REPO_COMMIT)
''')

md('## 3. Tải checkpoint và ảnh test\nRevision Hugging Face được cố định trong file, tránh đổi weights giữa các lần chạy tiếp. Lỗi tải tạm thời được thử lại tối đa 5 lần.')
code('''
download_script = r"""
import json, os, sys, time
from pathlib import Path
from huggingface_hub import HfApi, snapshot_download
run, ckpt, img = map(Path, sys.argv[1:])
api = HfApi(token=os.environ.get('HF_TOKEN') or None)
def retry(fn):
    for attempt in range(5):
        try:
            return fn()
        except Exception as e:
            if attempt == 4:
                raise
            delay = min(60, 10 * (attempt + 1))
            print(f'Tải chưa xong ({type(e).__name__}), thử lại sau {delay}s', flush=True)
            time.sleep(delay)
rp = run / 'hf_revisions.json'
if rp.exists():
    rev = json.loads(rp.read_text())
else:
    rev = {'model': retry(lambda: api.model_info('IVC-liuyuan/M3Diff')).sha,
           'dataset': retry(lambda: api.dataset_info('IVC-liuyuan/OmniDiff')).sha}
    rp.write_text(json.dumps(rev, indent=2))
retry(lambda: snapshot_download('IVC-liuyuan/M3Diff', revision=rev['model'],
                               local_dir=ckpt, max_workers=2, token=os.environ.get('HF_TOKEN') or None))
retry(lambda: snapshot_download('IVC-liuyuan/OmniDiff', repo_type='dataset', revision=rev['dataset'],
                               local_dir=img, allow_patterns=['Real/test/*', 'Render/test/*'],
                               max_workers=2, token=os.environ.get('HF_TOKEN') or None))
print('Tải xong:', rev)
"""
(CODE / 'download.py').write_text(download_script)
run([PY, CODE / 'download.py', RUN, CKPT, IMG], log=RUN / 'logs/download.log')

QUESTIONS = {}
for split in SPLITS:
    qfile = REPO / f'data/evaluation/prompt/OmniDiff_{split}_test.json'
    qs = json.loads(qfile.read_text())
    ids = [q['id'] for q in qs]
    assert len(ids) == len(set(ids)), f'{split}: ID câu hỏi bị trùng'
    need = {p for q in qs for p in q['image']}
    missing = [p for p in need if not (IMG / p).is_file()]
    if missing:
        raise RuntimeError(f'{split}: thiếu {len(missing)} ảnh, ví dụ {missing[:5]}')
    QUESTIONS[split] = qs
    print(f'{split}: {len(qs)} cặp, {len(need)} ảnh, không thiếu file.')
assert (CKPT / 'config.json').is_file(), 'Checkpoint thiếu config.json'
''')

md('## 4. Chuẩn bị runner baseline\nGiữ cách xử lý ảnh/prompt và sinh caption của repo. Chỉ thêm device map cho 1 GPU, seed và resume theo ID; runner nằm riêng, không sửa source repo.')

# Reuse the proven device-map patch from user's notebook, but replace its resume implementation.
patch_src = ''.join(old['cells'][7]['source'])
start = patch_src.index('old1 = ')
end = patch_src.index('# --- Patch 2:')
patch_def = patch_src[start:end]
patch_def = patch_def.replace('"8bit")', '"none")')
code('''
source_path = REPO / 'llava/eval/model_vqa_qwen_OmniDiff_Real.py'
src = source_path.read_text()
''' + patch_def + '''
if src.count(old1) != 1:
    raise RuntimeError('Script upstream đã đổi phần load model; dừng để tránh patch sai.')
src = src.replace(old1, new1, 1)
src = src.replace('    disable_torch_init()', ''' + repr('''    import random
    import numpy as np
    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)
    torch.cuda.manual_seed_all(42)
    disable_torch_init()''') + '''.replace('(42)', f'({SEED})'), 1)
old_open = '    ans_file = open(answers_file, "w")\\n'
resume = ''' + repr('''    expected_ids = {q["id"] for q in questions}
    saved = {}
    if os.path.exists(answers_file):
        with open(answers_file) as f:
            lines = f.readlines()
        for i, line in enumerate(lines):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                if i == len(lines) - 1:
                    print("[resume] Bỏ dòng cuối bị ngắt khi ghi", flush=True)
                    continue
                raise
            if row.get("id") not in expected_ids or row.get("image_id") != row["id"]:
                raise RuntimeError("File kết quả chứa ID ngoài tập câu hỏi hoặc sai schema")
            if not isinstance(row.get("caption"), str) or not row["caption"].strip():
                raise RuntimeError("File kết quả chứa caption rỗng")
            if row["id"] in saved:
                raise RuntimeError("File kết quả chứa ID trùng")
            saved[row["id"]] = row
    tmp = answers_file + ".repair.tmp"
    with open(tmp, "w") as f:
        for row in saved.values():
            f.write(json.dumps(row) + "\\n")
    os.replace(tmp, answers_file)
    questions = [q for q in questions if q["id"] not in saved]
    print(f"[resume] {len(saved)} xong, còn {len(questions)}", flush=True)
    model.eval()
    ans_file = open(answers_file, "a")
''') + '''
if src.count(old_open) != 1:
    raise RuntimeError('Script upstream đã đổi phần ghi file.')
src = src.replace(old_open, resume, 1)
src = src.replace('        ans_file.flush()', '        ans_file.flush()\\n        os.fsync(ans_file.fileno())', 1)
compile(src, '<baseline_runner>', 'exec')
EVAL_SCRIPT = CODE / 'baseline_eval.py'
EVAL_SCRIPT.write_text(src)

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

cfg = {
    'repo_commit': REPO_COMMIT,
    'hf_revisions': json.loads((RUN / 'hf_revisions.json').read_text()),
    'seed': SEED, 'quantization': 'none', 'dtype': 'bfloat16',
    'temperature': 0, 'num_beams': 1, 'max_new_tokens': MAX_NEW_TOKENS,
    'use_cache': True, 'flash_attention': False, 'conv_mode': 'qwen_2',
    'extra_prompt': '', 'runner_sha256': sha(EVAL_SCRIPT),
    'questions_sha256': {s: sha(REPO / f'data/evaluation/prompt/OmniDiff_{s}_test.json') for s in SPLITS},
    'reference_sha256': {s: sha(REPO / f'data/evaluation/reference/OmniDiff_{s}.json') for s in SPLITS},
}
config_file = RUN / 'run_config.json'
if config_file.exists() and json.loads(config_file.read_text()) != cfg:
    raise RuntimeError('Cấu hình khác lần chạy trước. Đặt RUN_NAME mới để không trộn kết quả.')
config_file.write_text(json.dumps(cfg, indent=2))
(RUN / 'gpu.txt').write_text(gpu + '\\n')
(RUN / 'repo_diff.patch').write_text(capture(['git', 'diff'], cwd=REPO))
print('Runner sẵn sàng. Config:', config_file)
''')

md('## 5. Chạy kiểm tra 3 cặp\nNếu bước này lỗi, notebook dừng trước khi chạy toàn bộ test.')
code('''
def completed(path, qs, allow_partial_tail=False):
    expected = {q['id'] for q in qs}
    if not Path(path).exists():
        return set()
    lines = Path(path).read_text().splitlines()
    ids = set()
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            if allow_partial_tail and i == len(lines)-1:
                continue
            raise
        assert row.get('id') in expected and row.get('image_id') == row['id'], 'Sai ID/schema kết quả'
        assert row['id'] not in ids, 'Trùng ID kết quả'
        assert isinstance(row.get('caption'), str) and row['caption'].strip(), 'Caption rỗng'
        ids.add(row['id'])
    return ids

def evaluate(qfile, out, qs, log):
    out.parent.mkdir(parents=True, exist_ok=True)
    done = completed(out, qs, allow_partial_tail=True)
    print(f'{out.name}: {len(done)}/{len(qs)} cặp hoàn tất')
    # Nếu dòng cuối bị hỏng dù đã đủ ID, vẫn chạy runner để sửa file.
    try:
        clean = len(completed(out, qs)) == len(qs)
    except json.JSONDecodeError:
        clean = False
    if not clean:
        env = dict(os.environ, M3DIFF_QUANT='none', PYTHONWARNINGS='ignore',
                   CUDA_VISIBLE_DEVICES='0',
                   PYTHONPATH=str(REPO) + os.pathsep + os.environ.get('PYTHONPATH', ''))
        run([PY, EVAL_SCRIPT, '--model-path', CKPT, '--question-file', qfile,
             '--answers-file', out, '--image-folder', IMG,
             '--num-chunks', '1', '--chunk-idx', '0', '--temperature', '0',
             '--num_beams', '1', '--max-new-tokens', str(MAX_NEW_TOKENS),
             '--conv-mode', 'qwen_2', '--torch-dtype', 'bfloat16', '--no-flash-attention'],
            cwd=REPO, env=env, log=log)
    assert len(completed(out, qs)) == len(qs), 'Chưa đủ caption, chưa được tính điểm'

smoke_q = RUN / 'smoke_questions.json'
smoke_q.write_text(json.dumps(QUESTIONS['Real'][:3]))
evaluate(smoke_q, RUN / 'smoke.jsonl', QUESTIONS['Real'][:3], RUN / 'logs/smoke.log')
for line in (RUN / 'smoke.jsonl').read_text().splitlines():
    r = json.loads(line)
    print(r['id'], '\\n', r['caption'], '\\n')
''')

md('## 6. Chạy toàn bộ Real + Render\nKhông lượng tử hóa. Dùng prompt gốc, temperature 0 và tối đa 1.024 token như mặc định repo.')
code('''
PREDICTIONS = {}
for split in SPLITS:
    out = RUN / f'OmniDiff_{split}' / f'OmniDiff_{split}.jsonl'
    started = time.time()
    evaluate(REPO / f'data/evaluation/prompt/OmniDiff_{split}_test.json', out,
             QUESTIONS[split], RUN / f'logs/eval_{split}.log')
    PREDICTIONS[split] = out
    print(f'{split}: đủ {len(QUESTIONS[split])} caption; cell mất {(time.time()-started)/60:.1f} phút.')
''')

md('## 7. Cài Java và tính điểm cả hai tập\nChỉ chấm khi đủ mọi ID và ID của reference khớp toàn bộ prediction. Điểm JSON là thang gốc; bảng CSV/báo cáo nhân 100.')
score_script = '''
import argparse, json
from pathlib import Path
from pycocotools.coco import COCO
from pycocoevalcap.tokenizer.ptbtokenizer import PTBTokenizer
from pycocoevalcap.bleu.bleu import Bleu
from pycocoevalcap.meteor.meteor import Meteor
from pycocoevalcap.rouge.rouge import Rouge
from pycocoevalcap.cider.cider import Cider

p = argparse.ArgumentParser()
p.add_argument('--reference', required=True)
p.add_argument('--prediction', required=True)
p.add_argument('--output', required=True)
a = p.parse_args()
rows = [json.loads(l) for l in Path(a.prediction).read_text().splitlines() if l.strip()]
ids = [r['image_id'] for r in rows]
assert len(ids) == len(set(ids)), 'Duplicate prediction IDs'
coco = COCO(a.reference)
assert set(ids) == set(coco.getImgIds()), 'Prediction/reference IDs do not match'
res = coco.loadRes([{'image_id': r['image_id'], 'caption': r['caption']} for r in rows])
tok = PTBTokenizer()
gts = tok.tokenize({i: coco.imgToAnns[i] for i in ids})
pred = tok.tokenize({i: res.imgToAnns[i] for i in ids})
out = {}
for scorer, names in [(Bleu(4), ['Bleu_1','Bleu_2','Bleu_3','Bleu_4']),
                      (Meteor(), ['METEOR']), (Rouge(), ['ROUGE_L']), (Cider(), ['CIDEr'])]:
    values, _ = scorer.compute_score(gts, pred)
    for key, val in zip(names, values if isinstance(values, list) else [values]):
        out[key] = float(val)
Path(a.output).write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=2))
'''
code('''
if shutil.which('java') is None:
    java_script = "import jdk; print(jdk.install('11', jre=True, path='/root/.m3diff-jdk'))"
    java_home = capture([PY, '-c', java_script]).splitlines()[-1]
    os.environ['PATH'] = str(Path(java_home) / 'bin') + os.pathsep + os.environ['PATH']
if shutil.which('java') is None:
    raise RuntimeError('Chưa cài được Java cho METEOR/PTBTokenizer.')
run(['java', '-version'])
''' + 'score_script = ' + repr(dedent(score_script).strip() + '\n') + '''
(CODE / 'score_baseline.py').write_text(score_script)
SCORES = {}
for split in SPLITS:
    assert len(completed(PREDICTIONS[split], QUESTIONS[split])) == len(QUESTIONS[split])
    score_path = RUN / f'OmniDiff_{split}' / 'scores.json'
    # Tính lại từ caption đã kiểm tra để không dùng nhầm scores cũ.
    run([PY, CODE / 'score_baseline.py',
         '--reference', REPO / f'data/evaluation/reference/OmniDiff_{split}.json',
         '--prediction', PREDICTIONS[split], '--output', score_path],
        cwd=REPO, log=RUN / f'logs/metrics_{split}.log')
    SCORES[split] = json.loads(score_path.read_text())
print('Đã chấm xong cả Real và Render.')
''')

md('## 8. Xuất bảng điểm, ví dụ và gói kết quả\nThông báo **HOÀN TẤT** chỉ xuất hiện sau khi đủ caption và chấm thành công cả hai tập. Gói ZIP không chứa weights/dataset.')
code('''
keys = ['Bleu_1', 'Bleu_2', 'Bleu_3', 'Bleu_4', 'METEOR', 'ROUGE_L', 'CIDEr']
with open(RUN / 'summary_x100.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['split', 'n_pairs'] + keys)
    w.writeheader()
    for split in SPLITS:
        w.writerow({'split': split, 'n_pairs': len(QUESTIONS[split]),
                    **{k: SCORES[split][k] * 100 for k in keys}})
report = ['# M³Diff — Kết quả tái lập baseline', '',
          f'Repo commit: `{REPO_COMMIT}`', f'GPU: {gpu}',
          'Thiết lập: BF16, không lượng tử hóa, temperature=0, beam=1, max_new_tokens=1024.',
          'Khởi tạo từ checkpoint M³Diff công bố; không fine-tune hoặc căn chỉnh ảnh.',
          'Scorer: pycocoevalcap BLEU, METEOR, ROUGE-L và CIDEr; không chạy SPICE.', '',
          '| Tập | Số cặp | BLEU-4 | METEOR | ROUGE-L | CIDEr |',
          '|---|---:|---:|---:|---:|---:|']
for split in SPLITS:
    s = SCORES[split]
    report.append(f"| {split} | {len(QUESTIONS[split])} | {s['Bleu_4']*100:.2f} | {s['METEOR']*100:.2f} | {s['ROUGE_L']*100:.2f} | {s['CIDEr']*100:.2f} |")
report += ['', 'Các điểm trong bảng được nhân 100. Không tự động khẳng định bằng kết quả paper.',
           'run_config.json ghi revision weights/dataset, hash prompt/reference/runner và cấu hình suy luận.',
           'environment_freeze.txt ghi thư viện; logs/ lưu log chạy.', '', '## Ví dụ caption']
examples = []
for split in SPLITS:
    rows = [json.loads(l) for l in PREDICTIONS[split].read_text().splitlines() if l.strip()]
    by_id = {r['id']: r for r in rows}
    for q in QUESTIONS[split][:5]:
        ex = {'split': split, 'id': q['id'], 'images': q['image'],
              'prompt': q['conversations'][0]['value'], 'caption': by_id[q['id']]['caption']}
        examples.append(ex)
        report += ['', f"### {split}: {q['id']}", ex['caption']]
(RUN / 'examples.json').write_text(json.dumps(examples, ensure_ascii=False, indent=2))
report_text = '\\n'.join(report) + '\\n'
(RUN / 'REPORT.md').write_text(report_text)
(RUN / 'SUCCESS.json').write_text(json.dumps({
    'completed_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'counts': {s: len(QUESTIONS[s]) for s in SPLITS}, 'scores': SCORES,
    'run_config_sha256': sha(RUN / 'run_config.json')}, indent=2))

bundle = RUN / 'm3diff_baseline_results.zip'
include = ['REPORT.md', 'summary_x100.csv', 'run_config.json', 'hf_revisions.json',
           'environment_freeze.txt', 'gpu.txt', 'repo_diff.patch', 'examples.json', 'SUCCESS.json']
with zipfile.ZipFile(bundle, 'w', zipfile.ZIP_DEFLATED) as z:
    for name in include:
        z.write(RUN / name, name)
    for folder in [CODE, RUN / 'logs'] + [RUN / f'OmniDiff_{s}' for s in SPLITS]:
        for p in folder.rglob('*'):
            if p.is_file() and '__pycache__' not in p.parts:
                z.write(p, p.relative_to(RUN))
from IPython.display import display, Markdown
display(Markdown(report_text))
print('HOÀN TẤT: baseline Real + Render đã chạy và chấm đủ.')
print('Tải gói kết quả trong Files:', bundle)
''')

nb = {'cells': cells, 'metadata': {'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'},
       'language_info': {'name': 'python', 'version': '3.12'}}, 'nbformat': 4, 'nbformat_minor': 5}
for i,c in enumerate(cells):
    c['id'] = f'baseline-{i:02d}'
out = ROOT / 'outputs' / 'm3diff-baseline-full.ipynb'
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding='utf-8')
print(f'Created {out}: {len(cells)} cells')
