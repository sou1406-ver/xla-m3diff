"""Local CPU-only completion collection. Never starts inference or new GPU jobs."""
from pathlib import Path
import json,time,subprocess,sys,dataclasses,hashlib
from datetime import datetime,timezone
from decimal import Decimal as D
import modal
H=Path(__file__).parent;P=H/'camera240';V=modal.Volume.from_name('m3diff');REMOTE='/mbr_pilot_20261103/camera240/'
def get(n):
 try:data=b''.join(V.read_file(REMOTE+n))
 except FileNotFoundError:return None
 (P/n).write_bytes(data);return json.loads(data) if n.endswith('.json') else data
started=time.time()
while time.time()-started<4800:
 done=get('PIPELINE_DONE.json')
 if done:break
 (P/'LOCAL_FINALIZER_WATCH.json').write_text(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'read_only_wait':True}));time.sleep(30)
else:raise RuntimeError('No pipeline completion by collector deadline; no retry')
gen=get('GEN_DONE.json')
if done['status']!='COMPLETE_SCORED' and gen and gen.get('complete'):
 # CPU correction is announced and recorded before generation ends. No GPU retry.
 assert not (P/'LOCAL_CPU_FIX_DISPATCH.json').exists()
 (P/'LOCAL_CPU_FIX_DISPATCH.json').write_text(json.dumps({'time':time.time(),'reason':'missing cv2 indirect import in original CPU image','unchanged_scorer':True,'gpu':False}))
 subprocess.run([sys.executable,'-X','utf8','-m','modal','run',str(H/'camera_score_cpu.py')],check=True)
 done=get('FINAL_OUTCOME.json');assert done['status']=='COMPLETE_SCORED'
for n in ['GPU_ATTEMPT.json','ATTEMPT.json','GPU_DONE.json','GEN_DONE.json','GENERATION_AUDIT.json','PROGRESS.json','results.jsonl','SELECTION.json','base.jsonl','mbr.jsonl','REVIEW_240.csv','METRICS.json','generation.log','CPU_DEPENDENCY_FIX_ATTEMPT.json']:get(n)
get('FINAL_OUTCOME.json')
raw=[json.loads(l) for l in (P/'results.jsonl').read_text().splitlines()];qs=json.loads((P/'questions.json').read_text())
assert len(raw)==240 and [r['id'] for r in raw]==[q['id'] for q in qs]
for r in raw:
 assert len(r['methods']['batch8']['samples'])==8
 assert r['methods']['batch8']['seed']==20261105+int(hashlib.sha256(r['id'].encode()).hexdigest()[:8],16)%1000000
assert hashlib.sha256((H/'camera240_score.py').read_bytes()).hexdigest()==json.loads((P/'ADMISSION.json').read_text())['code_sha256']['camera240_score.py']
s=modal.Workspace.from_context().billing.summary(cycle='2026-11');cost=max(abs(s.adjustments['Credits']),s.metered_cost+sum(v for k,v in s.adjustments.items() if k!='Credits'))
gpu=json.loads((P/'GPU_DONE.json').read_text());upper=D(str(gpu['gpu_worker_seconds']))*D('1.5452')/D(3600)+D('.15')
remaining=D(30)-max(cost,D('26.09')+upper)
snapshot={'utc':datetime.now(timezone.utc).isoformat(),'billing':dataclasses.asdict(s),'api_consumption':str(cost),'credit_remaining_estimate':str(D(30)-cost),'camera_conservative_cost_upper':str(upper),'credit_remaining_guarded':str(remaining),'not_final_invoice':True}
(P/'FINAL_BILLING.json').write_text(json.dumps(snapshot,default=str,indent=2))
# Never infer safety from delayed billing. Use measured whole camera generation,
# allow 25% extra runtime for600 plus setup; this is an estimate, not a hard bound.
forecast=D(str(gen['wall_seconds']))*D(600)/D(240)*D('1.25')*D('1.5452')/D(3600)+D('.20')
conditional={'remaining_guarded':str(remaining),'camera_based_synth600_cost_estimate_with_25pct_margin':str(forecast),'status':'NOT_ADMITTED_REQUIRE_SEPARATE_BOUNDED_RUN' if remaining>=D('2.5') and forecast<=remaining-D('.5') else 'STOP_INSUFFICIENT_SAFE_CREDIT','synthetic600_run':False,'reason':'Both remaining>=2.5 and estimatedcost+0.5buffer must fit; no automatic unbounded GPU job.'}
(P/'SYNTH600_DECISION.json').write_text(json.dumps(conditional,indent=2))
metrics=json.loads((P/'METRICS.json').read_text());b=metrics['greedy'];m=metrics['MBR']
report=f'''# Camera240: matched greedy versus MBR

Đủ240 cặp, base gốc, cùng phiên A10; greedy mới và8samples/pair, seed/config/train-IDF/scorer giữ nguyên. Không train hay GPU retry.

| Chỉ số regex | Greedy mới | MBR |
|---|---:|---:|
| Cờ thay đổi vật thể trên180 camera-only | {b['object_flags']} | {m['object_flags']} |
| Nhắc camera trên180 camera-only | {b['camera_mentions_pure']} | {m['camera_mentions_pure']} |
| Đúng hướng camera trên180 | {b['camera_direction_correct']} | {m['camera_direction_correct']} |
| Đúng loại+tên trên60 camera+object | {b['joint_type_name']} | {m['joint_type_name']} |
| Nhắc camera trên60 camera+object | {b['camera_mentions_object']} | {m['camera_mentions_object']} |
| Số từ trung bình240 | {b['mean_words']:.2f} | {m['mean_words']:.2f} |

Generation {gen['wall_seconds']:.1f}s gồm load; GPU worker {gpu['gpu_worker_seconds']:.1f}s gồm cài môi trường. Upper chi phí camera có đệm: {upper:.3f}USD, trần2USD. Xem FINAL_BILLING.json; billing có thể trễ, không phải invoice cuối.

CPU image đầu thiếu phụ thuộc gián tiếp cv2 từ synth_common. Đã báo và chuẩn bị correction trước khi sinh xong; chỉ bổ sung OpenCV ở CPU, chạy đúng selector/scorer bytes khóa ban đầu; giữ PIPELINE_DONE cũ và FINAL_OUTCOME sửa môi trường. Không sinh lại ứng viên, không đổi scoring theo kết quả.

Regex chỉ proxy, chưa có nhãn người; bộ camera tổng hợp2D đã từng dùng phát triển. Không dùng số134/180 cũ làm đối chứng chính, không chứng minh robustness3D hay quy lỗi về vision nếu không tăng. Không tự promotion decoder. Quyết định600: {conditional['status']}.
'''
(P/'KET_QUA.md').write_text(report,encoding='utf-8')
print(json.dumps({'metrics':metrics,'billing':snapshot,'synth600':conditional},default=str,indent=2),flush=True)
