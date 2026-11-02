# Đánh giá checkpoint r64: sanity8 và camera240 — 02/11/2026

Đã hoàn thành đúng phạm vi: A10, Bước11 xác nhận **Đã train xong**, sanity8, camera240; không train, không chạy bộ tổng hợp600 hoặc OmniDiff full. App hoàn tất và được xác nhận stopped/0task. Chờ người dùng chấm hai gate trước khi chạy tiếp.

## Kết quả bộ chấm từ khóa hiện có

| Chỉ số | Base đã lưu | r64 |
|---|---:|---:|
| Cờ thay đổi vật thể trên180camera-only, thấp hơn tốt |134/180 (74.4%)|43/180 (23.9%)|
| Nhắc camera trên180camera-only |0/180|149/180 (82.8%)|
| Hướng camera khớp từ khóa |0/180|45/180 (25.0%)|
| Đúng từ khóa thêm/xóa trên60camera+object |55/60|57/60|
| Nhắc đúng tên/category vật trên60camera+object |38/60|43/60|
| Cùng có đúng loại và tên vật trên60camera+object |35/60 (58.3%)|43/60 (71.7%)|

Chi tiết: cam_add30cặp, loại27→30, tên19→22; cam_remove30cặp, loại28→27, tên19→21. Hướng camera vẫn yếu; không được coi nhắc camera là hiểu đúng biến đổi. Ví dụ zoom_in_L1_00 bị r64 gọi là shifted to the left; zoom_in_L1_03 bị gọi là darker.

**Đây là proxy từ regex, chưa phải nhãn semantic độc lập.** `false_obj` có thể bắt cả mô tả kích thước/visibility do zoom và chưa xử lý mọi phủ định; đúng tên và loại không đảm bảo cùng thuộc một claim đúng. Một số lỗi như nói sai ánh sáng hoặc xoay sai không thuộc cờ vật thể. Do đó chưa tự tuyên bố qua gate. File `REVIEW_240.csv` có nhãn kỳ vọng, hai caption, cờ hỗ trợ và cột human để trống cho người dùng chấm. `CAPTIONS_240.md` chứa đủ240cặp đọc trực tiếp.

## Thời gian thực tế

- Sanity8:53.34giây gồm nạp model; vòng sinh14giây.
- Camera240:415.67giây = **6phút55.67giây** gồm nạp model; vòng sinh **6phút43giây** (~1.68giây/cặp).
- Job thành công từ vào function tới trả về:539.61giây = **8phút59.61giây**, gồm cài môi trường + sanity + camera + chấm/lưu.
- App thành công tạo19:47:31, stopped19:57:08 GMT+7; thời gian app gồm startup. Một lượt setup trước đó thiếu pandas ở kernel đã dừng trước Bước11 (19:45:47→19:47:06), không sinh caption/train. Không gộp thời gian setup lỗi vào thời gian inference.

Nếu ngoại suy máy móc tốc độ camera:1570×1.68giây≈44phút sinh câu. **Chưa dùng con số này để đặt trần fulltest**, vì natural captions dài hơn nhiều so với caption camera; cần đo đoạn OmniDiff đại diện chỉ sau khi người dùng chấm qua gate và cho tiếp tục.

## Protocol và artifact

- Nguồn notebook local `m3diff-nb-finetune.ipynb`, tạo bản `r64-camera-only.ipynb` chỉ thực hiện subset được yêu cầu. Cache source pinned4e346e5/base/dataset từ Volume; không tải lại hoặc sinh lại bộ240.
- Sửa thứ tự cài đặt để UV/PY được định nghĩa trước cell setuptools; sửa magic `%uv` thành `%pip`; bổ sung pandas cho kernel Python3.12 ngoài venvmodel3.10. PEFT0.4.0, torch2.2.2+cu121, transformers4.40.0, NumPy1.26.4. Xem executed notebook.
- A10 thực tế23028MiB; quant none, BF16, greedy, noFlash, defaultmax1024. Dùng loader notebook **merge LoRA**, không đổi sang FP32unmerged của các thí nghiệm r16. Basegenerationconfig penalty1.05; chưa instrument dump effective generation config runtime trong lượt này.
- Bước11 chặn trước nếu thiếu adapter hoặc không đủ338steps; chỉ chạy nhánh đã train. Theo cell gốc, config adapter đặt unfreeze_mm_vision_tower=True để nạp trọng số vision gốc. Không có cập nhật trọng số bằng training.
- So với `ft/eval/camtest_base.jsonl` đã có từ trước theo yêu cầu. Chưa chạy lại base cùng phiên; không gọi đây là same-GPU matched experiment.
- Raw240r64,240base,8sanity; câu hỏi240 và manifest; `camtest_compare.csv`480rows; timings; notebook executed; báo cáo/proxy summary. Kết quả trên Volume `m3diff/r64_camera_eval_20261102/`, raw r64 cũng ở `ft/eval/camtest_ft.jsonl`.
- Hai app: failedsetup `ap-LM5RfVgVU9BabhqHMuk0k8`, completed `ap-pON0QVAZCxOyq1ZxwNooiG`. Cả hai stopped/0task sau lần kiểm tra cuối. Chưa chạy OmniDiff full.
