# MBR decoding: pilot val200 qua gate, chưa chạy full test

**Cập nhật sau báo cáo pilot:** user đã duyệt full18USD và [full đang chạy](LIVE_FULL.md). Các trạng thái chưaadmit/GPUoff trong báo cáo phía dưới mô tả lúc kết thúc pilot, không phải trạng thái live. Chưa có điểm full.


Cập nhật 03/11/2026. Dùng checkpoint M3Diff gốc, không adapter, không train. Nhánh caption SFT v2 vẫn đã đóng; chưa triển khai loss đặc trưng. MBR là thay đổi ở bước sinh/chọn câu, chưa có bằng chứng model nhìn ảnh tốt hơn.

## Kết quả chính

Greedy và 8 caption sampling được sinh mới trong cùng container/GPU A10G, cùng phiên, cùng embedding ảnh cho từng cặp. Không lấy baseline lịch sử ghép vào phép so này. Một cấu hình được khóa trước val200; không chọn cấu hình theo điểm val.

| CIDEr ×100 | Greedy mới | MBR | Chênh lệch | Gate ≥ +1,0 |
|---|---:|---:|---:|---|
| Real, 100 cặp | 85,62 | 106,53 | **+20,91** | Qua |
| Render, 100 cặp | 201,47 | 206,70 | **+5,23** | Qua |

Đây là điểm trên tập val nhỏ, không so trực tiếp với CIDEr full test lịch sử. Val đã được dùng trong các vòng trước; không gọi đây là tập kiểm tra hoàn toàn chưa từng xem. CIDEr sử dụng bộ reference và DF của từng miền val theo scorer gốc, khác DF full test.

Bootstrap mô tả theo nhóm ảnh, giữ cố định DF reference: Real CI95% chênh lệch **[+5,65; +38,27]**, Render **[−38,95; +45,34]**. Có 20 nhóm ảnh Real, 11 nhóm Render; 100 cặp mỗi miền không phải 100 cảnh độc lập. Render chưa cho bằng chứng thống kê chắc chắn về mức tăng. CI chỉ để mô tả, không thay gate điểm số đã khóa.

## Đa dạng ứng viên, oracle và độ dài

| Chỉ số | Real | Render |
|---|---:|---:|
| Số caption khác nhau trung bình /9 | 8,48 | 8,58 |
| Số cặp MBR thay câu greedy /100 | 73 | 67 |
| Oracle CIDEr ×100 | 204,43 | 352,44 |
| Oracle − greedy | +118,81 | +150,97 |
| Số từ trung bình greedy → MBR | 53,62 → 51,72 | 57,88 → 51,25 |
| Số từ trung vị greedy → MBR | 47 → 44,5 | 48,5 → 49 |

Oracle dùng reference thật để biết trần của chính 9 ứng viên đã sinh; chỉ là chẩn đoán, không phải kết quả đạt được, không dùng để chọn caption hoặc chỉnh cấu hình. Selector thực chỉ dùng DF từ 12.452 cặp train. Có nhiều câu khác nhau để chọn; khoảng cách oracle lớn cho thấy selector vẫn bỏ lỡ nhiều ứng viên có điểm cao theo reference.

MBR chọn câu ngắn hơn về trung bình, nhất là Render; trung vị Render gần như không giảm. Chưa đủ để kết luận hết bỏ sót ý hoặc CIDEr chỉ tăng nhờ độ dài.

## Xem ảnh và caption thay thế

Đã xem 40 cặp được chọn bằng seed từ các cặp MBR đổi greedy, 20 mỗi miền, không chọn theo chênh lệch CIDEr thuận lợi. Che tên model bằng A/B, lưu và commit nhận xét trước khi mở khóa mapping. Real được xem trước điểm val cuối; Render sau khi biết điểm tổng nhưng không hiển thị điểm từng cặp hoặc caption reference.

| Nhận xét theo ảnh | Real /20 | Render /20 | Tổng /40 |
|---|---:|---:|---:|
| MBR tốt hơn về thông tin đúng/đủ | 7 | 6 | 13 |
| Greedy tốt hơn | 3 | 4 | 7 |
| Tương đương | 8 | 7 | 15 |
| Không chắc | 2 | 3 | 5 |

Người chấm là **Codex assistant**, không phải người gán nhãn độc lập. Mẫu chỉ gồm các cặp đổi caption, có cảnh nền dùng chung; không biến bảng này thành tỷ lệ lỗi factual của toàn bộ 200 cặp. Cả hai câu vẫn có thể sai. MBR có ca giảm câu bịa/định vị sai, cũng có ca thêm thông tin sai hoặc bỏ ý; không thể nói MBR tốt hơn ở mọi cặp.

Bằng chứng: [Real review](val200/ASSISTANT_REVIEW_REAL.json), [Render review](val200/ASSISTANT_REVIEW_RENDER.json). Masked Render được khóa ở commit `7ffe488` trước khi unmask; không sửa nhận xét sau khi đọc tên model.

## Tốc độ và kiểm tra implementation

- Pilot20: 8 lần sampling tuần tự mất 620,13 giây; batch thực tế 2 ×4 lượt mất 437,61 giây: nhanh hơn **1,42 lần**. Batch8 và batch4 OOM trên A10 ở implementation hiện tại; chuyển batch2 theo fallback khóa trước. Không lượng tử hóa để ép batch8.
- Reuse embedding ảnh/MDP một lần mỗi cặp. Không tái sử dụng KV prefix giữa các chuỗi: `generate` vẫn nhân bản batch trước LLM prefill. Ước tính KV riêng không đại diện cho tổng VRAM.
- Val200: inference **3.854,56 giây = 64 phút 15 giây**; toàn GPU job gồm setup **3.897,00 giây = 64 phút 57 giây**. 3/1.600 sampled caption và 1/200 greedy chạm cap1024; giữ nguyên, không sinh lại để chọn kết quả.
- Audit A100 được giới hạn trước ở 0,60 USD; hoàn thành **18/20**, dừng theo soft deadline, không retry. Không gọi đó là audit đủ20. Caption greedy từ cached embeddings khớp đường LLaVA gốc **18/18**, pixel CPU/GPU khớp **18/18**. Đây là kiểm tra implementation trên mẫu, không bảo đảm mọi môi trường/GPU cho caption giống nhau.
- Trên cùng18 ID, thời gian generate dùng cho full: A10 516,36 giây, A100 260,66 giây; A100 nhanh quan sát khoảng1,98 lần, chi phí theo rate upper khoảng0,962 lần A10. Không chấm điểm pool A100 bằng reference để chọn GPU. Độ dài output khác giữa GPU có thể ảnh hưởng phép đo thời gian này.
- Audit A100 job397,22 giây, GPU stopped **05:09:27 GMT+7**. Sau cùng app list và container list đều rỗng; không có GPU tiếp tục chạy.

## Cấu hình và tránh dùng nhãn để chọn câu

8 sampled +1 greedy; temperature0,7; top_p0,8; top_k20; repetition_penalty1,05; beam1; cap1024; BF16, noFlash/noquant; torch2.2.2+cu121, transformers4.40.0, peft0.4.0. Sampling seed cố định theo ID. Batch2 được chọn vì runtime trước khi quyết định val, không vì điểm CIDEr.

Chọn câu bằng CIDEr-D trung bình với 8 câu còn lại, loại chính nó, giữ câu trùng, hòa ưu tiên greedy rồi index nhỏ. Đây là consensus MBR xấp xỉ, không khẳng định là ước lượng posterior-risk không chệch. Train IDF đã cross-check với scorer độc lập trên3 ca (max error2,22e−16).

Một file metadata val chứa cột reference caption lịch sử nhưng không được đưa vào model hoặc utility; generator chỉ lấy id/subset ở file đó, prompt thật từ câu hỏi human và ảnh. Xem [DATAFLOW_AUDIT](DATAFLOW_AUDIT.json). Không diễn giải quá mức rằng process chưa từng mở file có nhãn. Lượt full đã chuẩn bị metadata chỉ id/domain, câu hỏi chỉ giữ human turn.

Fresh greedy val lần này khác baseline val lịch sử (Real94,41/Render203,17). Nguyên nhân chênh lệch môi trường/số học chưa được cô lập; không tự quy về một nguyên nhân hoặc dựng ngưỡng nhiễu chung. So sánh chính là paired greedy/MBR mới trong cùng phiên.

## Ngân sách và quyết định tiếp theo

Pilot20 trần1 USD; val200 và audit thuộc trần3,60 USD. Tổng upper bảo thủ đã cập nhật cho MBR là **3,32 USD**, gồm allowance/startup; không gọi đây là hóa đơn thực tế. Không mua thêm credit hay đổi gói.

Ước full từ thời gian theo từng miền val200: A10 khoảng8,32 giờ generation. Dùng tỷ lệ quan sát A10018 cặp cho ước tính khoảng4,20 giờ, chi phí upper-rate khoảng13,6 USD trước margin. Đây không phải đảm bảo runtime full, nhất là với đuôi caption dài.

Lượt full đã chuẩn bị, **chưa admit/chưa upload admission/chưa launch**: A10080GB,4CPU/32GiB,hard19.200 giây,soft18.900 giây, không retry. Đề xuất reservation17,70 USD (GPU17,45 gồm180 giây startup, CPU/misc0,25), trần18 USD. Mức này gần hết credit còn lại và vượt xa dự đoán4–6 USD ban đầu, nên cần chốt riêng mức chi này trước khi chạy. Xem [proposed protocol](full1570/PROPOSED_PROTOCOL.json).

Nếu chạy full, phải sinh mới greedy +8 mẫu cho803Real+767Render cùng phiên, giữ nguyên cấu hình/selector; chấm full bằng reference và scorer gốc. Không dùng oracle test để chọn, không tự đổi model mặc định, không đổi tham số theo kết quả full. Partial run không được gọi là benchmark đầy đủ.

**Kết luận hiện tại:** MBR có tín hiệu dương và qua gate val200; chưa xác nhận cải thiện full benchmark hoặc khả năng hiểu zoom/xoay. Pilot đã hoàn tất và GPU đã dừng.
