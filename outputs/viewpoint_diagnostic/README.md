# Diagnostic xoay ảnh / zoom của M3Diff

**Cập nhật:** kiểm tra mở rộng phát hiện false suppression trên thay đổi appearance nhỏ. Không dùng chế độ approximate registration của bản v1 để tự ghi caption. Bản hiện tại ở `../viewpoint_extension/safe_pipeline.py` chỉ dùng căn chỉnh gần đúng như gợi ý; xem `../viewpoint_extension/KET_QUA.md`.

So sánh một prompt gốc với một prompt nhắc model phân biệt camera/crop và thay đổi vật, sau đó thử bộ chặn không-thay-đổi dựa trên căn chỉnh ảnh. Không train thêm, không tìm nhiều prompt rồi chọn trên cùng tập đánh giá.

`KET_QUA.md` là kết luận căn chỉnh; `PROMPT_KET_QUA.md` là thử prompt. `protocol_locked.json` khóa ảnh, phép biến đổi, prompt và điều kiện lựa chọn trước output; `scoring_rubric.json` khóa tiêu chí chấm và fact tự nhiên. `masked_assessments.json` là điểm trợ lý ghi khi chưa mở khóa tên prompt; `decoded_assessments.json` là bản giải khóa. Đây là đánh giá hỗ trợ nghiên cứu, chưa có người gán nhãn độc lập.

## Thiết kế

12 scene khác nhau, 6 Real và 6 Render. Mỗi scene dùng 4 cặp đối chứng không thay đổi vật (identity, zoom 1,10×, roll +8°, roll −8° + zoom) và 1 cặp tự nhiên. Roll có phóng/crop tối thiểu để mọi pixel output lấy từ ảnh gốc, không sinh viền đen hay điền nền giả. `manifest.json` lưu ma trận affine, scale thực tế, ảnh nguồn, scene và dev/validation. Tổng 60 cặp, 120 lượt sinh caption.

6 scene dev và 6 scene validation không trùng nhau trong diagnostic này. Nguồn ảnh đã được xem ở nghiên cứu trước, nên không phải test độc lập mới. 2D roll không thay thế được camera đổi góc 3D. Cặp classroom chỉ đổi độ sáng; báo cáo theo fact riêng, không coi đó là vật bị thêm/bớt.

## Chạy lại trong workspace hiện tại

```powershell
python prepare.py
..\.modal-client\Scripts\python.exe -X utf8 -m modal run --detach run_modal.py
..\.modal-client\Scripts\python.exe -X utf8 -m modal volume get m3diff viewpoint_diagnostic_v1/results.zip results.zip --force
Expand-Archive -LiteralPath results.zip -DestinationPath results -Force
```

`prepare.py` dùng 24 ảnh gốc và metadata đã có trong `../curated_sft/blind_images/originals`, `blind_image_selection.json`, `image_only_observations.json`. Dùng Pillow. Script GPU dùng Volume Modal `m3diff` với cache model/repo đã dựng trước, không phải trình cài từ tài khoản trống. Mỗi function timeout 3.600 giây và tự trả GPU khi hoàn thành, không có deployment thường trực. Khi đổi prompt/ảnh/config phải đổi run directory, không trộn với dự đoán đã lưu.

Sau khi xem các ảnh trong `boards/`, đọc **chỉ** `results/masked_predictions.json`, ghi điểm theo rubric rồi mới mở `results/mask_key.json`. Chạy `python report.py` để giải khóa, tính báo sai, fact đúng và bootstrap theo scene. Không dùng chính kết quả này để sửa điểm chấm hoặc dò prompt mới. `review.csv` có thể dùng cho người rà độc lập. Gói `../m3diff_viewpoint_previews.zip` chứa ảnh preview JPEG, không thay thế PNG dùng cho inference ở dataset/cache Modal.

Caption mỗi nhánh được lọc câu lặp giống nhau trước khi chấm; cả caption raw lẫn bản hiển thị đều lưu. Không dùng CIDEr với câu no-change tự viết làm nhãn vàng vì độ khớp từ không đo trực tiếp hallucination.

## Áp dụng prompt thử nghiệm

Prompt chính xác nằm trong `protocol_locked.json`, mục `arms.camera_aware`. Dùng nguyên cặp ảnh ở thứ tự before/after. Việc prompt nghe hợp lý không bảo đảm hiệu quả; chỉ dùng làm cấu hình chính nếu kết quả và kiểm tra riêng của nhóm ủng hộ.

## Bộ chặn bằng căn chỉnh ảnh

Kết quả mới ở `registration_results.json`. `registration_protocol.json` khóa ngưỡng sau khi chỉ xem feature của 6 scene dev, trước khi tính feature validation. `registration_*_features.json` giữ feature SIFT/RANSAC và sai khác pixel; không dùng scene ID hoặc đáp án để ra quyết định. `registration_stress_decisions.json` ghi 18 kiểm tra đổi mảng nhỏ/nét mảnh/tăng sáng.

`registration_gate.py` tính feature và quyết định; `apply_registration_gate.py` là CLI dùng ngay. Mặc định chỉ bắt ảnh giống hệt sau giải mã, cần NumPy/Pillow và không cần OpenCV:

```powershell
python apply_registration_gate.py --manifest manifest.json --image-root dataset --input baseline_clean.jsonl --output identity_guarded.jsonl --audit identity_audit.json
```

Căn chỉnh gần đúng cần chủ động bật `--mode registration --protocol registration_protocol.json`. Môi trường đối chiếu: `numpy<2`, `Pillow==11.1.0`, `opencv-python-headless==4.10.0.84`. CLI giữ nguyên thứ tự/metadata và caption fallback. `try_no_change` có thể gọi trước inference để bỏ qua việc sinh caption khi đủ điều kiện; bản đánh giá này dùng caption đã lưu, không chạy lại GPU.

Chạy lại phép CPU trong workspace hiện tại:

```powershell
..\.modal-client\Scripts\python.exe -X utf8 -m modal run --detach run_registration_cpu.py --partition dev
# Chỉ chọn/khóa ngưỡng trên dev; không chạy lại lock_registration.py sau khi xem validation.
..\.modal-client\Scripts\python.exe -X utf8 -m modal run --detach run_registration_cpu.py --partition validation
python report_registration.py
```

`check_pipeline_cpu.py` kiểm tra CLI thực tế trên đủ 60 ảnh và đối chiếu dự đoán từ chính sách đã khóa, không dùng GPU. `CLI_CHECK_SUCCESS.json` xác nhận caption, metadata và thứ tự input. Gói zip không chứa trọng số, môi trường Python hoặc PNG dataset lớn; ảnh inference vẫn ở workspace và Volume `m3diff/viewpoint_diagnostic_v1/dataset`.

Ngưỡng chỉ là heuristic, còn có thể bỏ sót thay đổi nhỏ/ít tương phản hoặc ngoài phần ảnh chung; chưa kiểm tra góc nhìn 3D. Không gọi căn chỉnh gần đúng là chứng minh hai scene giống nhau. Phải kiểm tra trên scene mới trước khi bật cho toàn hệ thống.
