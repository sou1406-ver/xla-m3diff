# Chấm nội dung40cặp camera bằng trợ lý

Đã xem toàn bộ10contactsheet, mỗi sheet4cặp, gồm ảnh A/B và caption base/r64. Mẫu khóa bằng seed20261102 trước kết quả synth600:24camera-only (6mỗi loại) +16camera+object (8thêm,8xóa). Đây là **chấm bởi trợ lý, không phải nhãn người độc lập và không blind**. Không điền vào cột `human_*`; nhãn nằm ở `assistant_*` trong `ASSISTANT_REVIEW_40.csv`.

## Kết quả và tiêu chí

| Chỉ số trong mẫu đã chọn | Base | r64 |
|---|---:|---:|
| Khẳng định thay đổi vật không được phép bởi camera-only /24 |22rõ +1mơ hồ|2rõ|
| Không khẳng định thay đổi vật /24 |1|22|
| Giữ đúng sự kiện thêm/xóa đúng vật /16 |12|12|
| Gần đúng/một phần /16 |2|1|
| Sai hoặc bỏ sót /16 |2|3|

Camera-only: camera type/direction sai và ánh sáng sai không tính thành thay đổi vật; vẫn ghi là lỗi ở notes. Câu chỉ nói kích thước biểu kiến ("objects appear larger") không xem là khẳng định vật thực sự thay đổi kích thước. "Disappeared" với vật bị crop ra ngoài mà không rõ có ngụ ý bị xóa được giữ uncertain. Nhãn thứ hai đòi đúng loại thêm/xóa và category hoặc mô tả nhận diện vật duy nhất có căn cứ trên ảnh; gọi gần đúng category được tách partial. Không yêu cầu mọi chi tiết phụ của caption đều đúng mới tính đã giữ sự kiện mục tiêu; lỗi phụ nằm trong notes.

Do đó12/16không có nghĩa12caption hoàn toàn đúng. Không suy ra tỷ lệ này cho60hay240ca, không dùng như đánh giá ngoài phân phối. Mẫu nhóm nền cảnh lặp, cùng generator, reference/template hiển thị cho người chấm và mô hình dễ nhận ra từ văn phong.

## Regex sai ở đâu trong mẫu này?

- `rotate_L3_08`: base bịa ba người quay hướng, regex bỏ sót; r64 nói camera zoom làm vật **trông** lớn hơn, regex size gắn cờ vật thể nhưng rubric không tính physical change. r64 vẫn giải thích sai camera.
- `zoom_out_L1_12`: base bịa thay monitor/ghế, nhưng từ "replaced" không thuộc mẫu add/remove/color/move/size đã dùng nên bỏ sót.
- `rotate_L1_12`: base bịa thay keyboard và quay ghế; regex bỏ sót.
- `zoom_in_L1_10`: base nói hoa từ blue-and-white sang all-white, regex màu bỏ sót cấu trúc câu này. r64 cũng bịa đổi màu và bị regex bắt.
- `pan_L2_11`: base nói túi ngoài mép đã biến mất, trong ảnh nó bị crop. Giữ uncertain về physical removal thay vì ép positive/negative.
- `cam_remove_0021`: base mô tả vật trắng sọc đỏ/xanh biến mất, đúng vùng vật xe bị xóa dù không gọi tên car; regex category đánh trượt. Đây là ví dụ cần cho phép mô tả có thể nhận diện được vật.

Mẫu kiểm tra hỗ trợ tín hiệu giảm bịa vật của r64 nhưng **không xác thực134/180và43/180là tỷ lệ lỗi semantic thật**. Không thay bộ chấm/gate sau khi đã thấy kết quả để cứu model. Giữ điểm regex gốc và kết quả chấm bổ sung song song.

## Chất lượng dữ liệu cần ghi trong báo cáo

Nhiều cutout tổng hợp thiếu tự nhiên: `cam_add_0021` là fragment teddy khó nhìn ra category, `cam_add_0017` book là dải kệ sách, `cam_add_0020` teddy đi kèm fragment người, `cam_add_0001` book có cả điện thoại. Màu trong reference có thể khác cảm nhận ảnh (redteddy nhưng bearbrown/redscarf). Chấm trên category/sự kiện và ảnh, không coi nhãn tổng hợp là hoàn hảo về mọi chi tiết.

Toàn bộ nhãn, caption và lý do theo từng cặp: `ASSISTANT_REVIEW_40.csv`; tổng hợp machine-readable: `ASSISTANT_REVIEW_SUMMARY.json`; lựa chọn khóa: `REVIEW_SELECTION.json`; ảnh: `review_boards/` trong gói kết quả tải về/Volume (không đưa ảnh dataset lên Git).
