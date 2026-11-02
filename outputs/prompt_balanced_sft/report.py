from pathlib import Path
import json,hashlib,zipfile
ROOT=Path(__file__).parent
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(n,v):(ROOT/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
scores=load(ROOT/'masked_assessments.json');preds=load(ROOT/'results/masked_predictions.json');assert len(preds)==len(scores['cases'])==72
for r,p in zip(scores['cases'],preds):
 assert r['id']==p['id']
 for c in [1,2]:assert r[f'candidate_{c}'] and r[f'candidate_{c}']['caption']==p[f'candidate_{c}']
key=load(ROOT/'results/mask_key.json');rubric=load(ROOT.parent/'invariance_sft/eval_rubric.json');rows=[]
for r,p in zip(scores['cases'],preds):
 for c in [1,2]:rows.append({**{k:p[k] for k in ['id','scene','cohort','split','condition']},'arm':key[p['id']][f'candidate_{c}'],**r[f'candidate_{c}']})
save('decoded_assessments.json',{'masked_score_sha256':hashlib.sha256((ROOT/'masked_assessments.json').read_bytes()).hexdigest(),'rows':rows});stats={}
for co in ['old','new','all']:
 for split in ['Real','Render','all']:
  for group in ['identity','transformed','natural']:
   selected=[r for r in rows if (co=='all' or r['cohort']==co) and (split=='all' or r['split']==split) and ((group=='identity' and r['condition']=='identity') or (group=='transformed' and r['condition'] not in ['identity','natural']) or (group=='natural' and r['condition']=='natural' and r['scene'] not in rubric['excluded_natural'].get(r['cohort'],[])))]
   out={}
   for a in ['baseline','balanced']:
    rs=[r for r in selected if r['arm']==a]
    out[a]={'n':len(rs),'physical_fp_pairs':sum(r['fp'] for r in rs),'illumination_inferences':sum(r['illum'] for r in rs),'identity_difference_pairs':sum(r['identity_diff'] for r in rs),'fact_hits':sum(len(r['facts']) for r in rs),'unsupported_pairs':sum(bool(r['unsupported']) for r in rs),'any_recorded_geometry_error':sum(bool(r['fp'] or r['illum'] or 'WRONG:' in r.get('note','')) for r in rs)}
    if group=='natural':out[a]['possible_facts']=sum(len(rubric['facts'][r['cohort']][r['scene']]) for r in rs)
   stats[f'{co}/{split}/{group}']=out
save('metrics.json',stats);checks={'new_physical_fp_decreases':stats['new/all/transformed']['balanced']['physical_fp_pairs']<stats['new/all/transformed']['baseline']['physical_fp_pairs']}
for co in ['old','new']:
 for split in ['Real','Render']:checks[f'{co}_{split}_facts_preserved']=stats[f'{co}/{split}/natural']['balanced']['fact_hits']>=stats[f'{co}/{split}/natural']['baseline']['fact_hits']
checks['new_unsupported_not_increased']=stats['new/all/natural']['balanced']['unsupported_pairs']<=stats['new/all/natural']['baseline']['unsupported_pairs']
decision={'fixed_factual_gate':checks,'passes':all(checks.values()),'selection_for_full_requires_prompt_probe_too':True,'limits':'One seed, development images and assistant labels. Same init/order but not identical dropout masks after question length changes.'};save('decision.json',decision)
lines=['# Đối chứng cân bằng10 cách hỏi','', 'Giữ nguyên256 ảnh/target/order và64 update LR2e-5, chỉ đổi phân phối câu hỏi của64 negative. Đã khớp khởi tạo LoRA/MDP và cả hai thứ tự epoch. Không khẳng định dropout mask giống nhau vì độ dài câu hỏi thay đổi.','', '| Nhóm | Baseline | Balanced |','|---|---:|---:|']
for k,label,f in [('new/all/transformed','Bịa thay vật,32 cặp','physical_fp_pairs'),('new/all/transformed','Lỗi vật/ánh sáng/camera,32 cặp','any_recorded_geometry_error'),('old/Real/natural','Fact cũ Real','fact_hits'),('old/Render/natural','Fact cũ Render','fact_hits'),('new/Real/natural','Fact mới Real','fact_hits'),('new/Render/natural','Fact mới Render','fact_hits')]:lines.append(f"| {label} | {stats[k]['baseline'][f]} | {stats[k]['balanced'][f]} |")
lines+=['', 'Gate factual đã định: '+('đạt' if decision['passes'] else 'chưa đạt')+'.', '', 'Phát hiện mất cân bằng template đến từ code/data trước khi đọc caption confirmation80. Chưa chứng minh model đã học shortcut; probe10 template kiểm tra riêng. Không thay nhãn sau khi mở khóa.127/144 nhãn trùng chính xác được tái dùng,17 câu mới đã chấm trước giải khóa. Trợ lý chấm, không phải người chấm độc lập.']
(ROOT/'KET_QUA.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
with zipfile.ZipFile(ROOT.parent/'m3diff_prompt_balanced_sft.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in ROOT.rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts and p.suffix in ['.py','.json','.jsonl','.txt','.log','.md']:z.write(p,str(p.relative_to(ROOT)))
print(json.dumps({'decision':decision,'new_geometry':stats['new/all/transformed'],'natural':stats['all/all/natural']},ensure_ascii=False,indent=2))
