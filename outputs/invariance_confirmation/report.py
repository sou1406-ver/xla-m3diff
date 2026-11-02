"""Report the fixed new-pair experiment after saving every masked annotation."""
from pathlib import Path
import json,hashlib,zipfile
ROOT=Path(__file__).parent
def load(n):return json.loads((ROOT/n).read_text(encoding='utf-8-sig'))
def save(n,v):(ROOT/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
scores=load('masked_assessments.json');preds=load('results/masked_predictions.json');rubric=load('eval_rubric.json')
assert len(scores['cases'])==len(preds)==80
for r,p in zip(scores['cases'],preds):
 assert r['id']==p['id']
 for c in [1,2,3]:assert r[f'candidate_{c}'] and r[f'candidate_{c}']['caption']==p[f'candidate_{c}']
key=load('results/mask_key.json');rows=[]
for r,p in zip(scores['cases'],preds):
 for c in [1,2,3]:rows.append({**{k:p[k] for k in ['id','cohort','scene','split','condition']},'arm':key[p['id']][f'candidate_{c}'],**r[f'candidate_{c}']})
save('decoded_assessments.json',{'masked_score_sha256':hashlib.sha256((ROOT/'masked_assessments.json').read_bytes()).hexdigest(),'rows':rows})
arms=['baseline','positive_control','mixed_objective'];stats={}
for subset in ['all_pairs','unfamiliar_backgrounds']:
 for domain in ['Real','Render','all']:
  for group in ['identity','transformed','natural']:
   selected=[r for r in rows if (subset=='all_pairs' or r['scene'] in rubric['unseen_in_prior_diagnostic_backgrounds']) and (domain=='all' or r['split']==domain) and ((group=='identity' and r['condition']=='identity') or (group=='transformed' and r['condition'] not in ['identity','natural']) or (group=='natural' and r['condition']=='natural'))]
   out={}
   for a in arms:
    rs=[r for r in selected if r['arm']==a]
    out[a]={'n':len(rs),'physical_fp_pairs':sum(r['fp'] for r in rs),'illumination_inferences':sum(r['illum'] for r in rs),'identity_difference_pairs':sum(r['identity_diff'] for r in rs),'camera_acknowledged':sum(r['ack'] for r in rs),'wrong_geometry_explanations':sum(r.get('wrong_geometry',0) for r in rs),'fact_hits':sum(len(r['facts']) for r in rs),'unsupported_pairs':sum(bool(r['unsupported']) for r in rs),'suppressed_natural_pairs':sum(r['suppression'] for r in rs),'any_recorded_geometry_error':sum(bool(r['fp'] or r['illum'] or r.get('wrong_geometry')) for r in rs)}
    if group=='natural':out[a]['possible_facts']=sum(len(rubric['facts'][r['scene']]) for r in rs)
   stats[f'{subset}/{domain}/{group}']=out
save('metrics.json',stats);checks={}
for a in arms[1:]:
 ch={'physical_fp_decreases':stats['all_pairs/all/transformed'][a]['physical_fp_pairs']<stats['all_pairs/all/transformed']['baseline']['physical_fp_pairs']}
 for d in ['Real','Render']:ch[d+'_natural_facts_preserved']=stats[f'all_pairs/{d}/natural'][a]['fact_hits']>=stats[f'all_pairs/{d}/natural']['baseline']['fact_hits']
 ch['natural_unsupported_not_increased']=stats['all_pairs/all/natural'][a]['unsupported_pairs']<=stats['all_pairs/all/natural']['baseline']['unsupported_pairs']
 checks[a]={'checks':ch,'passes':all(ch.values())}
save('decision.json',{'fixed_gate':checks,'limits':rubric['limits'],'mixed_selected_before_this_run':True,'do_not_relabel_or_tune_on_confirmation':True})
lines=['# Xác nhận trên16 cặp ảnh khác','', 'Baseline và hai LoRA chạy80 cặp/240 caption cùng A10, prompt gốc, greedy1024. Có48 biến thể xoay/zoom,16 identity và16 tự nhiên. Đã loại trùng RGB với ảnh train/diagnostic/gallery và khóa fact trước inference.','', '**11/16 cặp vẫn cùng background đã xem.** Chỉ5 background Real chưa có trong diagnostic; Render không có background lạ. Render00/04 và01/05 còn chia sẻ background trong bộ này. Không gọi đây là16 scene độc lập chưa thấy.','', '| Nhóm | Baseline | Chỉ loss positive | Thêm loss không đổi |','|---|---:|---:|---:|']
for k,label,f in [('all_pairs/all/transformed','Bịa vật,48 cặp','physical_fp_pairs'),('all_pairs/all/transformed','Có lỗi vật/ánh sáng/giải thích hình học,48 cặp','any_recorded_geometry_error'),('all_pairs/all/identity','Bịa khác biệt,16 identity','identity_difference_pairs'),('all_pairs/Real/natural','Fact đúng Real','fact_hits'),('all_pairs/Render/natural','Fact đúng Render','fact_hits'),('all_pairs/all/natural','Cặp tự nhiên có chi tiết sai','unsupported_pairs'),('unfamiliar_backgrounds/Real/transformed','Bịa vật ở5 background Real lạ,15 cặp','physical_fp_pairs'),('unfamiliar_backgrounds/Real/natural','Fact đúng ở5 background Real lạ','fact_hits')]:lines.append('| '+label+' | '+' | '.join(str(stats[k][a][f]) for a in arms)+' |')
lines+=['', 'Kết quả gate cố định: '+json.dumps({a:v['passes'] for a,v in checks.items()})+'.','', 'Nhãn do trợ lý chấm, không phải người chấm độc lập; từng caption và phần chưa chắc được giữ nguyên trước mở khóa. Một seed, augmentation2D, cùng dataset và scene lặp; cần benchmark rộng và/hoặc thêm seed để đánh giá độ ổn định. Không thay ngưỡng sau xem kết quả.']
(ROOT/'KET_QUA.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
with zipfile.ZipFile(ROOT.parent/'m3diff_invariance_confirmation.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in ROOT.rglob('*'):
  if p.is_file() and '__pycache__' not in p.parts and p.suffix in ['.py','.json','.jsonl','.md','.log','.txt','.jpg']:z.write(p,str(p.relative_to(ROOT)))
print(json.dumps({'checks':checks,'geometry':stats['all_pairs/all/transformed'],'natural':stats['all_pairs/all/natural'],'unfamiliar':stats['unfamiliar_backgrounds/Real/transformed']},ensure_ascii=False,indent=2))
