# Matched val200 precheck trước v2

Không train. Base M3Diff và checkpoint r64 hiện có chạy nối tiếp trong cùng container/GPUA10-family trên200val đã khóa (100Real,100Render). Một prompt chính thức cố định, qwen_2,greedy,BF16,noFlash,max1024,repetition_penalty1.05tường minh,loader mergeLoRA như notebook r64. Log config nạp và overrides, dtype MDP/projector, runner hash. Không trộn cache cũ. Không dùng test.

Selection seed20261103; phân bố round-robin qua connected image components (20Real,11Render),259ảnh độc nhất. Officialval1576cặp. Trainmix r64 thực tế5420records không chứa đường dẫnval/selectedval. Không tuyên bố decodedRGB/scene độc lập toàn train; chưa làm hash toàn ảnh train/test. Đã ghi decodedRGB của259ảnh được chọn. Localartifactsearch không thấyvalIDs trước lựa chọn, không bảo đảm tài khoản/máy khác chưa từng xem.

Chấm CIDEr×100 riêng từng miền bằng pycocoevalcap/PTB cùng reference và scorer cho hai model; lưu per-pair để kiểm tra. Không so với CIDEr test33.75/35.54hoặc developmentSCST; cohort vàDFkhác nhau. Đây là development precheck cho thiết kế v2, không validation độc lập cuối cùng.

Diễn giải vận hành trước điểm: nếu r64−base<−1.0điểm ở bất kỳ miền nào, đánh dấu cần tăng replay OmniDiff trong đề xuất recipev2; nếu không, vẫn chưa chứng minh không mất thông tin hoặc tương đương thống kê. Ngưỡng là tham chiếu thực dụng theo dung sai v2 đã thống nhất, không kiểm định nhiễu. Chốt con số replay/steps/budget trainv2 sau precheck và trước một lượt train duy nhất.

Ngân sách precheck:rateupper1.70USD/h,timeout3000giây+180startupreserve=1.51USD; billedcost hiện0, không mua credit. DừngGPUkhi xong. Không tự chạy fulltest hoặc train trong job này.

Schema correction trước inference: bản đầu questions dùng trườngtext; đã sửa sangconversations để khớp evaluator chính thức, giữ nguyên200IDs/ảnh/prompt/reference/seed. Bản locktrước sửa ởSELECTION_LOCK_SCHEMA_INITIAL.json; hashselected_rows.json không đổi. Không chọn lại mẫu theo caption hoặc metric.
