# Chẩn đoán, grounding và alignment

[← Mục lục nghiên cứu](../README.md) · [Kết quả tổng hợp](../../docs/RESULTS.md)

Các phép thử kiểm tra nguồn lỗi; không đồng nghĩa giải pháp đã được xác nhận.

| Artifact gốc | Nội dung / kết luận |
|---|---|
| [precision_audit](../../outputs/precision_audit/) | BF16 merge so với FP32 unmerged |
| [prompt_probe](../../outputs/prompt_probe/) | Crossed prompt probe |
| [locateanything_demo](../../outputs/locateanything_demo/) | Demo localization; không train M3Diff |
| [locateanything_robustness](../../outputs/locateanything_robustness/) | Probe localization robustness |
| [locateanything_coco](../../outputs/locateanything_coco/) | COCO pilot nhỏ; chưa suy rộng absence reliability |
| [grounded_caption_pilot](../../outputs/grounded_caption_pilot/) | Rewrite pilot24; gain không đồng đều giữa miền |
| [m3diff_caption_verifier](../../outputs/m3diff_caption_verifier/) | Caption verifier; chưa gain ổn định |
| [caption_verifier_color_v4](../../outputs/caption_verifier_color_v4/) | Color verifier; fresh24 sửa 0 caption |
| [viewpoint_diagnostic](../../outputs/viewpoint_diagnostic/) | Chẩn đoán viewpoint/alignment |
| [viewpoint_extension](../../outputs/viewpoint_extension/) | Alignment có false suppression; chỉ exact RGB guard trong pipeline chọn |

Đọc report kết quả trước protocol và raw. Các file khóa lựa chọn, assessment và prediction gốc giữ nguyên. Thư mục này là mục lục theo chủ đề; code và bằng chứng nằm tại đường dẫn được liên kết.
