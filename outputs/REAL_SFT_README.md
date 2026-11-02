# Thử nghiệm SFT caption trên dữ liệu thật

Script: `run_real_sft_modal.py`. Volume Modal: `m3diff/real_sft_pilot_v1`.

Chạy từ thư mục outputs:

```powershell
.\.modal-client\Scripts\python.exe -X utf8 -m modal run --detach .\run_real_sft_modal.py
```

Thử nghiệm so sánh bốn nhánh trên cùng 64 cặp test (32 Real, 32 Render): checkpoint công bố, checkpoint fine-tune tổng hợp cũ, SFT chọn mẫu ngẫu nhiên, SFT ưu tiên mẫu có CIDEr thấp trên train. Caption baseline được tái sử dụng từ lần đánh giá đầy đủ. Tham số sinh giữ nguyên: greedy, BF16, tối đa 1.024 token.

Hai nhánh mới bắt đầu từ checkpoint công bố, không nối tiếp checkpoint tổng hợp. Mỗi nhánh học 256 cặp: 128 cặp được chọn từ 256 ứng viên train và 128 cặp replay giống nhau. Nhánh hard lấy 64 ứng viên có CIDEr thấp nhất mỗi miền; nhánh random lấy ngẫu nhiên 64 mỗi miền. CIDEr được tính trên các caption train đã công bố, không dùng caption test để chọn mẫu hoặc sửa nhãn.

Mỗi nhánh train một epoch, LoRA r16/alpha32, LR 1e-5, batch1/gradient accumulation8, seed42. Vision và projector đóng băng; MDP và LoRA được cập nhật. Không sinh ảnh mới, không dùng LocateAnything, không DPO. Hai nhánh dùng cùng dữ liệu replay và ngân sách train.

Chỉ dùng đường dẫn `/train/` cho dữ liệu học. Không dùng chung ảnh giữa nhóm ứng viên và replay; ảnh test được loại khỏi train bằng đường dẫn. Tập test nhỏ được cố định trước khi chấm kết quả, loại ảnh đã dùng trong pilot LocateAnything và validation trước. Điều này chưa bảo đảm độc lập theo scene; không gọi đây là kết quả trên toàn benchmark.

CIDEr thấp là cách tự động tìm ứng viên khó; không khẳng định tất cả là lỗi thị giác hoặc đã được người gán nhãn kiểm tra. Các caption mục tiêu là annotation gốc của dataset. Một lần chạy với một seed chỉ cho bằng chứng thăm dò.

Checkpoint công bố đã được học từ bộ dữ liệu gốc; đây là continued SFT với cách chọn mẫu khác, không phải bổ sung một bộ nhãn mới hay đánh giá trên dữ liệu train chưa từng thấy. Nếu không cải thiện trên test, không nên suy từ train loss giảm rằng caption đã tốt hơn.

Ảnh train cần thiết được tải ở function CPU trước khi cấp GPU. Function GPU có timeout 90 phút, không tạo endpoint thường trực; container hạ sau khi function trả về. Khi hoàn tất, kiểm tra app đã dừng và tải `real_sft_results.zip`. Trọng số adapter vẫn lưu trên Volume, không đưa vào zip kết quả nhỏ.

Kết quả cần đọc: `metrics.json`, `comparison.json`, `mining_ranking.json`, `*_train.json`, `prepared.json`, `SUCCESS.json`, và `logs/`. Chỉ khi có `SUCCESS.json` và đủ caption của mọi nhánh mới coi lần chạy hoàn tất.
