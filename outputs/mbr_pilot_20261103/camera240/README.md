# Camera240 MBR — khóa trước lượt chạy

Ủy quyền mới của user: chỉ base gốc, greedy mới + 8 mẫu cùng phiên; cấu hình và train-IDF giữ từ full1570. Không train, không adapter, không retry/resume. A10 hard4200s, process watchdog4080s (gồm cài môi trường/load); GPU4CPU32GiB rate1.5452USD/h, hard GPU≈1.803USD; CPU scorer240s và controller4590s, startup/scaledown/reconciliation buffer, tổng reservation1.95USD dưới trần2USD. Credit snapshot26.09/30USD, 0app chạy. Không mua credit.

240 ID/manifest/scorer giữ nguyên hash; batch2 cố định, seed20261105+SHA256(ID)%1000000, cap1024, bf16 cả MDP/projector. Clean/generate/measured AST khớp val200. MBR consensus9 ứng viên, train-IDF PTB cố định; nhãn camera chỉ mở sau selection. Không chọn theo scorer/ref. File REVIEW dùng nhãn ft để tương thích scorer cũ, ở lượt này ft nghĩa MBR không phải fine-tune.

Báo matched180 camera-only: cờ vật thể, nhắc camera, hướng;60 camera-object: đúng loại+tên và nhắc camera; kèm độ dài, thời gian, raw9candidates. Regex chỉ proxy, không gọi tỉ lệ semantic người chấm. Đây chẩn đoán bổ sung trên test tổng hợp đã từng xem, không phải blind holdout hay chứng minh robustness3D. Không đặt lại gate SFT cho decoder này; báo mọi kết quả, không tự promotion. Không giảm cờ không chứng minh lỗi ở vision.

Bộ600 chưa admit: sau camera phải đối soát billing, đủ≥2.50USD thực tế ước tính có đệm, và dự báo measured upper nằm trong số dư an toàn. Không đủ thì dừng. Timeout/partial/error không chạy lại.
