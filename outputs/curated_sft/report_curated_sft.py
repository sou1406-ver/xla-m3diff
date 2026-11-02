"""CPU scoring, exact-loop ablation, clustered uncertainty and blinded visual audit."""
from pathlib import Path
import modal
HERE=Path(__file__).parent
app=modal.App('m3diff-curated-sft-analysis')
volume=modal.Volume.from_name('m3diff')
image=(modal.Image.debian_slim(python_version='3.10').apt_install('default-jre-headless')
 .pip_install('numpy==1.25.0','pycocoevalcap==1.2','pycocotools','Pillow==11.1.0')
 .add_local_file(str(HERE/'image_only_observations.json'),'/root/image_only_observations.json',copy=True)
 .add_local_file(str(HERE/'deduplicate_caption.py'),'/root/deduplicate_caption.py',copy=True))
RUN='curated_sft_v4'

@app.function(image=image,cpu=4,memory=8192,timeout=1800,volumes={'/mnt/m3diff':volume},scaledown_window=2)
def report():
 import json,csv,re,collections,zipfile,subprocess,sys,hashlib,random,statistics
 import numpy as np
 from pycocoevalcap.tokenizer.ptbtokenizer import PTBTokenizer
 from pycocoevalcap.cider.cider import Cider
 from PIL import Image,ImageOps,ImageDraw
 sys.path.insert(0,'/root');from deduplicate_caption import deduplicate_caption
 root=Path('/mnt/m3diff');out=root/RUN
 assert (out/'SUCCESS.json').exists(),'GPU experiment not complete'
 assert (out/'LORA_ONLY_SUCCESS.json').exists(),'LoRA-only ablation not complete'
 assert (out/'MATCHED_BASELINE_SUCCESS.json').exists(),'Matched A100 baseline not complete'
 def save(n,v):(out/n).write_text(json.dumps(v,ensure_ascii=False,indent=2))
 config=json.loads((out/'prepared.json').read_text());questions=json.loads((out/'eval_questions.json').read_text())
 (out/'image_only_observations.json').write_text(Path('/root/image_only_observations.json').read_text())
 expected_ids={q['id'] for q in questions};integrity={}
 for arm in ['original_labels','corrected_labels','corrected_lora_only','previous_random','matched_baseline']:
  rows=[json.loads(l) for l in (out/(arm+'.jsonl')).read_text().splitlines() if l.strip()]
  ids=[r['id'] for r in rows]
  assert len(ids)==len(set(ids))==len(expected_ids) and set(ids)==expected_ids,('Prediction integrity',arm)
  assert all(isinstance(r['caption'],str) for r in rows)
  integrity[arm]={'n':len(rows),'unique_ids':len(set(ids)),'expected_id_set_matches':True}
 save('prediction_integrity.json',integrity)
 controlled=['original_labels','corrected_labels','corrected_lora_only']
 initialization={a:json.loads((out/f'm3diff-{a}-lora/initialization_audit.json').read_text()) for a in controlled}
 orders={a:json.loads((out/f'm3diff-{a}-lora/sample_order.json').read_text()) for a in controlled}
 for a in controlled:
  assert sorted(orders[a])==list(range(216)),(a,'invalid sample order')
  assert all('lora_' in n or ('vision_resampler' in n and a!='corrected_lora_only') for n in initialization[a]['trainable_names'])
 for field in ['lora_initialization','MDP_initialization']:
  assert len({initialization[a][field]['sha256'] for a in controlled})==1,('Initialization differs',field)
 assert orders['original_labels']==orders['corrected_labels']==orders['corrected_lora_only'],'Actual sample orders differ'
 original=json.loads((out/'original_labels_train.json').read_text());corrected=json.loads((out/'corrected_labels_train.json').read_text())
 assert [(r['id'],r['image'],r['conversations'][0]) for r in original]==[(r['id'],r['image'],r['conversations'][0]) for r in corrected]
 assert corrected==json.loads((out/'corrected_lora_only_train.json').read_text())
 save('control_verification.json',{'matched_lora_initialization':True,'matched_MDP_initialization':True,
  'matched_actual_sample_order':True,'n_sampled_records':216,'same_images_prompts_and_input_order':True,
  'lora_initialization_sha256':initialization['original_labels']['lora_initialization']['sha256'],
  'MDP_initialization_sha256':initialization['original_labels']['MDP_initialization']['sha256'],
  'target_records_changed':sum(x['conversations'][-1]['value']!=y['conversations'][-1]['value'] for x,y in zip(original,corrected)),
  'trainable_parameters':{a:initialization[a]['trainable_parameters'] for a in controlled}})
 for name in ['run_config.json','hf_revisions.json','environment_freeze.txt','repo_diff.patch']:
  path=root/'baseline_reproduction_v1'/name
  if path.exists():(out/('baseline_'+name)).write_text(path.read_text())
 snapshot=out/'gpu_stage_metrics_cached_baseline.json'
 if not snapshot.exists():snapshot.write_text((out/'metrics.json').read_text())
 metrics=json.loads(snapshot.read_text())
 raw_arms=['baseline','cached_A10_baseline','previous_random','original_labels','corrected_labels','corrected_lora_only']
 arms=raw_arms+[a+'_dedup' for a in raw_arms]
 contrasts=[('corrected_labels','baseline'),('original_labels','baseline'),('corrected_labels','original_labels'),
  ('previous_random','baseline'),('baseline_dedup','baseline'),('corrected_labels_dedup','corrected_labels'),
  ('previous_random_dedup','baseline_dedup'),('corrected_labels_dedup','baseline_dedup'),
  ('corrected_lora_only','baseline'),('corrected_lora_only','corrected_labels'),
  ('corrected_lora_only_dedup','baseline_dedup'),('baseline','cached_A10_baseline')]
 intervals={};diagnostics={};per_pair=[];clean_metrics={}
 all_predictions={};dedup_audits=[]
 for split in ['Real','Render']:
  qs=[q for q in questions if q['split']==split]
  ref=json.loads((out/(split+'_reference.json')).read_text())
  g={r['id']:[] for r in ref['images']}
  for r in ref['annotations']:g[r['image_id']].append({'caption':r['caption']})
  cached_file=out/f'{split}_cached_A10_baseline.jsonl'
  if not cached_file.exists():cached_file.write_text((out/f'{split}_baseline.jsonl').read_text())
  metrics[split]['cached_A10_baseline']=metrics[split].pop('baseline')
  matched=[r for r in map(json.loads,(out/'matched_baseline.jsonl').read_text().splitlines()) if r['id'] in g]
  assert len(matched)==len({r['id'] for r in matched})==len(g)
  (out/f'{split}_baseline.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in matched))
  for arm in raw_arms:
   raw_file=out/f'{split}_{arm}.jsonl'
   if not raw_file.exists():
    rows=[r for r in map(json.loads,(out/(arm+'.jsonl')).read_text().splitlines()) if r['id'] in g]
    raw_file.write_text(''.join(json.dumps(r)+'\n' for r in rows))
   rows=[json.loads(l) for l in raw_file.read_text().splitlines() if l.strip()]
   assert {r['id'] for r in rows}==set(g)
   if arm not in metrics[split]:
    target=out/f'{split}_{arm}_scores.json'
    with open(out/'logs/lora_only_scoring.log','a') as log:
     subprocess.run([sys.executable,root/'baseline_reproduction_v1/code/score_baseline.py',
      '--reference',out/(split+'_reference.json'),'--prediction',raw_file,'--output',target],stdout=log,stderr=log,check=True)
    metrics[split][arm]=json.loads(target.read_text())
   fixed=[]
   for r in rows:
    cap,audit=deduplicate_caption(r['caption']);fixed.append({**r,'caption':cap})
    dedup_audits.append({'split':split,'arm':arm,'id':r['id'],**audit})
   predfile=out/f'{split}_{arm}_dedup.jsonl';predfile.write_text(''.join(json.dumps(r)+'\n' for r in fixed))
   target=out/f'{split}_{arm}_dedup_scores.json'
   with open(out/'logs/dedup_scoring.log','a') as log:
    subprocess.run([sys.executable,root/'baseline_reproduction_v1/code/score_baseline.py',
     '--reference',out/(split+'_reference.json'),'--prediction',predfile,'--output',target],stdout=log,stderr=log,check=True)
   metrics[split][arm+'_dedup']=json.loads(target.read_text())
  tokenizer=PTBTokenizer();g=tokenizer.tokenize(g);scores={};tokenized={}
  for arm in arms:
   rows=[json.loads(l) for l in (out/f'{split}_{arm}.jsonl').read_text().splitlines() if l.strip()]
   all_predictions.setdefault(split,{})[arm]={r['id']:r['caption'] for r in rows}
   h=tokenizer.tokenize({r['id']:[{'caption':r['caption']}] for r in rows});tokenized[arm]=h
   total,s=Cider().compute_score(g,h);scores[arm]=np.array(s)*100
   assert abs(total-metrics[split][arm]['CIDEr'])<1e-7
   repeats=[]
   for r in rows:
    counter=collections.Counter(s.strip().lower() for s in re.split(r'[.!?]+',r['caption']) if len(s.split())>=4)
    if max(counter.values(),default=0)>=3:repeats.append(r['id'])
   diagnostics[f'{split}/{arm}']={'repeat_3plus_count':len(repeats),'repeat_ids':repeats,
       'median_words':float(np.median([len(r['caption'].split()) for r in rows]))}
  # Connected components of shared image paths account for direct pair dependence.
  parent={}
  def find(x):
   parent.setdefault(x,x)
   if parent[x]!=x:parent[x]=find(parent[x])
   return parent[x]
  for q in qs:
   a,b=map(find,q['image']);parent[a]=b
  lookup={q['id']:find(q['image'][0]) for q in qs};groups={}
  for i,key in enumerate(g):groups.setdefault(lookup[key],[]).append(i)
  group_indices=list(groups.values());sizes=np.array([len(i) for i in group_indices])
  rng=np.random.default_rng(20261031)
  cluster_draw=rng.integers(0,len(group_indices),size=(10000,len(group_indices)))
  pair_draw=rng.integers(0,len(g),size=(10000,len(g)))
  intervals[split]={'n_pairs':len(g),'n_shared_image_components':len(groups),'component_sizes':list(map(int,sizes)),'contrasts':{}}
  for arm,other in contrasts:
   delta=scores[arm]-scores[other];sums=np.array([delta[i].sum() for i in group_indices])
   clustered=sums[cluster_draw].sum(axis=1)/sizes[cluster_draw].sum(axis=1)
   paired=delta[pair_draw].mean(axis=1)
   intervals[split]['contrasts'][arm+' minus '+other]={'delta_CIDEr_x100':float(delta.mean()),
    'cluster_bootstrap_95pct_CI':list(map(float,np.quantile(clustered,[.025,.975]))) if len(groups)>1 else None,
    'pair_bootstrap_95pct_CI':list(map(float,np.quantile(paired,[.025,.975])))}
  for i,key in enumerate(g):per_pair.append({'id':key,'split':split,'shared_image_component':lookup[key],
     **{arm:float(scores[arm][i]) for arm in arms}})
  clean_ids={q['id'] for q in qs if q['all_images_unseen_in_previous_pilots']}
  clean_g={k:v for k,v in g.items() if k in clean_ids};clean_metrics[split]={'n':len(clean_ids),'CIDEr_x100':{}}
  if len(clean_g)>1:
   for arm in arms:
    value,_=Cider().compute_score(clean_g,{k:tokenized[arm][k] for k in clean_g})
    clean_metrics[split]['CIDEr_x100'][arm]=float(value*100)
 save('metrics_with_dedup.json',metrics);save('cluster_bootstrap.json',intervals);save('diagnostics.json',diagnostics)
 save('metrics.json',{split:{arm:metrics[split][arm] for arm in raw_arms} for split in metrics})
 final_comparison=[]
 for q in questions:
  final_comparison.append({'id':q['id'],'split':q['split'],'images':q['image'],
   'all_images_unseen_in_previous_pilots':q['all_images_unseen_in_previous_pilots'],
   **{arm:all_predictions[q['split']][arm][q['id']] for arm in arms}})
 save('final_comparison.json',final_comparison)
 save('per_pair_cider.json',per_pair);save('image_clean_metrics.json',clean_metrics);save('dedup_audit.json',dedup_audits)
 (out/'deduplicate_caption.py').write_text(Path('/root/deduplicate_caption.py').read_text())
 save('dedup_provenance.json',{'sha256':hashlib.sha256(Path('/root/deduplicate_caption.py').read_bytes()).hexdigest(),
   'rule':'Remove exact whitespace-normalized repeated sentences, case-sensitive and quotation-aware; trim a final repeated prefix only after 2+ exact duplicates. No semantic paraphrasing or invented facts.',
   'planned_before_current_test_scores':'Local source fixed during GPU run before evaluation scores were inspected.'})
 with open(out/'summary_x100.csv','w') as f:
  w=csv.writer(f);w.writerow(['split','n','arm','Bleu_4','METEOR','ROUGE_L','CIDEr','repeat_3plus'])
  for split in metrics:
   for arm in arms:w.writerow([split,len([q for q in questions if q['split']==split]),arm,
     *[metrics[split][arm][m]*100 for m in ['Bleu_4','METEOR','ROUGE_L','CIDEr']],diagnostics[f'{split}/{arm}']['repeat_3plus_count']])
 # Blinded, fixed-seed comparison: baseline versus corrected-label SFT on image-clean pairs.
 audit=[];key={};rng=random.Random(20261031)
 for split in ['Real','Render']:
  pool=[q for q in questions if q['split']==split and q['all_images_unseen_in_previous_pilots']]
  rng.shuffle(pool)
  for q in pool[:8]:
   order=['baseline_dedup','corrected_labels_dedup','corrected_lora_only_dedup'];rng.shuffle(order);i=len(audit)
   audit.append({'index':i,'id':q['id'],'split':split,'images':q['image'],
    **{f'candidate_{j+1}':all_predictions[split][arm][q['id']] for j,arm in enumerate(order)}})
   key[q['id']]={f'candidate_{j+1}':arm for j,arm in enumerate(order)}
 save('blind_audit.json',audit);save('blind_key.json',key)
 if (out/'blind_image_selection.json').exists():
  assert [r['id'] for r in audit]==[r['id'] for r in json.loads((out/'blind_image_selection.json').read_text())]
 with zipfile.ZipFile(out/'blind_audit_images.zip','w',zipfile.ZIP_DEFLATED) as z:
  seen_images=set()
  for r in audit:
   sheet=Image.new('RGB',(1800,950),'#eeeeee');draw=ImageDraw.Draw(sheet)
   for k,rel in enumerate(r['images']):
    path=root/'baseline_cache/OmniDiff'/rel
    if rel not in seen_images:z.write(path,'originals/'+rel);seen_images.add(rel)
    im=ImageOps.contain(Image.open(path).convert('RGB'),(890,900));sheet.paste(im,(k*900+(890-im.width)//2,35+(900-im.height)//2))
    draw.text((k*900+10,8),f"AUDIT {r['index']:02d}  "+('BEFORE' if k==0 else 'AFTER'),fill='black')
   path=out/f"blind_{r['index']:02d}.jpg";sheet.save(path,quality=96);z.write(path,path.name)
 lines=['# SFT trên caption được rà ảnh','',
   '44 cặp train được trợ lý rà trực quan (22 Real, 22 Render), từ 48 ứng viên. Chưa có người gán nhãn độc lập xác nhận.',
   'Hai nhánh học cùng ảnh và thứ tự: 44 cặp x 2 lượt xuất hiện + 128 cặp replay = 216 bản ghi, một epoch, 27 optimizer update. Chỉ caption mục tiêu khác nhau.',
   'Đã kiểm tra hash LoRA và MDP trước train trùng nhau ở cả ba nhánh; thứ tự 216 chỉ số mẫu thực tế cũng trùng nhau. Seed42 đặt trước khi tạo model; tắt group_by_modality_length. Xem control_verification.json và initialization_audit.json/sample_order.json của từng model.',
   'Nhánh corrected_lora_only dùng đúng nhãn sửa/thứ tự/số bước, nhưng đóng băng MDP thay vì cập nhật MDP. Đã kiểm tra non_lora_trainables.bin rỗng để xác nhận không cập nhật trọng số ngoài LoRA.',
   'Nhãn sửa đồng thời thay đổi độ chi tiết và cách diễn đạt; đây không phải phép đo tách riêng độ chính xác ngữ nghĩa khỏi độ dài caption.',
   'Đánh giá trên 256 cặp chưa dùng ở các pilot chọn mẫu trước đó (128 mỗi miền). Baseline chính chạy lại trên họ GPU A100/BF16; mọi nhánh cùng yêu cầu A100-40GB, nhưng Modal cấp A100-SXM4-80GB cho lượt baseline. Đây là đối chiếu cùng họ A100, chưa kiểm chứng trùng SKU vật lý tuyệt đối. cached_A10_baseline giữ caption baseline cũ. Cả 128 cặp Real dùng ảnh chưa xem ở các pilot chọn mẫu; Render chỉ có 9 cặp như vậy. Các cặp còn lại có thể dùng ảnh đã xem trước, nhưng không đưa ảnh test vào train.',
   'Đây là nghiên cứu một seed, chưa bảo đảm tách scene. Nhánh previous_random có dữ liệu/số bước khác nên chỉ là đối chiếu thực dụng.',
   'Các nhánh _dedup chỉ loại câu lặp nguyên văn sau sinh, không cập nhật model. Điểm nhân 100; CIDEr cùng document frequency trong từng miền.','',
   '| Miền | Nhánh | BLEU-4 | METEOR | ROUGE-L | CIDEr | Lặp câu >=3 |',
   '|---|---|---:|---:|---:|---:|---:|']
 for split in metrics:
  for arm in arms:
   vals=[metrics[split][arm][m]*100 for m in ['Bleu_4','METEOR','ROUGE_L','CIDEr']]
   lines.append('| '+split+' | '+arm+' | '+' | '.join(f'{v:.2f}' for v in vals)+f" | {diagnostics[f'{split}/{arm}']['repeat_3plus_count']} |")
 lines+=['','## Bất định theo cụm ảnh chung','',
   'Bootstrap 10.000 lần theo thành phần liên thông ảnh chung; mỗi lần lấy lại các cụm rồi tính chênh lệch trung bình theo cặp. Cụm ảnh chung chưa nhất thiết bao trùm toàn bộ scene; không tính biến thiên giữa seed train.']
 for split,info in intervals.items():
  lines.append(f"\n{split}: {info['n_pairs']} cặp, {info['n_shared_image_components']} cụm.")
  for name,d in info['contrasts'].items():
   ci=d['cluster_bootstrap_95pct_CI'];txt=f'[{ci[0]:+.2f}, {ci[1]:+.2f}]' if ci else 'không ước lượng được'
   lines.append(f"- {name}: {d['delta_CIDEr_x100']:+.2f}; CI95% {txt}.")
 lines+=['','## Tệp kiểm tra','',
   'annotations.json và review_manifest.json ghi nhãn gốc, caption baseline, nhãn sửa và bằng chứng cho 48 cặp train.',
   'final_comparison.json dùng baseline A100 khớp phần cứng; comparison.json từ bước GPU ban đầu còn giữ baseline A10 cũ. Dùng final_comparison.json khi đọc báo cáo cuối.',
   'blind_audit.json và blind_audit_images.zip: 16 cặp test dùng ảnh mới, baseline và cả hai nhánh SFT nhãn sửa đều đã qua cùng bộ lọc lặp rồi được xáo thứ tự. Đánh giá nói sai và bỏ sót riêng; blind_key.json là khóa giải sau khi chấm trực quan.',
   'image_clean_metrics.json chấm lại từng nhánh trên nhóm ảnh mới. Không so CIDEr giữa tập con này và toàn bộ 128 cặp vì document frequency khác nhau.',
   'Trọng số lưu trên Volume m3diff/curated_sft_v4/m3diff-original_labels-lora, m3diff-corrected_labels-lora và m3diff-corrected_lora_only-lora. GPU được giải phóng khi mỗi function experiment trả về.']
 (out/'REPORT.md').write_text('\n'.join(lines)+'\n')
 with zipfile.ZipFile(out/'curated_sft_results.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in out.rglob('*'):
   if p.is_file() and p.suffix in ['.json','.jsonl','.log','.py','.md','.csv','.txt','.patch'] and p.stat().st_size<20_000_000:z.write(p,str(p.relative_to(out)))
 volume.commit();print('\n'.join(lines),flush=True)

@app.local_entrypoint()
def main():report.remote()
