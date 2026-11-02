#12camera claims trên Realval: xem ảnh trước khi kết luận

Trợ lý đã xem đủ12board ảnh gốc A/B,captionr64vàreference. Khôngblind,không phải người chấm độc lập; chỉ mô tả,không gate. Kết quả theo **claim cụ thể của model**, gồm hướng zoom/xoay:2đúng,6sai,4không chắc.

- `real_val_pair_000627`:referenceghi scene same nhưng khung/kệ giày thực sự nghiêng toàn cảnh; claim xoay camera phù hợp. Không được dùng reference im lặng để gọi đây là falsecamera.
- `real_val_pair_000354`:panda và nền gỗ đều lớn/crop hơn, hỗ trợ mô tả zoom-in; model vẫn bỏ sót thay đổi tư thế/tre.
- `real_val_pair_000584`:reference nochange nhưng ảnh sau rộng hơn; r64nói zoom-in nên sai hướng, không phải bằng chứng cặp này hoàn toàn không có camera nuisance.
- 4ca chó/panda/bàn có thay đổi framing lẫn vị trí/tư thế không đủ rõ để tách loại camera được khẳng định:giữ uncertain.
- 6ca sai có claim không được hỗ trợ bởi nền/cấu trúc chung hoặc ngược hướng quan sát; lý do từng ca ởASSISTANT_ASSESSMENTS.json.

Các con số không suy rộng thành tỷ lệ falsecamera của toànReal100. Ngay cả claimcamerađúng cũng không có nghĩa caption đủ ý:vẫn có thể bỏ sót thay đổi vật thể và làm CIDEr giảm. Không kết luận nguyên nhân nội tại của model chỉ từ12ca.
