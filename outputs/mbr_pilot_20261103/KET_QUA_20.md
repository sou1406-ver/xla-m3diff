# Pilot MBR20 — đo thực tế trước val200

**Đủ20/20cặp,10Real+10Render. Không train, chỉ base gốc. Batch8và4 OOM trong implementation này; dùng4chunk×2 để sinh8câu. Chọn batch2 theo runtime đã khóa, không chọn theo điểm.** GPU pilot đã dừng03/11 03:38:18 GMT+7. Val200 là bước tiếp theo riêng, chưa có điểm ở snapshot này.

## Tốc độ và bộ nhớ

| Sinh8caption/cặp | Tổng20cặp | Trung bình | Trung vị | Chậm nhất |
|---|---:|---:|---:|---:|
| Tuần tự |620,13s|31,01s|20,80s|185,62s|
|4chunk×2|437,61s|21,88s|14,04s|146,55s|

Batch2 nhanh hơn **1,417×**, chưa phải mức tăng tốc giả định cho batch8. Peak allocated thành công khoảng16,99GiB tuần tự và18,35GiB batch2; lần8/4bịOOM không được tính là successful peak. Greedy20cặp mất95,48s; xử lý ảnh/vision/MDP thành embedding mất8,80s. Tổng job gồm cả hai cách,greedy,setup là1.262,98s=21phút3giây.

`render_val_pair_000416` là ca dài: greedy lịch sử732từ và chi phối đuôi thời gian đo. Mỗi cách có4/160samplingcaption chạm cap1024token; không hạ cap/bỏ cặp sau khi thấy chậm. Dự toán lấy từ đúng đường được chọn: `(437,61+95,48+8,80)/20≈27,09s/cặp`, tức khoảng90phút cho200 trước margin/setup. Đây là ngoại suy từ20cặp, không phải thời gian thực tế của val200.

## Điểm20cặp: trái chiều, không cherry-pick cách tốt hơn

Điểm là CIDEr×100, mỗi miền dùng DF từ đầy đủ100referenceval đã khóa để tính điểm chẩn đoán cho10cặp được chọn. Không so trực tiếp điểm trung bình10cặp này với điểm100cặp hoặc fulltest.

| Pool sinh | Miền | Greedy | MBR | Chênh | Oracle | Oracle−greedy |
|---|---|---:|---:|---:|---:|---:|
|Tuần tự|Real|120,87|144,06|+23,20|260,77|+139,91|
|Tuần tự|Render|266,86|303,45|+36,59|428,75|+161,89|
|Batch2 đã chọn|Real|120,87|108,73|−12,14|244,52|+123,66|
|Batch2 đã chọn|Render|266,86|225,44|−41,42|377,51|+110,65|

Hai implementation tiêu thụ RNG theo cách khác nên tạo hai pool khác nhau dù cùng phân bố/hyperparameter; không kỳ vọng từng sample giống nhau. Trái dấu trên10cặp/miền cho thấy kết luận từ một pool nhỏ rất không chắc. Không chuyển sang tuần tự vì nó có điểm tốt hơn sau khi xem reference. Val200 giữ phương pháp chọn bằng runtime, một cấu hình/seed; không tune lại.

Oracle dùng referenceval **chỉ để chẩn đoán sau sinh/chọn**. Đây là trần có điều kiện của những pool đã sinh, không phải điểm đạt được, không dùng để chọn caption thực tế và không dự đoán chắc kết quả200cặp. Pool có câu tốt hơn greedy khá nhiều, nhưng consensus chưa chọn được tốt trên pool batch nhỏ này.

## Độ đa dạng và độ dài — pool batch2

|Miền|Caption khác nhau trung bình /9|Greedy số từ mean/median|MBR số từ mean/median|Đổi câu so greedy|
|---|---:|---:|---:|---:|
|Real|8,4|57,2/46,5|61,5/51,5|5/10|
|Render|8,0|124,0/66,0|53,8/48,5|6/10|

Mean Render bị ảnh hưởng mạnh bởi caption dài; không quy mọi chênh lệch điểm cho độ dài chỉ từ bảng này. Tham khảo raw trong [results20](results20.jsonl), [METRICS20](METRICS20.json), [PER_PAIR20](PER_PAIR20.json).

## Chi tiết để tái kiểm tra

- `temperature=.7,top_p=.8,top_k=20,repetition_penalty=1.05,max_new_tokens=1024,num_beams=1`;BF16,không quantize/Flash. Greedy cùng cap/penalty.
- Tái dùng embedding vision/MDP một lần mỗi cặp. Native Qwen2generate xử lý `inputs_embeds`; xác nhận greedy cặp đầu khớp wrapper LLaVA. **Chưa chia sẻ KV prefix của LLM.** `num_return_sequences`/expandembeds không tự cho prefix sharing. Không suy từ ước tính KV rằng toàn bộ batch8 phải vừa24GB.
- Selector: CIDEr-D trung bình với8caption còn lại, bỏself,giữmultiplicitycủacâutrùng,tieưu tiêngreedy. Greedy nằm trong pool tham chiếu giả theo đề xuất; đây là consensus MBR xấp xỉ, không tuyên bố estimator posterior risk không chệch.
- IDF chỉ từ12.452trainpair,248.504n-gram,PTBtokenizer,sigma6,4gram. Numeric utility cross-check3ca với scorer benchmark sai số tối đa2,22e−16. Có một lỗi format ca kiểm chứng CPU đã sửa trước GPU/candidate; lưu lịch sử lock.
- Generation chỉ dùng question/image làm đầu vào model; sidecar selection có caption tham chiếu cũ nhưng mã sinh chỉ truy cập id/subset, không dùng caption. Không mô tả process là chưa từng mở file có nhãn. Selector chỉ nhận caption sinh và IDF train; COCO referenceval dùng để chấm sau lựa chọn. Xem DATAFLOW_AUDIT.json.
- Cohort200đã được dùng làm development ở các vòng trước, không phải một tập hoàn toàn chưa từng xem. Fulltest cũng có lịch sử baseline; không tuyên bố blind test.

Val200 chốt một cấu hình trên cùng GPU/phiên cho greedy+MBR, gate mỗi miền `delta CIDEr×100>=1,0`, trần3,60USD(hard2hGPU,reserve3,57USDgồmscoring). Chỉ sau gate và xem mẫu caption được thay thế mới xét ngân sách full. Không có loss đặc trưng hoặc training trong hướng này; vòng V2 vẫn đóng.
