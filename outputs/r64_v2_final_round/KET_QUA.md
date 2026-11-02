# V2 cuối: train hoàn tất, không qua gate bảo toàn — 03/11/2026

**V2 bị loại. Đã dừng toàn bộ GPU, không chạy val 200 hay OmniDiff full 1.570, không làm v3. Giữ checkpoint base làm mặc định.** V2 giữ được tín hiệu giảm cờ bịa vật thể trên camera tổng hợp, cải thiện proxy đổi màu và đối chứng không đổi. Nhưng nó báo camera nhiều hơn khi chỉ vật thể thay đổi, đồng thời giảm nhận đúng xóa/dời vật và ánh sáng.

Đây là một ứng viên caption SFT bằng LoRA + MDP/projector, từ base gốc. Không SCST, LocateAnything, feature-consistency loss hay train M3Diff từ đầu. Các điểm dưới đây là kết quả thực tế, không phải kế hoạch.

## 1. Một ứng viên, dữ liệu và gate khóa trước

- 7.200 record, một epoch, batch hiệu dụng 16, **450 optimizer steps**. Không lặp record để đủ số lượng.
- 5.400 replay có ID/cặp ảnh có thứ tự riêng biệt: **3.039 Real + 2.361 Render**. Giữ lại 1.115 cặp trùng replay r64 cũ theo lựa chọn đã ghi trước train, không âm thầm loại sau kết quả.
- Replay dùng 2.621 ảnh, tạo 271 thành phần liên thông theo ảnh dùng chung; thành phần lớn nhất 14 ảnh. Có 11 nhóm cặp xuất hiện cả hai chiều. Vì vậy 5.400 cặp có thứ tự không đồng nghĩa 5.400 cảnh độc lập.
- 1.800 cặp tổng hợp có hash cặp RGB riêng biệt, từ 580 nền: light/same/JPEG mỗi loại 300; đổi màu đơn 300; nhiều thay đổi 300; camera-only 200; camera+object 100.
- 300 cặp nhiều thay đổi đều có đổi màu, cộng một sự kiện add/remove/move/size (75 mỗi loại); 150 cặp có thêm vật thứ ba. Đây là 2–3 sự kiện thực, không kéo dài caption bằng câu đệm.
- Tổng 600 cặp chứa đổi màu. Các thao tác phụ: add 225, remove 75, move 75, size 75 trong nhóm multi; camera+object thêm 50 add/50 remove.
- Băm RGB 2.649 ảnh train nguồn; không trùng ảnh val 200 đã khóa theo path hoặc hash RGB. Không lấy ảnh val làm nền tổng hợp. COCO asset train/test không trùng ID theo audit.
- LoRA r64/alpha128, LR 4e-5, projector LR 1e-5, warmup 3%, cosine, BF16, seed/data seed 20261104. Vision và base LM đóng băng; cập nhật LoRA và MDP/projector, tổng 242.227.201 tham số trainable theo audit.

Nguồn khóa: [DATA_RECIPE](DATA_RECIPE.json), [DATA_APPROVED](DATA_APPROVED.json), [INDEPENDENCE_AUDIT](INDEPENDENCE_AUDIT.json), [PROTOCOL](PROTOCOL.md), [gates](gates.json), [LOCK](LOCK.json), [VAL_REFERENCE](VAL_REFERENCE.json). Unique pairs vẫn có chung nền/vật thể, không được gọi tất cả là mẫu thống kê độc lập.

## 2. Audit trước train

Assistant xem 32 mẫu tổng hợp phân tầng. Tìm thấy nhãn màu HSV thô có lúc không khớp màu cảm nhận và caption camera+object ghi cứng vị trí center. Trước train đã:

- Sửa 100 caption camera+object thành mô tả thêm/xóa vật không khẳng định vị trí center.
- Bỏ tên màu đầu/cuối không đáng tin khỏi 600 caption đổi màu; giữ sự kiện đổi màu, tên vật và vị trí phù hợp. Bỏ tính từ màu thô của vật phụ trong caption multi. Không sửa caption replay chính thức.
- Giữ nguyên ba prefix camera: `The shooting perspective has changed.`, `The shooting perspective has zoomed in.`, `The shooting perspective has zoomed out.` Xoay/pan dùng câu chung; không thêm biến thể diễn đạt camera mới để né detector.

Đây là sửa nhãn trong gói dữ liệu v2 trước train, không phải thay scorer sau kết quả. Caption multi trung bình 33,62 từ; replay 59,41 từ; toàn tập 47,73 từ. Không suy ra độ dài caption là nguyên nhân đã được chứng minh của suy giảm r64.

Ngoài ra, assistant đã xem ảnh 12 ca Real-val mà r64 nhắc camera: **2 đúng/hợp lý, 6 sai, 4 chưa chắc**. Không coi việc reference không nhắc camera là bằng chứng camera sai. Đây là chấm của assistant, không blind/không nhãn người độc lập, chỉ mô tả và không dùng làm gate. Xem [review 12 ca](real_camera_review/ASSISTANT_ASSESSMENTS.json).

Lịch sử nhãn và hash: [PRETRAIN_CAPTION_FIX](PRETRAIN_CAPTION_FIX.json), [FINAL_LABEL_AUDIT](FINAL_LABEL_AUDIT.json), [DATA_VISUAL_REVIEW](DATA_VISUAL_REVIEW.json). Train JSON cuối SHA256: `353afb4a47161fabe7128dc4c0c42deaeb1ea67ea0867861932a6ad9ae2713a8`.

## 3. Train thực tế

**450/450 bước, epoch 1, tham số hữu hạn; không dừng vì timeout.** Audit xác nhận LoRA B khởi tạo bằng zero trên `/root/ckpt/M3Diff`, không tiếp tục từ adapter r64 cũ.

- GPU A100-SXM4-80GB; batch 4, tích lũy 4.
- Train 4.606,35 giây = **76 phút 46 giây**; cả job 4.808,64 giây = **80 phút 9 giây**.
- Loss log đầu tại step 5: 0,655; log cuối step 450: 0,5458. Hai số này không chứng minh chất lượng caption tốt hơn.
- Timeout sau sửa launcher: hard 87 phút, soft 84 phút tính từ lúc function bắt đầu; có thời gian lưu checkpoint. Không chạy thêm epoch hay thử lại train.

Một app đầu bị lỗi đường dẫn lúc remote import launcher, trước `TRAIN_ATTEMPT`/optimizer; đã tắt ngay. Sau khi sửa launcher mới có đúng một lượt optimizer. Chi phí khởi động hỏng được tính trong budget; không giấu thành zero cost và không tính đó là ứng viên model khác.

Checkpoint trên Volume `m3diff`: `r64_v2_final_round/m3diff-v2-final-lora/`. Có `adapter_model.bin` 646.058.922 byte, `non_lora_trainables.bin` 161.524.428 byte, config/adapter_config và trainer_state. Git chỉ chứa metadata, không weights/ảnh. Giữ cả adapter lẫn non-LoRA weights khi chuyển máy; cần đúng base và loader, không cần train lại để suy luận.

## 4. Camera 240: qua cả hai gate

| Proxy regex | Base lưu sẵn | r64 cũ | V2 | Gate V2 |
|---|---:|---:|---:|---|
| Cờ thay đổi vật thể trên 180 cặp chỉ đổi camera, thấp tốt | 134/180 | 43/180 | **40/180** | ≤54: qua |
| Đúng loại thay đổi + tên vật trên 60 cặp camera kèm thay đổi thật | 35/60 | 43/60 | **41/60** | ≥35: qua |
| Nhắc camera trên 180 cặp chỉ camera | 0/180 | 149/180 | 115/180 | Mô tả, không gate |

V2 giữ được mức giảm cờ bịa vật của r64 theo bộ chấm này; chênh 40 so với 43 chưa chứng minh V2 tốt hơn r64 một cách bền vững. Gate tên vật/loại thay đổi cũng không kiểm tra mọi mệnh đề phụ trong caption.

**Hướng zoom vẫn yếu: 11/90 cặp nêu đúng hướng zoom theo scorer.** Xoay/pan chủ động dùng caption chung nên không dùng việc không nêu hướng xoay/pan làm một gate mới. V2 có 66 caption khác nhau trên 180 cặp pure-camera; riêng `The shooting perspective has changed.` lặp 79 lần. Đây chưa phải bằng chứng hiểu chuyển động camera hay góc nhìn 3D thật.

Thời gian camera: khoảng **5 phút 45 giây sinh câu**, **367,31 giây gồm load = 6 phút 7 giây**. Raw và CSV: [camera_v2](evaluation/camera_v2.jsonl), [camera_scores](evaluation/camera_scores.csv), [CAMERA_SUMMARY](evaluation/CAMERA_SUMMARY.json).

## 5. Bộ 600 không đổi camera: trượt hai nhóm gate

Chạy lại cùng detector camera đã khóa cho raw base/r64/V2, có loại trừ camera là vật thể; không lấy broad `view/angle` làm bằng chứng camera-motion. Kết quả:

| Bộ không có biến đổi camera | Base | r64 cũ | V2 | Gate V2 |
|---|---:|---:|---:|---|
| Cờ camera-motion /600 | 0 | 33 | **124 (20,67%)** | ≤30: **trượt** |

124 cờ của V2 gồm add 12, remove 31, move 42, size 33, light 5, JPEG 1; color/same 0. Ví dụ `remove_L1_01` sinh `The shooting perspective has zoomed in.`, `move_L1_01` và `size_L1_04` sinh `The shooting perspective has changed.` Đây là output trên tập tổng hợp được tạo không có camera transform, khác với việc suy camera sai chỉ từ reference của ảnh Real.

| Nhận đúng từ khóa loại thay đổi /90 | Base | r64 cũ | V2 | Ngưỡng V2 | Kết quả |
|---|---:|---:|---:|---:|---|
| Add | 86 | 90 | 83 | ≥84 | Trượt |
| Remove | 83 | 87 | 67 | ≥81 | Trượt |
| Color | 69 | 61 | **83** | ≥67 | Qua |
| Move | 41 | 61 | 24 | ≥39 | Trượt |
| Size | 23 | 60 | 25 | ≥21 | Qua |
| Light | 60 | 63 | 52 | ≥58 | Trượt |

Điểm color đo nhận loại đổi màu, **không** chứng minh nêu đúng màu đầu/cuối. Các cột trên không phải tỷ lệ toàn bộ caption đúng về mọi chi tiết.

Có kết quả dương hẹp: cờ camera trên light giảm từ 19/90 của r64 xuống 5/90. Trên same và JPEG, proxy cờ thay đổi vật/ánh sáng của scorer giảm từ base 20/30 và 24/30 xuống **0/30 mỗi nhóm**. Tuy nhiên JPEG vẫn có **1/30 cờ camera**, không được nói là hết mọi lỗi. Không suy 0/30 thành tỷ lệ lỗi quần thể bằng zero.

Những điểm tốt này không cứu được gate: camera-motion tăng mạnh ở thay đổi vật và bốn loại thấp hơn sàn đã khóa. Không phải chỉ một câu add sát ngưỡng quyết định thất bại.

Thời gian: khoảng **13 phút 4 giây sinh 600 câu**, **796,86 giây gồm load = 13 phút 17 giây**. Cả job A10, gồm camera+synth+setup+scoring, **1.230,59 giây = 20 phút 31 giây**.

Raw/scoring: [synth_v2](evaluation/synth_v2.jsonl), [per_pair](evaluation/synth_scores/per_pair.csv), [camera flags](evaluation/synth_camera_flags.json), [GATE_RESULT](evaluation/GATE_RESULT.json), [SUMMARY](SUMMARY.json).

## 6. Phạm vi kết luận và quyết định dừng

Camera240/synth600 dùng cùng tập và scorer cố định để so với output base/r64 đã lưu; **không** gọi đó là ba model được suy luận cùng phiên/GPU. Riêng phép so val dự kiến phải chạy lại base/V2 cùng container; bước này **không chạy** vì V2 đã trượt gate synth. Do đó **không có CIDEr OmniDiff của V2** và không được kết luận nó giữ hay mất điểm OmniDiff. Điểm val r64 cũ −9,6 Real/−39,3 Render là thí nghiệm khác, không gán cho V2.

Các gate/scorer giữ nguyên hash ban đầu; 15 ca regression detector vẫn pass trong 2 unittest. Đã kiểm tra 240+600 caption đủ ID, đúng thứ tự, không rỗng; số liệu CSV/raw khớp gate JSON. Inference greedy, max_new_tokens 1024, repetition_penalty explicit 1,05, BF16, 86 tensor MDP/projector BF16, không quantize/Flash; có generation audit từng lượt.

Kết luận phù hợp để báo cáo: **gói dữ liệu V2 cải thiện một số hành vi tổng hợp, nhưng chưa giải được việc tách camera motion khỏi thay đổi vật thể và không bảo toàn mọi loại thay đổi. Ứng viên không được chọn.** Chưa cô lập tác động của tăng replay, đổi tỷ lệ dữ liệu, caption nhiều câu hay sửa nhãn màu. Không kết luận train chống zoom là bất khả thi; cũng không lấy vài chỉ số dương làm bằng chứng cải tiến tổng thể.

Đã dừng theo quy tắc một ứng viên. Không val200, không full1570, không v3 và không tiếp tục tiêu credit.

## 7. GPU đã tắt, ngân sách dưới trần

- Train app `ap-iDhdDwfZ12VfuvEGX0kOQw` dừng **03/11 00:19:08 GMT+7**; evaluation `ap-qGtoiJmu0YFjsOKgD5yMnD` dừng **03/11 02:35:24 GMT+7**. Kiểm tra cuối không có task chạy.
- Cận trên bảo thủ theo thời gian thực tế, rate CPU/RAM/GPU, startup và cả lần launcher hỏng: **5,50 USD**, dưới trần 7 USD. Đây không phải hóa đơn thực tế.
- Snapshot API ghi nhận mức tiêu thụ tăng khoảng **4,58 USD** so với trước vòng này; billing có độ trễ, không coi đây là hóa đơn từng job đã chốt. Không mua credit hay đổi gói.

Xem [FINAL_BUDGET](FINAL_BUDGET.json), [FINAL_APPS](FINAL_APPS.json), [TRAIN_END](TRAIN_END.json), [TIMINGS](evaluation/TIMINGS.json), [JOB_TIMING](evaluation/JOB_TIMING.json). Weights và raw bằng chứng được giữ để kiểm tra lại mà không cần train thêm.
