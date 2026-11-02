# Thử giới hạn độ dài caption

Thử nghiệm sau benchmark, không đổi điểm full hoặc mặc định1024 token. Không train thêm. Các ca dài được chọn từ lỗi đã biết, không phải mẫu ngẫu nhiên.

| Bản | Số ca | Natural khớp cache cũ | Natural chạm cap | Ca dài chạm cap |
|---|---:|---:|---:|---:|
| LoRA256 | 23 | 8/19 | 0 | 4/4 |
| base256 | 23 | 6/19 | 0 | 4/4 |
| base128 | 23 | 6/19 | 1 | 4/4 |

Cache natural cũ chạyA100, lượt mớiA10/A10G. Không dùng sự khác nhau với cache đó để kết luận giới hạn token làm mất fact. Không có timing1024 cùng lượt cho các ca dài nên không khẳng định hệ số tăng tốc.

Đối chứng cùng model/GPU: 18/19 caption natural ở128 token khớp hoàn toàn lượt1024 ngay trước đó. Các ca khác được lưu trong `CAP_AUDIT.json` để xem phần bị cắt.

Giới hạn token là tùy chọn vận hành, không sửa nhận diện xoay/zoom hoặc câu bịa. Giữ mặc định1024 cho tái lập; nếu chọn cap nhỏ cho demo cần chấp nhận khả năng thiếu mô tả.
