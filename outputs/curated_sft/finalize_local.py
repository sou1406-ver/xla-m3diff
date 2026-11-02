"""Decode only the saved masked rankings and assemble the final deliverables."""
import datetime, hashlib, json, zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parent
def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8-sig'))
def write(path,obj):(ROOT/path).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
audit=read('masked_assessments.json'); candidates=read('final_results/blind_audit.json');key=read('final_results/blind_key.json')
assert len(audit['cases'])==len(candidates)==16
results={a:{s:{'wins':0,'losses':0,'ties':0} for s in ['Real','Render','all']} for a in ['corrected_labels_dedup','corrected_lora_only_dedup']}
decoded=[]
for review,case in zip(audit['cases'],candidates):
    assert review['index']==case['index']
    ranks={key[case['id']][f'candidate_{i}']:rank for rank,tier in enumerate(review['rank_tiers']) for i in tier}
    assert len(ranks)==3
    item={'id':case['id'],'split':case['split'],'ranks':ranks,'evidence':review['evidence']}
    for arm in results:
        outcome='wins' if ranks[arm]<ranks['baseline_dedup'] else 'losses' if ranks[arm]>ranks['baseline_dedup'] else 'ties'
        for split in [case['split'],'all']:results[arm][split][outcome]+=1
    decoded.append(item)
write('decoded_audit.json',{'reviewer':audit['reviewer'],'masked_source_sha256':hashlib.sha256((ROOT/'masked_assessments.json').read_bytes()).hexdigest(),'outcomes':results,'cases':decoded,'limitations':audit['limitations']})
metrics=read('final_results/metrics_with_dedup.json');full=read('dedup_full_results/metrics.json')
gate={}
for arm in ['corrected_labels','corrected_lora_only']:
    delta={s:{m:100*(metrics[s][arm][m]-metrics[s]['baseline'][m]) for m in ['CIDEr','Bleu_4']} for s in metrics}
    outcome=results[arm+'_dedup']['all']
    checks={'CIDEr_improves_both_domains':all(d['CIDEr']>0 for d in delta.values()),'BLEU4_drop_at_most_1_each':all(d['Bleu_4']>=-1 for d in delta.values()),'blind_wins_exceed_losses':outcome['wins']>outcome['losses']}
    gate[arm]={'delta_x100':delta,'checks':checks,'qualifies':all(checks.values())}
assert not any(g['qualifies'] for g in gate.values()),'A candidate qualifies: run the authorized full evaluation before finalizing.'
write('decision.json',{'time_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'candidate_gate':gate,'decision':'Keep published checkpoint plus exact-sentence cleanup. No full-test SFT run or further tuning in this experiment.','reason':'Both corrected-label arms lose raw CIDEr on Render; neither meets the fixed gate.','scope':'No demonstrated rotation/zoom understanding gain; output cleanup verified on saved full-test predictions.'})
controls=read('final_results/control_verification.json')
assert all(controls[k] for k in ['matched_lora_initialization','matched_MDP_initialization','matched_actual_sample_order','same_images_prompts_and_input_order'])
for item in read('final_results/prediction_integrity.json').values():assert item['n']==item['unique_ids']==256 and item['expected_id_set_matches']
for p in ROOT.glob('*.zip'):
    with zipfile.ZipFile(p) as z:assert z.testzip() is None,p
lines=['# Kết quả cải thiện M3Diff','',
'**Bản nên dùng hiện tại: checkpoint M3Diff công bố + bộ lọc câu lặp nguyên văn. Các checkpoint SFT được giữ để nghiên cứu, chưa chọn thay baseline.**','',
'## Đã làm','',
'- Rà trực quan 48 cặp train, giữ 44 cặp (22 mỗi miền), sửa caption theo bằng chứng trong ảnh. Người rà là trợ lý Codex, chưa có gán nhãn độc lập bởi con người.',
'- Train ba đối chứng: nhãn gốc + LoRA/MDP; nhãn sửa + LoRA/MDP; nhãn sửa + chỉ LoRA. Mỗi nhánh 216 bản ghi, 172 cặp duy nhất, 27 update. Đã xác nhận hash khởi tạo và thứ tự mẫu thực tế trùng nhau.',
'- Đánh giá 256 cặp (128 mỗi miền), chạy lại baseline trên GPU họ A100 và chấm BLEU/METEOR/ROUGE/CIDEr. Modal cấp baseline A100-SXM4-80GB dù yêu cầu 40GB; chưa xác nhận cùng SKU vật lý cho mọi nhánh.',
'- Xem ảnh trước caption và chấm ẩn tên model trên 16 cặp; lưu nhận xét rồi mới giải khóa. Đây là đánh giá của trợ lý, không phải nghiên cứu chấm mù độc lập bởi con người.','',
'## SFT trên cùng 256 cặp','',
'Điểm nhân 100. Đây là điểm trên tập con, không so CIDEr trực tiếp với điểm toàn test ở bảng sau.','',
'| Nhánh | Real CIDEr | Render CIDEr | Real BLEU-4 | Render BLEU-4 |',
'|---|---:|---:|---:|---:|']
for arm,label in [('baseline','Checkpoint gốc, chạy lại A100'),('original_labels','SFT nhãn gốc'),('corrected_labels','SFT nhãn sửa + MDP'),('corrected_lora_only','SFT nhãn sửa, MDP đóng băng'),('previous_random','SFT ngẫu nhiên pilot trước')]:
    v=[100*metrics[s][arm][m] for m,s in [('CIDEr','Real'),('CIDEr','Render'),('Bleu_4','Real'),('Bleu_4','Render')]]
    lines.append('| '+label+' | '+' | '.join(f'{x:.2f}' for x in v)+' |')
lines+=['','Nhãn sửa + MDP tăng CIDEr Real +3,87 nhưng giảm Render −3,71; chỉ LoRA tăng Real +3,30 và giảm Render −2,77. Nhánh nhãn sửa + MDP còn thấp hơn nhãn gốc trên cả hai miền. Chưa chứng minh sửa nhãn theo cách này giúp model tốt hơn; chưa thể quy kết nguyên nhân từ một seed và bộ train nhỏ. Bootstrap theo cụm ảnh chung cho nhánh nhãn sửa + MDP ở Real có CI95% chứa 0 (−1,64 đến +12,71).','',
'Chấm trực quan cùng bộ lọc lặp trước khi so:']
for arm,label in [('corrected_labels_dedup','Nhãn sửa + MDP'),('corrected_lora_only_dedup','Nhãn sửa, MDP đóng băng')]:
    r=results[arm]['all'];lines.append(f"- {label}: {r['wins']} thắng / {r['losses']} thua / {r['ties']} hòa so với baseline trên 16 cặp.")
lines+=['','Nhiều trường hợp cả ba caption cùng sai: thay tư thế bị mô tả thành nằm xuống, vật vẫn còn bị nói biến mất, màn hình xoay bị nhầm thành thay bàn phím/ghế. Thắng tương đối không đồng nghĩa caption đã đúng. Cả hai nhánh đều không đạt điều kiện tăng CIDEr ở cả hai miền, nên không chạy tiếp full-test SFT hoặc dò thêm cấu hình.','',
'## Cải thiện giữ lại: loại câu lặp','',
'Đã chấm lại toàn bộ **803 Real + 767 Render**, dùng đúng caption gốc và sau xử lý trên cùng nguồn dự đoán baseline đã lưu. Không cần GPU cho bước lọc.','',
'| Miền | BLEU-4 trước → sau | CIDEr trước → sau |',
'|---|---:|---:|']
for s in ['Real','Render']:
    b,d=full[s]['baseline'],full[s]['dedup'];lines.append(f"| {s} | {b['Bleu_4']*100:.3f} → {d['Bleu_4']*100:.3f} | {b['CIDEr']*100:.3f} → {d['CIDEr']*100:.3f} |")
lines+=['','15/1.570 caption được xử lý lặp, 1.555 giữ nguyên. Bộ lọc chỉ xóa phần lặp, không thêm mô tả mới. BLEU tăng chủ yếu nhờ cắt vòng lặp dài; CIDEr tăng rất ít. Đây là cải thiện chất lượng đầu ra, **chưa phải cải thiện khả năng hiểu xoay góc hoặc zoom**.','',
'## Dùng ngay','',
'```powershell','python postprocess_jsonl.py --input captions_raw.jsonl --output captions_clean.jsonl --audit dedup_audit.json','```','',
'`README.md` hướng dẫn chạy lại; `dedup_full_results/` có caption sau lọc và điểm đủ test; `final_results/` có caption, điểm, log và kiểm tra đối chứng SFT; `masked_assessments.json` và `decoded_audit.json` ghi chấm ẩn tên và giải khóa. `decision.json` ghi điều kiện chọn model và quyết định.','',
'## Giới hạn và hướng tiếp theo','',
'Tập đánh giá được dùng cho nhiều phép thử nên không còn là test độc lập cho lựa chọn model. 128 cặp Real dùng ảnh mới so với pilot; Render chỉ 9 cặp ảnh mới, các cặp còn lại chia sẻ ảnh đã xem. Có cụm ảnh chung; bootstrap theo cụm vẫn chưa bảo đảm bao hết scene. Một seed, ít dữ liệu sửa, độ dài/cách viết nhãn cũng thay đổi cùng độ chính xác.','',
'Hướng nghiên cứu tiếp hợp lý là lập validation tách scene và tập kiểm tra riêng cho thay góc/zoom nhưng không thay vật; mở rộng nhãn sửa bằng người rà độc lập rồi thử huấn luyện nhất quán theo góc nhìn với đối chứng. Chưa có kết quả để khẳng định hướng đó sẽ tăng điểm.','',
'Tất cả app thử nghiệm đã ở trạng thái stopped, 0 task khi kiểm tra cuối. Trọng số và dữ liệu vẫn lưu trên Modal Volume m3diff/curated_sft_v4; không có endpoint GPU thường trực.']
(ROOT/'KET_QUA.md').write_text('\n'.join(lines)+'\n',encoding='utf8')
for n in ['masked_assessments.json','decoded_audit.json','decision.json','KET_QUA.md']:(ROOT/'final_results'/n).write_bytes((ROOT/n).read_bytes())
files=[p for p in ROOT.rglob('*') if p.is_file() and (p.parent==ROOT or p.relative_to(ROOT).parts[0] in ['final_results','dedup_full_results']) and p.suffix in ['.py','.json','.jsonl','.md','.csv','.log','.txt','.patch']]
with zipfile.ZipFile(ROOT.parent/'m3diff_improvement_results.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in files:z.write(p,str(p.relative_to(ROOT)))
with zipfile.ZipFile(ROOT.parent/'m3diff_improvement_results.zip') as z:assert z.testzip() is None
print(json.dumps({'audit':results,'gate':gate,'packaged_files':len(files)},ensure_ascii=False,indent=2))
