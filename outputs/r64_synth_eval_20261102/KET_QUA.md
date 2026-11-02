# r64: synth600 và chấm bổ sung40cặp camera — 02/11/2026

**Đã chạy đủ600cặp. r64 trượt cả gate camera sai và gate giữ từng loại thay đổi. Đã dừng A10; không chạy OmniDiff full1570.** Có cải thiện đo được ở nhiều loại tổng hợp, nhưng chưa có bằng chứng giữ chất lượng tổng thể.

## 1. Gate camera sai trên bộ không có biến đổi camera

Quy tắc trước kết quả: union `ft_common.CAM` và `m_view` của bộ chấm cũ, tối đa30/600.

- Union r64: **35/600=5.83%**, vượt5%.
- Union có2câu nói về camera là vật thể (color_L1_12,move_L3_29), không phải đổi góc chụp. Không đổi gate sau kết quả; báo riêng để tránh gọi nhầm35ca đều camera-motion hallucination.
- Regex camera chuyển động cụ thể `CAM`: **33/600=5.50%**. Ngay khi bỏ2câu thiết bị, vẫn vượt5%.
- Trong33ca: add1,remove2,size1,light19,same4,jpeg6. Đặc biệt19/90cặp chỉ đổi sáng bị r64 nói camera;10/60đối chứng same/jpeg cũng vậy.
- Base `CAM`0/600; broad`m_view`28/600 có nhiều cụm nhìn về camera/thiết bị, không được gọi28ca đó đều bịa góc chụp.

Ví dụ light_L1_04 chỉ đổi sáng nhưng r64 nói "The camera has rotated slightly clockwise." `remove_L1_15` xóa vật nhưng chỉ nói perspective shiftedleft. Raw và toàn bộ flags lưu trong `r64.jsonl`, `r64_camera_flags.json`.

## 2. Gate không giảm từng loại: đổi màu trượt

Chấm lại cả raw base có sẵn và r64 bằng cùng script. Mỗi loại90cặp. Đây là nhận đúng **từ khóa loại thay đổi**, không tương đương mọi câu đúng về vật/màu/hướng.

| Loại | Base | r64 | Giữ >=base? |
|---|---:|---:|---|
| Add |86/90=95.6%|90/90=100.0%|Có|
| Remove |83/90=92.2%|87/90=96.7%|Có|
| Color |69/90=76.7%|61/90=67.8%|**Không**|
| Move |41/90=45.6%|61/90=67.8%|Có|
| Size |23/90=25.6%|60/90=66.7%|Có|
| Light |60/90=66.7%|63/90=70.0%|Có|

Điểm đúng cả loại+tên vật: add59→71/90;remove49→64;color50→47;move26→49;size14→50. r64 không phải suy giảm đồng loạt: thêm/xóa/dời/kích thước tốt hơn theo bộ chấm này. Nhưng điều kiện mỗi loại đều không thấp hơn base không đạt vì color.

Đối chứng không có thay đổi ngữ nghĩa vẫn yếu: same30cặp, cờ thay đổi giả20→25;JPEG30cặp24→25. Đây là proxy gốc của scorer; không đổi metric để né gate. Điểm thông tin đúng có thể tăng đồng thời với lỗi khác, không suy ra caption hoàn toàn đúng.

## 3.40cặp camera được xem ảnh/caption

Đã chọn ngẫu nhiên phân tầng và khóa trước kết quả600:24camera-only +16camera+object. Trợ lý đã xem đủ40cặp trên10board. Đây không phải nhãn người độc lập; không blind; không điền cột human.

- Camera-only: base22ca bịa vật rõ,1không,1uncertain; r64 2ca rõ,22không.
- Camera+object: giữ đúng sự kiện mục tiêu12/16ở mỗi model; partial base2/r641; sai/bỏ sót base2/r643. Không diễn giải thành cả hai12caption hoàn toàn đúng.
- Regex có cả bỏ sót (thay thế vật/quay người/đổi màu theo cấu trúc khác) và bắt nhầm ("objects appear larger" chỉ là kích thước biểu kiến). Không dùng mẫu24để thay134/180→43/180thành tỷ lệ semantic đã được xác thực.

Chi tiết: `ASSISTANT_REVIEW.md`, `ASSISTANT_REVIEW_40.csv`, `ASSISTANT_REVIEW_SUMMARY.json`, `REVIEW_SELECTION.json`. Board trong gói kết quả/Volume, không đưa ảnh dataset lên Git. Một số cutout/reference không tự nhiên hoặc màu không khớp cảm nhận; đã ghi vào note.

## 4. Thời gian, phạm vi và quyết định

- A10 thực tế23028MiB, không quantize; notebook loader mergeLoRA,BF16,greedy,maxdefault1024,noFlash, cùng đường nạp đã dùng camera240.
-600caption: **18phút44giây vòng sinh**, **19phút19.31giây gồm nạp model**.
- Job thành công tổng **20phút58.55giây**, gồm setup,tạo40board,suy luận,chấm,lưu. Không có train hay retry job này.
- App `ap-2CV3a5lYJxmNolrErOLRlI` stopped20:38:39 GMT+7; bằng chứng `FINAL_APPS.json` stopped/0task. Kết quả trên Volume `m3diff/r64_synth_eval_20261102`; raw cũng ở `ft/eval/synth_ft.jsonl`.
- Base tái dùng caption lịch sử và chấm lại cùng scorer, chưa sinh base cùng phiên này. Không gọi đây là matched same-GPU inference.
- `gate_result.json`:camera_fail,color_retention_fail. Không chạy50OmniDiff,không full1570,không tiêu tiếp để dùng hết credit. Không có điểm CIDEr OmniDiff cho r64 để viết "không mất điểm OmniDiff".

Kết luận báo cáo phù hợp: **r64 có tín hiệu giảm bịa vật trên camera tổng hợp và tăng nhận dạng nhiều loại thay đổi tổng hợp, nhưng còn nhầm camera khi chỉ đổi sáng/ảnh không đổi, giảm nhận dạng đổi màu và chưa đạt gate đã đặt.** Giữ base mặc định; không gọi r64 là cải thiện tổng thể hoặc bằng chứng hiểu góc chụp thật3D.
