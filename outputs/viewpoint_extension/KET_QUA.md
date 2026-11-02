# Kiểm tra tiếp: zoom-out và thay đổi nhỏ

**Kết luận: không dùng bộ căn chỉnh v1 để tự thay caption bằng “không đổi”. Có phản ví dụ rõ về ảnh đã bị sửa nhưng bộ chặn vẫn cho qua. Căn chỉnh gần đúng chuyển thành gợi ý; chỉ ảnh giống hệt sau giải mã mới được trả tự động “không khác biệt”.**

Đã giữ nguyên code/hash/ngưỡng v1 và kiểm tra 8 scene khác bộ diagnostic trước: 4 Real, 4 Render. Ảnh thuộc OmniDiff test đã được checkpoint gốc chạy trong toàn bộ benchmark trước đây; đây không phải dữ liệu ngoài hoàn toàn mới. Không gọi GPU hay sinh caption mới trong phép CPU này.

## Độ bao phủ trên 40 cặp không thay đổi vật

| Điều kiện | V1 chấp nhận không đổi / 8 |
|---|---:|
| identity | 8 |
| zoom_in_1p10 | 6 |
| zoom_out_reverse_1p10 | 0 |
| roll_8_safe | 6 |
| roll_minus8_zoom | 4 |

Zoom-out ở đây là đảo chiều cặp ảnh crop/zoom-in, không dựng thêm phần cảnh giả. V1 đòi ít nhất 95% ảnh đích nằm trong phần đối chiếu, nên zoom-out có vùng mới lộ ra bị fallback. Đó là giới hạn bao phủ, không phải bằng chứng model đã hiểu zoom-out sai.

## Thay đổi tổng hợp có bị bỏ qua?

Mỗi trường hợp có chỉnh sửa pixel biết chắc đã xảy ra. Đây là stress appearance tổng hợp, không được trình bày như tỷ lệ bỏ sót vật thể thật ngoài đời.

| Stress chính | V1 trả nhầm “không đổi” / 8 |
|---|---:|
| square32_delta16 | 8 |
| square8_invert | 0 |
| thin2x32_invert | 1 |
| brightness_plus8 | 0 |

| Vừa đổi hình học vừa sửa mảng màu 32×32 | V1 trả nhầm “không đổi” / 8 |
|---|---:|
| zoom_in_1p10 | 6 |
| roll_8_safe | 5 |
| zoom_out_1p10 | 0 |

Tổng stress chính bị chặn nhầm: **20/56**. Không nới hay dò lại ngưỡng trên các kết quả này.

Các stress nhạy hơn (mảng nhỏ +4 RGB, tăng sáng toàn ảnh +1, đổi một pixel) lưu riêng trong CSV. Chúng thăm giới hạn độ phân giải/dung sai; không dùng để khẳng định một khác biệt nhỏ đến vậy phải được mô tả trong caption ngữ nghĩa.

## Cặp tự nhiên

Đã xem ảnh trước khi đọc kết quả bộ chặn: 7 cặp có thay đổi rõ, 1 cặp quần áo có lẫn khung hình/che khuất chưa gán nhãn chắc. V1 không chặn nhầm cặp nào trong **7 cặp thay đổi rõ**. Điều này không xóa các phản ví dụ appearance tổng hợp, cũng không phải phép đo recall caption mới.

## Đã sửa pipeline

`safe_pipeline.py` giữ nguyên caption M3Diff cho mọi cặp không giống hệt pixel. Cờ `--registration-advice` chỉ ghi thông tin căn chỉnh, phần ảnh chung và gợi ý kiểm tra; không ghi đè caption. Không có cờ bật lại việc thay caption gần đúng trong bản này.

```powershell
python safe_pipeline.py --manifest pairs.json --image-root images --input captions.jsonl --output captions_safe.jsonl --audit review_flags.json
```

Để có gợi ý căn chỉnh, thêm `--registration-advice` và cài OpenCV theo README. Input/output/manifest/audit phải là tệp khác nhau. ID, thứ tự và metadata được giữ.

Đã chạy CLI đầu-cuối bằng CPU trên 5 trường hợp: giống hệt, zoom-out, thay mảng màu nhỏ, vừa zoom vừa sửa mảng, và cặp tự nhiên thêm người. Chỉ ảnh giống hệt bị thay caption; phản ví dụ mà v1 cho qua đã giữ nguyên caption gốc. `safe_check/SUCCESS.json` ghi bằng chứng. Chính sách cũng được áp dụng lên 128 feature đã lưu: không thay caption ở bất kỳ trường hợp không giống hệt nào.

## Ý nghĩa cho hướng cải thiện

Kết quả tích cực 14/18 → 5/18 trước đây vẫn là số đo đúng trên diagnostic cũ, nhưng không đủ để bật bộ chặn gần đúng tự động. Vấn đề còn lại là model phải học phân biệt thay đổi vật với thay đổi khung hình; một bộ so pixel có dung sai không thể chứng minh không có thay đổi ngữ nghĩa. Một pilot fine-tune bất biến góc/zoom được tách riêng ở `../invariance_sft/`, dùng ảnh train và không thay các kết quả CPU này.

Ảnh minh chứng có BEFORE / AFTER / chênh lệch pixel ×12. Ảnh chỉ minh họa phản ví dụ, không phải annotation vật thể. Toàn bộ thử nghiệm extension dùng CPU, các function đều có timeout và không triển khai endpoint thường trực.
