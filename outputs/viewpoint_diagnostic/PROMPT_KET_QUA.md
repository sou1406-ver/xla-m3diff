# Kiểm tra góc xoay/zoom M3Diff

So sánh checkpoint gốc với hai prompt cố định, **không train thêm**: prompt gốc và prompt nhắc phân biệt camera/crop với thay đổi vật.

12 scene, mỗi scene có 4 đối chứng cùng ảnh (giống hệt, zoom 1,10×, xoay 8° có crop an toàn, xoay −8° + zoom) và 1 cặp tự nhiên có thay đổi. Tổng 60 cặp × 2 prompt = 120 caption. Nguồn là ảnh đã xem trong các thử nghiệm trước; tách 6 scene dev/6 scene validation chỉ áp dụng trong lượt diagnostic này.

Caption được cùng lọc câu lặp, xáo tên prompt theo từng cặp. Trợ lý chấm và lưu trước khi giải khóa; không phải chấm mù độc lập bởi con người. Quy tắc và danh sách fact đã ghi trước khi đọc output mới.

## Báo sai thay đổi vật

Số cặp có ít nhất một khẳng định thay vật/màu/tư thế/số lượng/vị trí vật không được ảnh hỗ trợ. Camera/crop làm vật lệch hoặc khuất mép không tính là thay đổi vật thật. Khẳng định ánh sáng đổi được ghi riêng; trường hợp chỉ nói vị trí/kích thước trong khung nhưng không rõ đang nói vật dịch chuyển thật được chấm bảo thủ, có ghi chú.

| Nhóm | Số cặp | Prompt gốc | Prompt xét camera |
|---|---:|---:|---:|
| dev: ảnh giống hệt | 6 | 3 | 0 |
| dev: chỉ xoay/zoom | 18 | 15 | 11 |
| validation: ảnh giống hệt | 6 | 5 | 1 |
| validation: chỉ xoay/zoom | 18 | 14 | 12 |
| all: ảnh giống hệt | 12 | 8 | 1 |
| all: chỉ xoay/zoom | 36 | 29 | 23 |

### Kiểm tra tránh chuyển loại lỗi

| Validation | Prompt gốc | Prompt xét camera |
|---|---:|---:|
| Ảnh giống hệt nhưng nói có khác biệt /6 | 6 | 4 |
| Chỉ xoay/zoom nhưng khẳng định ánh sáng đổi /18 | 6 | 14 |
| Mô tả sai vị trí/kích thước trong ảnh /18 | 2 | 1 |
| Nêu rõ camera/framing đổi /18 | 0 | 0 |

Khẳng định ánh sáng đổi không gộp vào lỗi thay vật. Crop có thể đổi phân bố sáng toàn ảnh, nên phát biểu “ảnh sáng hơn” không tự chứng minh có đổi nguồn sáng. Cần đọc caption và ghi chú, không coi việc bớt nói vật đổi nhưng chuyển sang suy ánh sáng là đã hiểu hình học.

## Có bỏ sót thay đổi thật không?

Mỗi fact là một thay đổi cụ thể đã khóa trước, xem `scoring_rubric.json`. Classroom chỉ thay sáng và được ghi là illumination-only trong manifest.

| Nhóm | Tổng fact | Fact đúng: gốc | Fact đúng: xét camera | Cặp có khẳng định sai: gốc → mới |
|---|---:|---:|---:|---:|
| dev | 12 | 7 | 3 | 4 → 5 |
| validation | 10 | 2 | 3 | 6 → 5 |
| all | 22 | 9 | 6 | 10 → 10 |

## Kết luận

Prompt xét camera đạt điều kiện gợi ý trên diagnostic nhỏ này: giảm báo sai ở validation mà không giảm tổng fact đúng trên các cặp tự nhiên validation. Chưa đủ để thay cấu hình chính hoặc tuyên bố tăng năng lực hiểu ảnh.

Đây là phép biến đổi 2D, không mô phỏng camera đổi góc nhìn 3D. Xoay có kèm mức phóng tối thiểu để không sinh viền đen/ảnh giả; ma trận và scale thật lưu ở manifest. Mỗi miền chỉ 6 scene, tập validation chỉ 6 scene tổng cộng; các điều kiện trong cùng scene tương quan. Bootstrap theo scene mô tả bất định, không dùng để tuyên bố cải thiện tổng quát.

Mọi caption, điểm chấm, trường hợp sai và protocol có trong gói kết quả. Script Modal có timeout và tự trả GPU khi xong, không tạo endpoint thường trực.
