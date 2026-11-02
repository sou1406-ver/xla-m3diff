"""Separate cached cross-job comparisons from same-GPU cap controls."""
from pathlib import Path
import json,itertools,statistics
HERE=Path(__file__).parent
def read(p):return json.loads(p.read_text(encoding='utf8'))
def jsonl(p):return [json.loads(l) for l in p.read_text(encoding='utf8').splitlines() if l.strip()]
def prefix(a,b):return len(list(itertools.takewhile(lambda pair:pair[0]==pair[1],zip(a.split(),b.split()))))
def cap_hit(r):return r['generated_token_slots']>=r['max_new_tokens'] and r['last_token_id']!=r['tokenizer_eos_token_id']
audits=[];changed=[]
for name,folder,cap in [('LoRA256','results',256),('base256','base256_results',256),('base128','base128_results',128)]:
 root=HERE/folder
 if not (root/'SUCCESS.json').exists():continue
 status=read(root/'SUCCESS.json');rows=read(root/'comparison.json');natural=[r for r in rows if '__natural' in r['id']];long=[r for r in rows if '__natural' not in r['id']]
 assert len(rows)==status['n_completed'] and len({r['id'] for r in rows})==len(rows)
 audit={'probe':name,'cap':cap,'status':status,'natural_n':len(natural),'natural_exact_match_cached_cross_job':sum(r['exact_cached_match'] for r in natural),'natural_cap_hit_ids':[r['id'] for r in natural if cap_hit(r)],'long_cases':[{'id':r['id'],'cached1024_words':len(r['cached_1024'].split()),'capped_words':len(r['caption'].split()),'common_prefix_words_vs_cache':prefix(r['cached_1024'],r['caption']),'cap_hit':cap_hit(r),'token_slots':r['generated_token_slots']} for r in long],'cached_comparison_limit':'Natural cached captions came from earlierA100 pilot; these probes useA10/A10G. Differences below cap cannot be attributed to truncation. Long cached references came from earlier full runs, not the same model instance.'}
 control_path=root/'same_GPU_1024_controls.jsonl'
 if control_path.exists():
  controls={r['id']:r for r in jsonl(control_path)}
  matched=[r for r in natural if r['id'] in controls]
  audit['same_GPU_natural']={'n':len(matched),'exact_caption_matches':sum(r['caption']==controls[r['id']]['caption'] for r in matched),'changed_ids':[r['id'] for r in matched if r['caption']!=controls[r['id']]['caption']],'controls_token_slots':{r['id']:controls[r['id']]['generated_token_slots'] for r in matched},'all_controls_ended_before_1024':all(controls[r['id']]['generated_token_slots']<1024 for r in matched)}
  for r in matched:
   c=controls[r['id']]
   if r['caption']!=c['caption']:changed.append({'id':r['id'],'control1024':c['caption'],'candidate128':r['caption'],'control_token_slots':c['generated_token_slots'],'candidate_token_slots':r['generated_token_slots'],'candidate_hit_cap':cap_hit(r),'common_prefix_words':prefix(c['caption'],r['caption'])})
  timing=jsonl(root/'paired_timings.jsonl');paired=[r for r in timing if r['control1024_seconds'] is not None]
  audit['paired_timing']={'n_natural':len(paired),'control1024_median_seconds':statistics.median(r['control1024_seconds'] for r in paired),'candidate_median_seconds':statistics.median(r['candidate_seconds'] for r in paired),'limits':'Natural controls only; control always first. No same-GPU1024 timing for long cases. Caption JSON generation_seconds for base128 includes both calls; use paired_timings instead.'}
 audits.append(audit)
result={'probes':audits,'changed_natural_vs_same_GPU':changed,'deployment_default_max_new_tokens':1024,'full_benchmark_scores_unchanged':True,'no_retraining_performed':True,'limits':'Known natural/failure cases, not heldout unbiased quality evaluation. Token cap bounds generated length, not factuality or model vision understanding.'}
(HERE/'CAP_AUDIT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
lines=['# Thử giới hạn độ dài caption','', 'Thử nghiệm sau benchmark, không đổi điểm full hoặc mặc định1024 token. Không train thêm. Các ca dài được chọn từ lỗi đã biết, không phải mẫu ngẫu nhiên.','', '| Bản | Số ca | Natural khớp cache cũ | Natural chạm cap | Ca dài chạm cap |','|---|---:|---:|---:|---:|']
for a in audits:lines.append(f'| {a["probe"]} | {a["status"]["n_completed"]} | {a["natural_exact_match_cached_cross_job"]}/{a["natural_n"]} | {len(a["natural_cap_hit_ids"])} | {sum(r["cap_hit"] for r in a["long_cases"])}/{len(a["long_cases"])} |')
lines += ['','Cache natural cũ chạyA100, lượt mớiA10/A10G. Không dùng sự khác nhau với cache đó để kết luận giới hạn token làm mất fact. Không có timing1024 cùng lượt cho các ca dài nên không khẳng định hệ số tăng tốc.','']
for a in audits:
 if 'same_GPU_natural' in a:
  g=a['same_GPU_natural'];lines += [f'Đối chứng cùng model/GPU: {g["exact_caption_matches"]}/{g["n"]} caption natural ở128 token khớp hoàn toàn lượt1024 ngay trước đó. Các ca khác được lưu trong `CAP_AUDIT.json` để xem phần bị cắt.','']
lines += ['Giới hạn token là tùy chọn vận hành, không sửa nhận diện xoay/zoom hoặc câu bịa. Giữ mặc định1024 cho tái lập; nếu chọn cap nhỏ cho demo cần chấp nhận khả năng thiếu mô tả.','']
(HERE/'KET_QUA.md').write_text('\n'.join(lines),encoding='utf8');print(json.dumps(result,ensure_ascii=False,indent=2))
