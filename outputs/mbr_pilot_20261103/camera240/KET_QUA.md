# MBR camera: kết quả một phần174/240

**Chưa có bằng chứng MBR cải thiện đáng kể lỗi camera.** Cờ thay đổi vật thể giảm6/174, camera vẫn không được nhắc ở câu được chọn. Đây là chẩn đoán partial, không phải kết quả đầy đủ camera240.

| Regex proxy trên174 cặp camera-only | Greedy mới | MBR |
|---|---:|---:|
| Cờ thay đổi vật thể |127/174 (73.0%)|121/174 (69.5%)|
| Nhắc camera |0/174|0/174|
| Đúng hướng camera |0/174|0/174|
| Số từ trung bình |50.64|42.20|
| Trung vị số từ |42|38|

Giảm3.45 điểm phần trăm;15 cặp hết cờ,9 cặp phát sinh cờ. McNemar mô tả p≈0.31, chưa tính phụ thuộc giữa ảnh; không dùng để tuyên bố cải thiện có ý nghĩa. Caption ngắn hơn16.7%; có thể ảnh hưởng số cờ, chưa chứng minh nguyên nhân. Detector cũ chỉ bắt2/1566ứng viên thuộc2cặp có nhắc camera, cả hai không được MBR chọn. Đây là giới hạn của pool ứng viên trên detector này, không chứng minh lỗi nằm tại vision.

| Điều kiện | Hoàn thành | Thiếu |
|---|---:|---:|
| Zoom in |45|0|
| Zoom out |45|0|
| Rotate |45|0|
| Pan |39|6|
| Camera+add |0|30|
| Camera+remove |0|30|

**Khả năng giữ đúng loại+tên vật: chưa đo được**, vì thiếu toàn bộ60cặp đó; không diễn giải0/0 là0% hay đạt gate. 174cặp là prefix theo thứ tự, không phải mẫu ngẫu nhiên;89bg_source paths khác nhau không bảo đảm89scene độc lập. Regex chưa có nhãn người, synthetic2D không chứng minh3D robustness.

Job GPU bị hủy trước timeout: provider ghi cancellation00:23:14và00:24:54–56 ngày04/11GMT+7; GPU_DONE wall2985.84s≈49m46. Không xác định được nguồn phát lệnh hủy, không gọi đây là preemption/timeout nếu chưa có bằng chứng. Không GPU retry. PIPELINE_DONE/GEN_DONE gốc không được ghi; giữ GPU_DONE và log nguyên. Đã xác minh provider0container trước chấm CPU, và app CPU dừng10:05:21GMT+7.

CPU partial scorer dùng selector/train-IDF/frozenregex cũ, chỉ sửa denominator/assertion để báo phần hoàn chỉnh. Do parent bị hủy trước PIPELINE_DONE, cho phép proof0container thay cho receipt đó; không giả trạng thái full. Source raw SHA256 ae3ded84e44e3e83e17c82b8c9b4e11ffb84696151be1f47bd2cd82d4c0e25cd;174IDs/seeds/9candidates/selection tie/bytescopy đã kiểm chứng.

Billing10:05GMT+7: original app1.30143788USD, waiterCPU0.00040347USD; CPU chấm cuối chưa hiện trong hourlyreport, thêm tối đa~0.03USD cho240s4CPU8GiB. Toàn vòng dưới2USD. Workspace consumption27.38/30USD, còn khoảng2.62USD có độ trễ; giữ đệm, không chạy600 hay jobGPU mới.

Đọc cùng full1570: MBR cải thiện Render CIDEr(+3.62, CI[+1.09,+5.98]), Real chưa thấy lợi ích(−0.22). Kết luận phù hợp là cải tiến giải mã có lợi trên Render; chưa giải quyết được lỗi camera và chưa kiểm tra bảo toàn thay đổi vật thể trong lượt camera này. Giữ basegreedy mặc định.
