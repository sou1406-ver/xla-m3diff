# Báo cáo tổng hợp M3Diff ngày04/11/2026

Bản Word hoàn chỉnh trên máy: outputs/bao_cao_btl_20261104/BAO_CAO_BTL_M3DIFF.docx,18trang và8hình nhúng; đã render và xem toàn bộ trang. Markdown trên máy có cùng hình trong assets/. Repo chỉ chứa văn bản, caption, manifest, script và QA metadata; không đưa ảnh dataset, file Word nhúng dataset, weights hoặc môi trường lên Git.

Đọc BAO_CAO_BTL_M3DIFF.md để theo dõi từ tái lập baseline đến căn chỉnh, các vòng SFT, r64/V2, MBR val/full và camera partial174. Giới hạn: không có CIDEr OmniDiff V2; camera MBR thiếu cả60cam+object; gain Render không phải bằng chứng hiểu hình học. Assistant review không phải nhãn người độc lập. Tám ca được chọn có chủ đích để giải thích cả thành công lẫn thất bại.

## Tái tạo báo cáo từ tài nguyên đã có

Giữ layout outputs/ song song giữa các nhánh như hiện có. Cần source metric/caption JSON/CSV trong repo, ảnh viewpoint_diagnostic/dataset và failure_previews trong cache cũ, quyền đọc Modal Volume m3diff cho12ảnh được chọn, Python có python-docx/Pillow/lxml và Python Modal SDK. Đây không phải bản clone tự chứa mọi tài nguyên.

1. Chạy prepare_evidence.py bằng Python để chọn lại8ca từ raw/report đã lưu.
2. Chạy fetch_evidence.py bằng Python đã cài Modal SDK và xác thực đúng workspace. Script chỉ đọc Volume, không tạo app hayGPU.
3. Chạy make_figures.py rồi build_report.py bằng bundled Python để tạo assets, Word và Markdown.
4. Render Word với render_docx.py của skill Documents. Lần tạo này bundled LibreOffice không có nên dùng native Word read-only export và packaged rasterize; xem RENDER_BACKEND_NOTE.json.
5. Xem đủ mọi trang và chạy validate_report.py. Không coi kiểm tra XML thay cho xem ảnh trang.

CASES.json và IMAGE_SOURCES.json ghi ID/đường dẫn Volume/hash; EVIDENCE_MANIFEST.json giữ hash metric; FINAL_REPORT_QA.json giữ hash Word và18PNG đã xem. Không có model inference, train hay thử ngưỡng mới trong việc làm báo cáo. Báo cáo lịch sử trong bao_cao_m3diff_chi_tiet/ được giữ nguyên.
