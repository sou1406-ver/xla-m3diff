"""Consolidate the completed round; no remote compute, no model promotion."""
import csv,hashlib,json,statistics,sys,zipfile
from datetime import datetime,timezone
from pathlib import Path
HERE=Path(__file__).parent
read=lambda n:json.loads((HERE/n).read_text(encoding='utf-8-sig'))
save=lambda n,v:(HERE/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
arms=['baseline','old_mixed','control','revised'];initial=read('initial_metrics.json');new=read('new_metrics.json');stress=read('positive_stress/metrics.json')
stats={k:{**initial[k],**new[k]} for k in initial}
base=stats['all/all_synthetic']['baseline'];decisions={}
for arm in ['control','revised']:
    primary={'fewer_synthetic_unsupported_cases':stats['all/all_synthetic'][arm]['any_error']<base['any_error'],
        **{d+'_natural_facts_preserved':stats[d+'/natural'][arm]['fact_hits']>=stats[d+'/natural']['baseline']['fact_hits'] for d in ['Real','Render']},
        'natural_unsupported_pairs_not_increased':stats['all/natural'][arm]['unsupported_pairs']<=stats['all/natural']['baseline']['unsupported_pairs']}
    safety={**{d+'_stress_facts_preserved':stress[d][arm]['fact_hits']>=stress[d]['baseline']['fact_hits'] for d in ['Real','Render']},
        'stress_unsupported_pairs_not_increased':stress['all'][arm]['unsupported_pairs']<=stress['all']['baseline']['unsupported_pairs']}
    decisions[arm]={'primary_checks':primary,'primary_pass':all(primary.values()),'positive_stress_checks':safety,'positive_stress_pass':all(safety.values()),
                    'eligible_for_broad_evaluation':all(primary.values()) and all(safety.values())}
assert not any(v['eligible_for_broad_evaluation'] for v in decisions.values())
save('decision.json',{'candidates':decisions,'promoted_model':None,'full1570_run_for_new_models':False,
    'reason':'Neither candidate passes the pre-recorded natural-fact retention safety check. Keep credit; do not spend on full test for failed candidates.',
    'limits':'Conditional on small correlated assistant-reviewed samples; not proof that all geometry-aware approaches are infeasible.'})
apps=read('final_apps.json');ours=['ap-WIQHsKBJxELCehvzmToiXV','ap-ZSGxpTILIu84uGRLlmbd4c','ap-Hch5P6oavYL34jDPiAAFav','ap-GkCEGMY3CDLRFpCNjyLMAt','ap-y3DVFapxZJkcp9MY6AXvse','ap-iUSPUybguw2OzbAA6PBz3S']
byid={a['app_id']:a for a in apps};assert all(k in byid for k in ours)
assert all(byid[k]['state']=='stopped' and int(byid[k]['tasks'])==0 for k in ours)
save('FINAL_GPU_CHECK.json',{'time_utc':datetime.now(timezone.utc).isoformat(),'all_own_apps_stopped':True,'active_own_tasks':0,'app_ids':ours,'source':'final_apps.json'})
proof=read('MATCHED_TRAIN_DONE.json');assert proof['same_initialization'] and proof['same_index_orders'] and proof['steps_each']==128
for a in ['control','revised']:
    done=read(f'm3diff-{a}-lora/TRAIN_DONE.json');assert done['steps']==128 and done['samples']==1024 and done['only_lora'] and done['all_finite']
    load=read(a+'_load_audit.json');assert load['saved_values_restored_exactly_after_fp32_cast'] and load['n_adapter_tensors']==392
rows=read('initial_decoded.json')['rows']+read('new_decoded.json')['rows']
stressrows=read('positive_stress/decoded.json')['rows'];assert len(rows)==384 and len(stressrows)==64
with (HERE/'case_scores.csv').open('w',encoding='utf-8-sig',newline='') as f:
    fields=['set','id','scene','domain','condition','arm','physical','false_light','wrong_geometry','ack','facts','unsupported','uncertain','caption','raw_sha256']
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
    for dataset,rs in [('main',rows),('positive_stress',stressrows)]:
        for r in rs:
            item={k:r.get(k,'') for k in fields};item['set']=dataset
            if dataset=='positive_stress':item['condition']='positive_stress';item['ack']=r['display_ack']
            for k in ['facts','unsupported','uncertain']:item[k]=json.dumps(r[k],ensure_ascii=False)
            w.writerow(item)
behavior={}
for arm in arms:
    raw=[json.loads(l) for l in (HERE/(arm+'.jsonl')).read_text().splitlines() if l.strip()]
    assert len(raw)==96 and len({r['id'] for r in raw})==96
    lengths=[len(r['caption'].split()) for r in raw]
    behavior[arm]={'n':96,'mean_words':statistics.mean(lengths),'median_words':statistics.median(lengths),
                   'at_least500_words':sum(n>=500 for n in lengths),'max_words':max(lengths)}
save('caption_behavior.json',behavior);save('metrics_all_models.json',stats)
budget=read('latest_budget.json');cost=budget['api_consumption'];labels=['Gốc','Mixed cũ','Đối chứng128','Dữ liệu sửa128']
def table(headers,body):return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join(['---']+['---:']*(len(headers)-1))+'|']+['| '+' | '.join(map(str,r))+' |' for r in body])
def mainrow(name,key,metric):return [name]+[stats[key][a][metric] for a in arms]
def stressrow(name,domain,metric):return [name]+[stress[domain][a][metric] for a in arms]
text=f'''# M3Diff — kết quả vòng thử nghiệm ngày02/11/2026

**Đã train xong hai checkpoint LoRA mới, đánh giá xong và tắt toàn bộ GPU. Chưa có checkpoint mới đủ điều kiện giữ lại làm model cải thiện.** Nhánh sửa dữ liệu không tốt hơn đối chứng. Đối chứng có tín hiệu nhỏ trên bộ không đổi, nhưng mất thông tin khi vừa có thay đổi thật vừa có biến đổi hình học. Vì vậy không chạy full1570 cho hai ứng viên này và không tiêu tiếp chỉ để dùng hết credit.

##1. Đã thực hiện

- Kiểm chứng lại model gốc và mixed adapter cũ trên96 cặp đã khóa.
- Train2 nhánh từ model gốc: đối chứng và dữ liệu sửa. Mỗi nhánh512 record,2 epoch,128 cập nhật, batch1/accum8, LR1e-5, seed42, LoRA r16/alpha32. Tổng2048 lượt mẫu qua hai nhánh, không phải2048 cặp độc lập.
- Chỉ LoRA được cập nhật; vision, MDP, projector và trọng số ngôn ngữ gốc đóng băng. Không có SCST hoặc LocateAnything trong vòng này.
- Xác nhận cùng khởi tạo LoRA/MDP, cùng thứ tự index ở hai epoch, loss hữu hạn, chỉ LoRA trainable,392 tensor adapter được khôi phục chính xác ở FP32 khi suy luận.
- Model gốc/mixed cũ/đối chứng/sửa dữ liệu:4×96=384 caption. Kiểm tra bổ sung4×16=64 caption. Tổng448 caption mới; không phải448 scene độc lập.

##2. Nhánh sửa khác gì?

Đối chứng lặp lại192 record replay/positive và64 record nuisance cũ để đủ512 record. Nhánh sửa giữ192 replay gốc, thêm192 bản augmentation:96 biến đổi cả hai ảnh,96 chỉ biến đổi ảnh sau và thêm mô tả chính xác về display rotation/scale. Toàn bộ trường ảnh được giữ trên canvas trung tính.128 nuisance gồm64 mẫu cũ với nhãn riêng theo điều kiện,32 lượt lặp và32 mẫu chỉ sáng/tối.

Đây là so sánh một gói sửa dữ liệu/nhãn, không cô lập từng thành phần. Nhãn cũ đã có mô tả framing/orientation; không được nói lần này mới bổ sung khái niệm đó. Replay có nhãn tác giả và các sửa nhãn do trợ lý thực hiện trước đây; không phải toàn bộ được người chấm độc lập xác nhận. Xem `PROVENANCE_NOTES.md`.

##3. Bộ kiểm tra chính

16 cặp nguồn,13 nhóm nền cảnh, mỗi nguồn gồm identity, zoom-in, zoom-out, roll, brightness và natural:96 cặp. Loại trùng decoded RGB với958 hash trong các bộ train/chẩn đoán đã chọn. Không đồng nghĩa scene độc lập hoặc test chưa từng dùng: toàn official test đã được chạy trước đây. Rubric ảnh và29 ý tối thiểu được khóa trước caption mới. Chấm do trợ lý, ẩn tên model; chưa có người chấm độc lập.

“Ca có khẳng định sai” đếm hợp của lỗi vật thể, nói sai ánh sáng và giải thích hình học sai. Không đồng nghĩa mọi ca còn lại đều mô tả đầy đủ: câu chung chung có thể tránh bịa nhưng bỏ sót điều kiện. Ý chính natural và nhận đúng nuisance được ghi riêng.

'''
text+=table(['Chỉ số — thấp hơn tốt hơn']+labels,[
    mainrow('Có khẳng định sai /80 synthetic','all/all_synthetic','any_error'),
    mainrow('Có khẳng định sai /48 xoay-zoom','all/geometry','any_error'),
    mainrow('Bịa thay đổi vật thể /48 xoay-zoom','all/geometry','physical'),
    mainrow('Nói sai ánh sáng /48 xoay-zoom','all/geometry','false_light'),
    mainrow('Giải thích hình học sai /48 xoay-zoom','all/geometry','wrong_geometry'),
    mainrow('Khẳng định sai /16 ảnh giống hệt','all/identity','any_error'),
    mainrow('Khẳng định sai /16 chỉ tăng sáng','all/brightness','any_error')])
text+='\n\n'+table(['Natural — ý chính cao hơn tốt hơn']+labels,[
    mainrow('Ý chính Real /14','Real/natural','fact_hits'),mainrow('Ý chính Render /15','Render/natural','fact_hits'),
    mainrow('Tổng ý chính /29','all/natural','fact_hits'),mainrow('Cặp có khẳng định phụ sai /16','all/natural','unsupported_pairs')])
text+='''

Đối chứng mới chỉ hơn mixed cũ1 ca xoay/zoom theo đánh giá này; không đủ gọi là bước nhảy chất lượng. Nhánh sửa tăng lỗi giải thích hình học và ánh sáng, đồng thời mất ý chính natural. Nó có một số câu zoom đúng và nhận đúng tăng sáng nhiều hơn, nhưng dùng các mẫu giải thích ấy sai điều kiện: cả ảnh giống hệt cũng bị nói đã xoay90độ hoặc zoom. Đây là dấu hiệu đáng kiểm tra về học mẫu câu; chưa chứng minh được cơ chế bên trong.

##4. Thay đổi thật kèm biến đổi hình học

Thêm16 biến thể phụ thuộc của chính16 cặp natural: ảnh sau xoay-10độ có containment hoặc hiển thị ở88% scale. Không cắt nội dung; dùng cùng29 ý tối thiểu. Supplement được ghi sau khi xem kiểm tra gốc/mixed cũ, trước caption của hai model mới. Đây không phải một holdout mới.

'''
text+=table(['Chỉ số stress']+labels,[stressrow('Ý chính Real /14','Real','fact_hits'),stressrow('Ý chính Render /15','Render','fact_hits'),
    stressrow('Tổng ý chính /29','all','fact_hits'),stressrow('Cặp có khẳng định sai /16','all','unsupported_pairs')])
text+='''

Ngưỡng giữ lại: không giảm ý chính ở TỪNG miền và không tăng cặp có khẳng định sai so với model gốc. Đối chứng giảm Real8→6 và Render11→10; nhánh sửa giảm Real8→6 và Render11→7, còn tăng cặp sai. Vì vậy cả hai không đạt kiểm tra an toàn này. Các số nhỏ, nhiều chi tiết còn chưa chắc; kết luận phù hợp là chưa đủ cơ sở giữ checkpoint, không phải chứng minh mọi hướng chống nhiễu hình học đều vô ích.

##5. Ví dụ có thể xem lại

'''
for rid in ['v2_Real_00__identity','v2_Real_06__zoom_in','v2_Real_03__natural']:
    r=next(r for r in rows if r['id']==rid and r['arm']=='revised')
    text+=f"- `{rid}` — nhánh sửa: “{r['caption']}”\n"
text+='''
Ví dụ đầu là ảnh giống hệt nhưng bị nói xoay90độ; ví dụ thứ hai nhận đúng crop zoom; ví dụ thứ ba chỉ nói zoom và bỏ sót sự kiện xe đạp tiền cảnh đã khóa trong rubric. Có thể tra từng câu, nhãn, phần chưa chắc và hash raw trong `case_scores.csv`.

Trong96 caption chính, nhánh sửa có2 caption từ500 từ trở lên (dài nhất900 từ), trong khi3 model còn lại không có. Đây là cảnh báo về output dài/lặp trên mẫu này, không phải tỷ lệ lỗi toàn benchmark. Xem `caption_behavior.json`.

##6. Quyết định và giới hạn

- Không đổi model mặc định; không chạy full1570 cho ứng viên không đạt gate.
- Đối chứng qua gate chính nhưng không qua supplement giữ thông tin. Nhánh sửa không qua cả hai. Xem `decision.json` và quy tắc đã ghi trong `SELECTION_POLICY.md`.
- Chưa có CIDEr/BLEU full-test mới; không lấy điểm của các lượt trước gán cho hai checkpoint này.
- Một seed, ít nền cảnh lặp, biến đổi2D, nhãn/đánh giá có phần do trợ lý, prompt nuisance vẫn tập trung một kiểu trong khi replay có10 kiểu. Cùng decoding nhưng hai nhóm main predictions dùng hai container A10-family; không gọi tất cả là cùng một physical GPU. Supplement chạy cả4 model trong một container.
- Đơn thuần tăng train với công thức dữ liệu sửa này chưa được kết quả ủng hộ. Nếu nghiên cứu tiếp, cần thiết kế lại tín hiệu học/đối chiếu đặc trưng và dữ liệu viewpoint thật, cùng kiểm tra giữ thay đổi thật; những phần đó CHƯA được triển khai ở vòng này.

##7. Checkpoint và tài nguyên

Trọng số đã lưu trong Volume Modal `m3diff`:

- `/invariance_v2_20261102/m3diff-control-lora/`
- `/invariance_v2_20261102/m3diff-revised-lora/`

Đây là checkpoint LoRA suy luận thử nghiệm, không được chọn thay model gốc. Folder tương ứng ở máy hiện chỉ giữ metadata/log kiểm chứng; trọng số thực nằm trên Volume. Script `download.py` có thể lấy từng file qua SDK mà không mở GPU. Cần đúng base M3Diff và loader FP32 unmerged; chưa xuất một gói portable mới hoặc tuyên bố chạy được trong demo SCST của repo khác. Không lưu đầy đủ optimizer/RNG để exact-resume train.

'''
text+=f"Tất cả6 app của vòng này đã stopped,0 task (`FINAL_GPU_CHECK.json`). Billing snapshot `{budget['time_utc']}` ghi nhận consumption upper khoảng${float(cost):.2f}, billed cost0; số liệu có thể trễ, không phải endpoint số dư credit trực tiếp. Chưa dùng hết gói$30. Không mua credit, không đổi billing.\n\n"
text+='''Một job CPU bổ sung bị lỗi import lúc startup đã được dừng và sửa; job train chính không bị ảnh hưởng. Không có GPU chạy chờ người chấm.

##8. File kiểm chứng

`PLAN.md`, `SUPPLEMENT_PLAN.md`, `SELECTION_POLICY.md`, `SELECTION_LOCK.json`, `data_audit.json`, `REVIEW_APPROVED.json`, `MATCHED_TRAIN_DONE.json`, hai `TRAIN_DONE.json`, các raw JSONL, masked assessments/key, `ACK_DERIVATION_AUDIT.json`, `metrics_all_models.json`, `positive_stress/metrics.json`, `decision.json`, `case_scores.csv`, `caption_behavior.json`, `PROVENANCE_NOTES.md`, `FINAL_GPU_CHECK.json`.
'''
# Conventional Markdown heading whitespace and readable units, without changing source protocols.
import re
text=re.sub(r'^(#{1,6})(\d)',r'\1 \2',text,flags=re.M)
protected=['M3Diff','FP32','BF16','LoRA r16/alpha32','2D','3D']
parts=re.split(r'(`[^`]*`)',text)
for i,part in enumerate(parts):
    if part.startswith('`'):continue
    for j,token in enumerate(protected):part=part.replace(token,'@@PROTECTED'+chr(65+j)+'@@')
    part=re.sub(r'(?<=[A-Za-zÀ-ỹ])(?=\d)|(?<=\d)(?=[A-Za-zÀ-ỹ])',' ',part)
    part=re.sub(r',(?=\d)',', ',part);part=re.sub(r'(?<=[A-Za-zÀ-ỹ])(?=\$)',' ',part)
    for j,token in enumerate(protected):part=part.replace('@@PROTECTED'+chr(65+j)+'@@',token)
    parts[i]=part
text=''.join(parts)
(HERE/'KET_QUA.md').write_text(text,encoding='utf8')
save('ROUND_SUMMARY.json',{'complete':True,'new_checkpoints':2,'updates_each':128,'new_generations':448,'new_full_test':False,
    'promoted':None,'all_own_apps_stopped':True,'billing_snapshot_usd':cost,'decision':decisions})
evidence={str(p.relative_to(HERE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(HERE.rglob('*'))
          if p.is_file() and '__pycache__' not in p.parts and p.suffix in ['.py','.md','.json','.jsonl','.csv','.jpg','.png'] and p.name!='EVIDENCE_MANIFEST.json'}
save('EVIDENCE_MANIFEST.json',evidence)
archive=HERE.parent/'m3diff_invariance_v2_20261102_results.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(HERE.rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts and p.suffix in ['.py','.md','.json','.jsonl','.csv','.jpg','.png','.txt','.log']:
            z.write(p,str(p.relative_to(HERE)))
with zipfile.ZipFile(archive) as z:assert z.testzip() is None
print(json.dumps({'decision':decisions,'all_own_apps_stopped':True,'archive':str(archive),'bytes':archive.stat().st_size},ensure_ascii=False,indent=2))
