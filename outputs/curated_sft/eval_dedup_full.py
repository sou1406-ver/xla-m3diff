"""CPU-only full-test evaluation of the already locked exact-sentence deduper."""
from pathlib import Path
import modal
app=modal.App('m3diff-full-test-exact-dedup')
volume=modal.Volume.from_name('m3diff')
image=(modal.Image.debian_slim(python_version='3.10').apt_install('default-jre-headless')
 .pip_install('numpy==1.25.0','pycocoevalcap==1.2','pycocotools')
 .add_local_file(str(Path(__file__).with_name('deduplicate_caption.py')),'/root/deduplicate_caption.py',copy=True))

@app.function(image=image,cpu=4,memory=8192,timeout=1800,volumes={'/mnt/m3diff':volume},scaledown_window=2)
def evaluate():
 import json,sys,subprocess,hashlib,zipfile,csv,collections,re
 import numpy as np
 from pycocoevalcap.tokenizer.ptbtokenizer import PTBTokenizer
 from pycocoevalcap.cider.cider import Cider
 sys.path.insert(0,'/root');from deduplicate_caption import deduplicate_caption
 root=Path('/mnt/m3diff');base=root/'baseline_reproduction_v1';out=root/'dedup_full_baseline_v1';out.mkdir(exist_ok=True)
 metrics={};audits=[];contrast={}
 for split,n in [('Real',803),('Render',767)]:
  rows=[json.loads(l) for l in (base/f'OmniDiff_{split}/OmniDiff_{split}.jsonl').read_text().splitlines() if l.strip()]
  assert len(rows)==n;fixed=[]
  for r in rows:
   cap,audit=deduplicate_caption(r['caption']);fixed.append({**r,'caption':cap});audits.append({'id':r['id'],'split':split,**audit})
  pred=out/f'{split}_dedup.jsonl';pred.write_text(''.join(json.dumps(r)+'\n' for r in fixed))
  ref=base/f'repo/data/evaluation/reference/OmniDiff_{split}.json';target=out/f'{split}_dedup_scores.json'
  with open(out/f'{split}_scoring.log','w') as log:
   subprocess.run([sys.executable,base/'code/score_baseline.py','--reference',ref,'--prediction',pred,'--output',target],check=True,stdout=log,stderr=log)
  metrics[split]={'baseline':json.loads((base/f'OmniDiff_{split}/scores.json').read_text()),'dedup':json.loads(target.read_text())}
  reference=json.loads(ref.read_text());g={r['id']:[] for r in reference['images']}
  for r in reference['annotations']:g[r['image_id']].append({'caption':r['caption']})
  tok=PTBTokenizer();g=tok.tokenize(g);per={}
  for arm,rs in [('baseline',rows),('dedup',fixed)]:
   total,s=Cider().compute_score(g,tok.tokenize({r['id']:[{'caption':r['caption']}] for r in rs}));per[arm]=np.array(s)*100
   assert abs(total-metrics[split][arm]['CIDEr'])<1e-7
  delta=per['dedup']-per['baseline'];rng=np.random.default_rng(20261031)
  means=np.array([rng.choice(delta,size=len(delta),replace=True).mean() for _ in range(10000)])
  contrast[split]={'n':n,'changed':sum(a['split']==split and a['changed'] for a in audits),
   'delta_CIDEr_x100':float(delta.mean()),'pair_bootstrap_95pct_CI':list(map(float,np.quantile(means,[.025,.975]))),
   'pair_bootstrap_limitation':'Does not account for image/scene dependence or training-seed variation.'}
  print('FULL',split,json.dumps(metrics[split]),json.dumps(contrast[split]),flush=True)
 source=Path('/root/deduplicate_caption.py').read_text();(out/'deduplicate_caption.py').write_text(source)
 config={'source_sha256':hashlib.sha256(source.encode()).hexdigest(),'n_total':1570,
  'operation':'Exact repeated-sentence removal on cached published-checkpoint baseline captions; no GPU, no model changes, no semantic rewriting.',
  'rule_locked_before_full_test_scores':True,'limitations':'Does not fix incorrect visual claims or establish viewpoint/zoom robustness.'}
 for name,obj in [('metrics.json',metrics),('audit.json',audits),('contrast.json',contrast),('run_config.json',config)]:
  (out/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2))
 lines=['# Loại câu lặp trên toàn bộ OmniDiff test','',
  'Chỉ hậu xử lý caption baseline đã sinh: loại câu lặp nguyên văn. Không train hay gọi lại model, không dùng LocateAnything.',
  'Quy tắc đã cố định trước khi xem điểm full test. Điểm nhân 100.','',
  '| Miền | Nhánh | BLEU-4 | METEOR | ROUGE-L | CIDEr | Caption thay đổi |',
  '|---|---|---:|---:|---:|---:|---:|']
 with open(out/'summary_x100.csv','w') as f:
  w=csv.writer(f);w.writerow(['split','arm','n','Bleu_4','METEOR','ROUGE_L','CIDEr','changed'])
  for split in metrics:
   for arm in ['baseline','dedup']:
    vals=[metrics[split][arm][m]*100 for m in ['Bleu_4','METEOR','ROUGE_L','CIDEr']]
    n=contrast[split]['changed'] if arm=='dedup' else 0
    lines.append('| '+split+' | '+arm+' | '+' | '.join(f'{x:.3f}' for x in vals)+f' | {n} |')
    w.writerow([split,arm,contrast[split]['n'],*vals,n])
 lines+=['','Đây là cải thiện ở pipeline đầu ra nếu điểm tăng; không phải bằng chứng model hiểu ảnh tốt hơn. Caption bịa vật, nhầm xoay góc hay zoom vẫn có thể tồn tại.','',
  'contrast.json có bootstrap theo cặp, chưa xét phụ thuộc giữa các cặp chung ảnh/scene. audit.json ghi chính xác caption nào bị sửa.']
 (out/'REPORT.md').write_text('\n'.join(lines)+'\n');(out/'SUCCESS.json').write_text(json.dumps({'n':1570,'cpu_only':True}))
 with zipfile.ZipFile(out/'dedup_full_results.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in out.iterdir():
   if p.is_file() and p.suffix in ['.json','.jsonl','.csv','.md','.py','.log']:z.write(p,p.name)
 volume.commit();print('\n'.join(lines),flush=True)

@app.local_entrypoint()
def main():evaluate.remote()
