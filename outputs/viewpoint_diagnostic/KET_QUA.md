# Kết quả tiếp theo: kiểm tra camera trước M3Diff

**Cập nhật sau kiểm tra mở rộng:** v1 bỏ sót 20/56 stress appearance chính trên 8 scene khác, gồm cả ca vừa xoay/zoom vừa sửa vùng nhỏ. Không dùng căn chỉnh gần đúng để tự thay caption. Chính sách mới chỉ tự trả “không đổi” khi ảnh giống hệt sau giải mã; phần gần đúng chỉ gợi ý. Xem [báo cáo mở rộng](C:/Users/phuc1/Downloads/xla/outputs/viewpoint_extension/KET_QUA.md). Các số dưới đây là kết quả lịch sử trên diagnostic ban đầu.

**Có tín hiệu tốt hơn ở bộ kiểm tra có kiểm soát: căn chỉnh ảnh + kiểm tra phần còn khác giúp tránh một số caption bịa khi chỉ xoay/zoom. Chưa đủ bằng chứng cho đổi góc nhìn 3D hoặc dữ liệu mới ngoài bộ này.**

## Cách đang kiểm tra

Ảnh giống hệt từng pixel sau giải mã được trả “không có thay đổi”. Với ảnh khác, SIFT/RANSAC ước lượng xoay/phóng/tịnh tiến toàn ảnh; chỉ khi phần ảnh chung khớp rất sát và không còn vùng sai khác rõ thì trả mô tả đổi khung hình. Trường hợp không đủ chắc giữ nguyên caption checkpoint M3Diff gốc sau lọc câu lặp. Không cập nhật trọng số, không dùng LocateAnything, không thay bằng prompt mới.

Ngưỡng chọn trên 6 scene dev rồi khóa trước khi tính 6 scene validation. Những cảnh furniture nhiều chi tiết bị bỏ qua thay vì nới ngưỡng cho qua. Kiểm tra thêm 18 ảnh có thay đổi tổng hợp: đảo màu mảng 8×8, nét 2×32 và tăng sáng RGB +8. Các stress này kiểm tra bộ chặn, không đại diện một benchmark thay đổi vật tự nhiên.

## Kết quả bộ căn chỉnh

| Nhóm | Chỉ xoay/zoom được nhận ra | Ảnh giống hệt nhận ra | Cặp thay đổi thật bị trả nhầm “không đổi” |
|---|---:|---:|---:|
| Dev | 15/18 | 6/6 | 0/6 |
| Validation | 12/18 | 6/6 | 0/6 |
| Tổng | 27/36 | 12/12 | 0/12 |

| Lỗi bịa thay đổi vật | Trước | Sau bộ căn chỉnh |
|---|---:|---:|
| Validation: chỉ xoay/zoom | 14/18 | 5/18 |
| Validation: gồm cả ảnh giống hệt | 19/24 | 5/24 |
| Tổng: chỉ xoay/zoom | 29/36 | 6/36 |
| Tổng: gồm cả ảnh giống hệt | 37/48 | 6/48 |

Stress có thay đổi tổng hợp bị chặn nhầm: **0/18**.

Mức bao phủ các cặp xoay/zoom-in khác nhau theo miền: Real **9/18**, Render **18/18**. Các trường hợp còn lại giữ caption M3Diff, không tự ép thành không đổi.

Bộ căn chỉnh đạt điều kiện cố định trong diagnostic này. Cả 12 caption trên cặp tự nhiên được giữ nguyên từng ký tự sau lọc lặp; vì vậy nó không làm mất thêm thay đổi thật trong mẫu đã thử, nhưng cũng chưa sửa các lỗi sẵn có của M3Diff trên các cặp đó.

Đây là giảm báo sai nhờ pipeline nhận biết một số cặp không đổi, không phải model đã học hiểu góc nhìn tốt hơn. Các câu do bộ chặn thay được đánh giá theo nguồn ảnh/phép biến đổi đã biết, không cần nhờ model tự chấm nó. Các caption fallback giữ điểm chấm trực quan đã lưu trước đó.

## Lượt thử prompt

Đã chạy 120 caption trên 60 cặp (hai prompt). Ở validation, lỗi nói vật thay đổi giảm 19/24 → 13/24, nhưng khẳng định ánh sáng đổi tăng và không caption nào nêu camera/framing. Tổng fact đúng trên 12 cặp tự nhiên giảm 9/22 → 6/22. Vì vậy chưa dùng prompt xét camera làm mặc định. `PROMPT_KET_QUA.md` có bảng đầy đủ.

## Dùng mã

Mặc định an toàn về nội dung ảnh: chỉ bắt ảnh giống hệt, không dùng SIFT.

```powershell
python apply_registration_gate.py --manifest manifest.json --image-root dataset --input baseline_clean.jsonl --output identity_guarded.jsonl --audit identity_audit.json
```

Thử căn chỉnh gần đúng bằng cờ `--mode registration --protocol registration_protocol.json`, cần OpenCV. Có thể gọi `try_no_change(before, after, mode, thresholds)` trước bước sinh caption; nếu trả fallback thì chạy M3Diff như cũ. Bản đánh giá hiện tại tái sử dụng caption đã sinh, không chạy lại GPU để tiết kiệm credit.

## Giới hạn cần ghi trong báo cáo

- Chỉ 12 scene, ảnh đã được xem trong các thử nghiệm trước; validation chỉ tách scene trong diagnostic này, không phải test mới độc lập. Người chấm là trợ lý Codex, chưa có người gán nhãn độc lập.
- Xoay 2D có kèm crop an toàn, zoom-in nhỏ 1,10×; chưa kiểm tra zoom-out, 3D viewpoint/parallax hoặc zoom lớn. Ảnh nhiều chi tiết và trường hợp không đủ khớp sẽ fallback.
- Kiểm tra ở tối đa 1.024 pixel cạnh dài và có dung sai màu: vẫn có thể bỏ qua thay đổi rất nhỏ/ít tương phản hoặc nằm ngoài vùng chung. 18 stress chưa bao phủ mọi kiểu thay đổi; không gọi đây là chứng minh “không có thay đổi”.
- Ngưỡng cần kiểm tra lại trên tập scene mới, đặc biệt vật nhỏ và đổi sáng nhẹ, trước khi bật căn chỉnh gần đúng cho toàn bộ hệ thống. CLI mặc định chỉ bật so ảnh giống hệt.

Tất cả job GPU và CPU của lượt thử đã kết thúc. Không có endpoint hay lịch chạy thường trực.
