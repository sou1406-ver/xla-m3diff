# Vòng v2 cuối cùng — gate khóa trước train/kết quả v2

Trạng thái: chỉ khóa protocol/scorer; chưa chọn200val, chưa train hoặc chạy GPU trong bước này. Đúng một ứng viên v2 từ base M3Diff gốc; không tìm checkpoint theo điểm test, không đổi gate, không v3. Trượt bất kỳ gate bắt buộc nào thì dừng và ghi kết quả âm. Qua toàn bộ gate mới được xét full1570; chưa có kết quả full thì không nói giữ điểm OmniDiff.

## Gate bắt buộc: tất cả phải đạt

| Bộ | Điều kiện |
|---|---|
| Camera240:180camera-only | Cờ thay đổi vật thể theo scorer cũ **<=54/180** |
| Camera240:60camera+object | Đúng đồng thời từ khóa loại thêm/xóa và tên vật theo scorer cũ **>=35/60** |
| Synth600 không camera | Câu được detector camera-motion đã khóa gắn cờ **<=30/600 (5%)** |
| Synth600, mỗi loại90 | Số đúng loại của v2 **>= số đúng của base −2**, riêng từng add/remove/color/move/size/light |
| OmniDiff val200,100Real+100Render | **CIDEr(v2)−CIDEr(base)>=−1.0 điểm ×100 ở TỪNG miền**, tính CIDEr riêng miền |

Tất cả dùng so sánh bao gồm dấu bằng. Không làm tròn trước quyết định; CIDEr−1.01 trượt,−1.00đạt. Tolerance là **mức suy giảm được chấp nhận theo quyết định thực dụng**, không phải chứng minh nhiễu hoặc noninferiority thống kê. Có thể bootstrap theo nhóm ảnh/cảnh để mô tả độ chắc chắn; CI không thay thế hoặc cứu gate. Không diễn giải các cặp có chung ảnh là độc lập.

Mốc600 đã đọc bằng scorer cố định: add86,remove83,color69,move41,size23,light60 trên90mỗi loại. Vì vậy floor tương ứng84,81,67,39,21,58. Mốc camera r64:43/180 và43/60; base134/180và35/60 đều là proxyregex, chưa được coi là tỷ lệ semantic thật. Ngưỡng54là mức nới xấp xỉ25% so43; không phải mốc mới của base.

## Scorer camera và loại trừ khóa trước

`camera_detector.py` dùng regex CAM gốc làm bộ phát hiện, sau khi mask CHỈ danh từ camera chỉ thiết bị trong ngữ cảnh đã liệt kê. Không dùng `m_view` rộng làm gate vì nó bắt cả "facing the camera" và thiết bị. `m_view` có thể báo riêng.

Danh sách loại trừ cố định ở code: camera có tính từ màu/kỹ thuật (black,white,red,blue,green,yellow,gray/grey,brown,pink,silver,golden,digital,security,surveillance,video,web,DSLR,CCTV); hoặc camera theo ngay bởi cụm vị trí on/in/under/above/beside/behind/near/next to/in front of. Chỉ mask chữcamera, không loại cả câu: một câu vừa nhắc máy ảnh trên bàn vừa nhắc góc chụp đổi vẫn phải bị gắn cờ camera-motion. Không thêm exception theo ID/caption sau khi thấy v2.

Hai ca regression bắt buộc lấy nguyên văn từ r64:color_L1_12 vàmove_L3_29. Test thêm blackcamera,securitycamera,facingcamera, cụm camera-motion hợp lệ, và câu trộn thiết bị+viewpoint. Detector vẫn là heuristic: có thể hiểu sai phủ định và cú pháp chưa bao phủ; giữ raw predictions và chấm bổ sung, không sửa scorer sau kết quả để thay quyết định gate.

Scorer vật thể/loại thay đổi giữ nguyên snapshot `score_captions_frozen.py`, `ft_common_frozen.py`, `score_camera_frozen.py`; không đổi định nghĩa sau kết quả. Chấm trợ lý/người phải ghi tác giả, bất định và giữ riêng với điểm proxy. Zoom-in/out báo riêng theo từng loại; xoay/pan caption chung chỉ kiểm tra nhận biết camera thay đổi, không tuyên bố sửa đúng hướng. Bộ test240giữ nguyên, không sửa reference để khớp caption train mới.

## Trước khi train

1. Khóa200val,100mỗi miền bằng seed và manifest/hash, kiểm tra trùng ảnh với train/những lượt đã xem; ghi rõ mức phơi nhiễm. Không dùng test1570để chọn công thức. Chạy base/r64 cùng phiên/code/decoding để đo retention trước, log effective generation config và provenance. Định nghĩa đánh giá suy giảm r64 và chốt tỉ lệ replay cụ thể TRƯỚC train v2; không suy ra nguyên nhân từ một metric đơn lẻ.
2. Chốt datasetmanifest, số cặp độc lập, lượt lặp, caption recipe (light/same/JPEG khoảng300mỗi loại, tăng color, caption camera chung cho roll/pan, giữ zoomdirection), replay và steps. Các số này vẫn là thiết kế cần audit, không có nghĩa đã triển khai. Một lần train v2; giữ settings r64 nếu không có lý do được ghi trước.
3. Chốt budgetcap từ throughput/account còn lại trước GPU. Dự toán5–6đô không phải giá cố định hay chỉ thị dùng hết credit. Giải phóng GPU giữa các lượt, lỗi setup có thể sửa nhưng không dùng "sửa lỗi" để lén tạo ứng viên huấn luyện mới.
4. Sau train:camera240+synth600+val200, cùng scorer; base/v2valcùng phiên/code/precision/decoding. Thiếu case/NaN/provenance sai không được tính pass. Không lấy kết quả r64 cũ thay cho v2 hoặc đổi sampler val sau khi xem điểm.

Giới hạn bất kể kết quả: camera train/test cùng generator2D, nhiều background lặp và nhãn/cutout không hoàn hảo. Không chứng minh hiểu viewpoint3D thật, không chứng minh generalized improvement bằng điểm từ khóa.
