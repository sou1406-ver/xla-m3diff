# Tổng quan nghiên cứu

[← Trang chủ](../README.md) · [Kết quả](RESULTS.md) · [Thí nghiệm](EXPERIMENTS.md)

## Câu hỏi nghiên cứu

M3Diff có thể mô tả thay đổi vật thể chính xác hơn khi hai ảnh khác góc nhìn, zoom hoặc xoay hay không? Hai yêu cầu phải được đánh giá cùng nhau: giảm khẳng định sai và bảo toàn thay đổi thật.

## Luồng xử lý

**Hai ảnh → vision encoder → MDP / projector → language model → caption.**

Baseline dùng greedy. Nhánh MBR bổ sung 8 caption sampling và chọn một trong 9 câu theo mức đồng thuận; dùng base, không cập nhật weights. [Code chọn câu](../outputs/mbr_pilot_20261103/utility.py) và [code pilot sinh ứng viên](../outputs/mbr_pilot_20261103/benchmark.py).

## Các nhóm phương pháp

| Nhóm | Can thiệp | Mục đích |
|---|---|---|
| Baseline | Tái lập inference và metric từ checkpoint công bố | Tạo mốc đối chứng |
| Fine-tuning | Caption SFT với LoRA; một số vòng cập nhật MDP/projector | Phân biệt biến đổi camera và thay đổi thật |
| Decoding | Greedy so với consensus MBR | Chọn caption từ nhiều ứng viên |
| Diagnostics | Alignment, grounding, verifier, prompt, precision | Kiểm tra giả thuyết và nguồn lỗi |

Các vòng SFT khác nhau về dữ liệu và tham số trainable; không gộp tất cả thành LoRA-only. V2 cuối dùng LoRA + MDP/projector. Feature-consistency loss chưa được triển khai trong các vòng bàn giao; SCST thuộc repo tham khảo bên ngoài.

## Thiết kế đánh giá

- **Full test:** 803 Real + 767 Render; báo cáo từng miền riêng.
- **Val/pilot:** lựa chọn cấu hình theo protocol; không so trực tiếp với test khác cohort.
- **Camera/synthetic stress:** kiểm tra lỗi hình học và giữ thông tin thật; regex là proxy.
- **Review caption/ảnh:** nhiều bộ do assistant chấm, không phải nhãn người độc lập.

Cặp dùng chung ảnh nguồn hoặc nền có phụ thuộc thống kê. MBR full bootstrap theo nhóm ảnh liên thông. Synthetic 2D chưa chứng minh robustness với góc nhìn 3D thực.

## Câu hỏi còn mở

Cần đánh giá factuality độc lập, khả năng giữ thay đổi thật dưới biến đổi camera và chi phí suy luận. Feature consistency, region matching và kiểm chứng SCST là hướng đề xuất; không được coi là các phương pháp đã kiểm chứng tại đây.
