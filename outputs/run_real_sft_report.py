"""CPU-only final analysis; run after run_real_sft_modal.py succeeds."""
from pathlib import Path
import modal
app=modal.App('m3diff-real-sft-report')
volume=modal.Volume.from_name('m3diff')
image=(modal.Image.debian_slim(python_version='3.10').apt_install('default-jre-headless')
       .pip_install('numpy==1.25.0','pycocoevalcap==1.2','pycocotools'))

@app.function(image=image,cpu=4,memory=8192,timeout=600,volumes={'/mnt/m3diff':volume},scaledown_window=2)
def report():
    import json,csv,re,collections,zipfile
    import numpy as np
    from pycocoevalcap.tokenizer.ptbtokenizer import PTBTokenizer
    from pycocoevalcap.cider.cider import Cider
    out=Path('/mnt/m3diff/real_sft_pilot_v1')
    assert (out/'SUCCESS.json').exists(),'Experiment has not completed'
    metrics=json.loads((out/'metrics.json').read_text())
    arms=['baseline','old_ft','random_sft','hard_sft'];details={};intervals={};per_pair=[]
    for split in ['Real','Render']:
        refs=json.loads((out/(split+'_reference.json')).read_text())
        g={r['id']:[] for r in refs['images']}
        for r in refs['annotations']:g[r['image_id']].append({'caption':r['caption']})
        tokenizer=PTBTokenizer();g=tokenizer.tokenize(g);scores={}
        for arm in arms:
            rows=[json.loads(l) for l in (out/f'{split}_{arm}.jsonl').read_text().splitlines() if l.strip()]
            h=tokenizer.tokenize({r['id']:[{'caption':r['caption']}] for r in rows})
            total,s=Cider().compute_score(g,h);scores[arm]=np.array(s)*100
            assert abs(total-metrics[split][arm]['CIDEr'])<1e-7
            reps=[]
            for r in rows:
                counter=collections.Counter(s.strip().lower() for s in re.split(r'[.!?]+',r['caption']) if len(s.split())>=4)
                if max(counter.values(),default=0)>=3:reps.append(r['id'])
            details[f'{split}/{arm}']={'repeat_3plus_count':len(reps),'repeat_ids':reps,
                'median_words':float(np.median([len(r['caption'].split()) for r in rows]))}
        rng=np.random.default_rng(20261029);indices=rng.integers(0,len(g),size=(10000,len(g)))
        intervals[split]={}
        for arm,other in [('old_ft','baseline'),('random_sft','baseline'),('hard_sft','baseline'),('hard_sft','random_sft')]:
            delta=scores[arm]-scores[other];samples=delta[indices].mean(axis=1)
            intervals[split][arm+' minus '+other]={'delta_CIDEr_x100':float(delta.mean()),
                'paired_bootstrap_95pct_CI':list(map(float,np.quantile(samples,[.025,.975])))}
        for i,key in enumerate(g):
            per_pair.append({'id':key,'split':split,**{arm:float(scores[arm][i]) for arm in arms},
                             'hard_minus_baseline':float(scores['hard_sft'][i]-scores['baseline'][i])})
    (out/'diagnostics.json').write_text(json.dumps(details,indent=2))
    (out/'bootstrap.json').write_text(json.dumps(intervals,indent=2))
    (out/'per_pair_cider.json').write_text(json.dumps(per_pair,indent=2))
    with open(out/'summary_x100.csv','w') as f:
        w=csv.writer(f);w.writerow(['split','arm','n','Bleu_4','METEOR','ROUGE_L','CIDEr','repeat_3plus'])
        for split in metrics:
            for arm in arms:w.writerow([split,arm,32,*[metrics[split][arm][m]*100 for m in ['Bleu_4','METEOR','ROUGE_L','CIDEr']],details[f'{split}/{arm}']['repeat_3plus_count']])
    lines=['# Pilot SFT trên ảnh thật','',
       '64 cặp test cố định: 32 Real, 32 Render. Điểm dưới đây nhân 100; CIDEr dùng document frequency của từng tập con 32 cặp.',
       'Không so trực tiếp CIDEr ở đây với lần full test hoặc tập con khác. Không dùng test để chọn mẫu train.','',
       '| Miền | Nhánh | BLEU-4 | METEOR | ROUGE-L | CIDEr | Cặp lặp câu ≥3 lần |',
       '|---|---|---:|---:|---:|---:|---:|']
    for split in metrics:
        for arm in arms:
            vals=[metrics[split][arm][m]*100 for m in ['Bleu_4','METEOR','ROUGE_L','CIDEr']]
            lines.append('| '+split+' | '+arm+' | '+' | '.join(f'{v:.2f}' for v in vals)+f" | {details[f'{split}/{arm}']['repeat_3plus_count']} |")
    lines+=['','## Chênh lệch CIDEr và bất định','',
       'Bootstrap ghép cặp 10.000 lần trên điểm CIDEr từng cặp, giữ nguyên document frequency của tập con. Khoảng này không tính phụ thuộc giữa các cặp chung scene hay biến thiên giữa các seed train.']
    for split,contrasts in intervals.items():
        for name,d in contrasts.items():
            lo,hi=d['paired_bootstrap_95pct_CI']
            lines.append(f"- {split}, {name}: {d['delta_CIDEr_x100']:+.2f}, CI 95% [{lo:+.2f}, {hi:+.2f}].")
    lines+=['','## Phạm vi','',
       'Hai nhánh mới học 256 cặp/nhánh, một epoch, LoRA r16/alpha32, MDP trainable, vision/projector frozen, LR 1e-5. Nhánh hard chọn 128 mẫu có train-CIDEr thấp; nhánh random chọn 128 ngẫu nhiên từ cùng nhóm ứng viên. Cùng 128 mẫu replay, cùng seed và số optimizer update. Các mẫu chính của hai nhánh có thể trùng một phần.',
       'Checkpoint gốc đã học dữ liệu gốc; đây là continued SFT, không phải bộ nhãn mới. Train/ảnh test không trùng đường dẫn; chưa bảo đảm tách scene. Mẫu khó tự động chưa được con người xác minh đầy đủ. Một pilot nhỏ không chứng minh cải thiện khả năng chống xoay góc/zoom; cần bộ đánh giá riêng cho từng yếu tố đó.',
       'Checkpoint fine-tune cũ khác cả dữ liệu, rank và tham số train nên chỉ là đối chiếu thực dụng, không dùng riêng chênh lệch đó để quy nguyên nhân cho dữ liệu tổng hợp.',
       'Caption đầy đủ: comparison.json. Trọng số nằm trên Volume, các thư mục m3diff-random_sft-lora và m3diff-hard_sft-lora. Không tạo dịch vụ hoặc lịch GPU thường trực.']
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n')
    with zipfile.ZipFile(out/'real_sft_results.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in out.rglob('*'):
            if p.is_file() and p.suffix in ['.json','.jsonl','.log','.py','.md','.csv'] and p.stat().st_size<20_000_000:
                z.write(p,str(p.relative_to(out)))
    volume.commit();print('\n'.join(lines));return intervals

@app.local_entrypoint()
def main():report.remote()
