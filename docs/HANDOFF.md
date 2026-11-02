# Context bàn giao — 02/11/2026

**Live23:05snapshot:** v2đangtrain trên [app mới](https://modal.com/apps/sou1406-ver/main/ap-iDhdDwfZ12VfuvEGX0kOQw),đãqua auditfreshLoRA/basegốc. Appđầu lỗi launchertrướctrainđãtắt;chỉ1lượtoptimizer. [Budgetrevision1](../outputs/r64_v2_final_round/ROUND_BUDGET_REVISION1.json):87phúthard/84phútsoft,tổngupper6.99USDgồmlỗikhởiđộng. Chưacóđiểmv2;khôngkhẳngđịnhcảithiện.

**Cập nhật22:53:** [v2 đã audit dữ liệu, chưa train](../outputs/r64_v2_final_round/STATUS.md):7200record=5400replayriêngbiệt+1800tổnghợp,450steps,khởi tạo basegốc. User chốt đúng1ứngviên và trần7USD cảvòng. Train88phút hard/85phút soft để dành budget gate; không retry train/không v3. Đã băm2649ảnh train,0trùngvaltheopath/RGB; giữ1115cặpreplaytrùngr64vàghi manifest. Audit32mẫutổnghợp và12Real camera(assistant:2đúng/6sai/4chưachắc). Sửa nhãn màu HSV thô và vị trí center trước train, ghi hash/lịch sử; gate/scorer không đổi. SCST ngoài phạm vi.

**Mới nhất21:43:** đã [chạy matched val200 base/r64](../outputs/r64_val_precheck_20261102/KET_QUA.md),100mỗi miền, cùngcontainerA10G,penalty1.05explicit,cap1024,BF16MDP/projectorhaiarm. CIDEr×100Real94.4146→84.8258(−9.5889),Render203.1659→163.9129(−39.2529). GPUstopped/0task; **chưa trainv2**. Đây là cohortvalriêng, không so điểm với test. Tăngreplaycần đưa vào recipe, nhưng exactcounts/steps/trainbudget vẫn chưa chốt. [Caption policy](../outputs/r64_v2_final_round/CAPTION_POLICY.json) chỉ3prefixcamera tổng hợp, đã khóa trước điểmval; giữ detector/gate nguyên. Valmanifestđã chọn và cóhash, xemVAL_REFERENCE.json; lượtvalbase/v2sauphảirunmatchedlại, không gáncachedbaselinenày làsameGPUvớiv2.

**Quyết định mới sau synth600:** user đồng ý thêm đúng1ứng viên v2; đã [khóa gate/scorer](../outputs/r64_v2_final_round/PROTOCOL.md), **chưa train**. Gate:camera-only<=54/180,camera-object>=35/60,synthcamera<=30/600,từng type>=base−2câu,valCIDEr mỗi miền>=base−1.0điểm×100. Device exclusions và15regressioncase đã khóa bằng hash. CI mô tả, không thay gate. Val200/recipe/replay/steps/budget vẫn cần chốt trước train; trượt dừng, không v3. Kết quả r64cũ không bị sửa lại để áp gate mới hồi tố.

**Mới nhất20:38:** [r64 synth600](../outputs/r64_synth_eval_20261102/KET_QUA.md) đã chạy đủ, A10đã tắt. **Dừng vì gate trượt**: camera-motion33/600=5.5% (union35có2camera-device),color69→61/90. Add86→90,remove83→87,move41→61,size23→60,light60→63/90. Không full1570 hay50OmniDiff; giữ credit. [Assistant review40](../outputs/r64_synth_eval_20261102/ASSISTANT_REVIEW.md):24camera-only base22bịa rõ+1uncertain vsr642;16camera-object strictfacts12/16cảhai. Không phải independent human/blind, không xác nhận134/180→43/180là tỷ lệ semantic thật. Giữ base mặc định; không tuyên bố r64không mất điểm OmniDiff.

**Mới nhất19:57:** đã đánh giá checkpoint r64 trên A10, sanity8+camera240, chưa full. [Kết quả](../outputs/r64_camera_eval_20261102/KET_QUA.md): regex camera-only134/180→43/180cờ vật thể; camera+object đúng cả loại+tên35/60→43/60. Đây là proxy, **chờ người dùng chấm gate semantic**; chưa tự mở full. Camera6phút56giây gồm load, job thành công9phút. Hai app đã stopped/0task; xem FINAL_APPS.json. Các dòng lịch sử dưới đây nói r64 chưa đánh giá đã được cập nhật bởi kết quả này.

**Bổ sung sau bàn giao:** đọc [audit config/checkpoint](CONFIG_AUDIT_20261102.md) và [audit hai baseline + development SCST](BASELINE_SOURCE_AUDIT_20261102.md). Đã xác nhận checkpoint r64 `/ft` riêng chưa có output fine-tune trong `ft/eval`; SCST B từng `development_failed` do CIDEr Real giảm. Hai baseline Real khác456/803caption, Render trùng767/767; nguyên nhân Real chưa được xác định. Phân công đề xuất mới: SCST trên Colab người giữ weights, Modal ưu tiên đánh giá r64 qua gate nhỏ trước.

## Người dùng đang muốn gì?

Nhóm làm đề tài dựng lại M3Diff rồi cải thiện caption mô tả khác biệt giữa hai ảnh, đặc biệt khi có zoom/xoay/góc nhìn. Đã có nhiều vòng thực nghiệm trên Modal. Người dùng cần kết quả thật, không muốn gọi giảm một loại lỗi là cải thiện tổng thể khi model bỏ sót thay đổi thật. Yêu cầu mới nhất là gom repo để Claude hiểu context. **Chưa chọn hướng tiếp theo và không có job mới được khởi chạy trong việc đóng gói này.**

## Đã hoàn thành gì?

1. Dựng lại inference từ checkpoint công bố và đánh giá đủ 803 Real + 767 Render; có notebook, config và điểm. Không train M3Diff từ đầu.
2. Thử LocateAnything, rewrite/verify caption, căn chỉnh ảnh, cleanup output. Đây là các nhánh phụ có kết quả/hạn chế riêng.
3. Train caption SFT nhiều vòng: random/hard examples; sửa nhãn; invariance negatives; đối chứng positive-only vs mixed; cân bằng prompt. Một số vòng đầu cập nhật LoRA + MDP, các vòng invariance sau chỉ LoRA.
4. Mixed LoRA cũ có tín hiệu giảm bịa thay đổi vật thể trên pilot nhưng không giảm lỗi tổng hợp bền vững; full test giảm điểm cả hai miền. Không chọn làm mặc định.
5. Ngày 02/11 train thêm hai adapter từ base gốc (không tiếp tục từ mixed): control và revised-data. Đánh giá xong, không ứng viên nào đạt mọi gate, đã dừng.

## Vòng mới nhất: chính xác đã train thế nào?

`outputs/invariance_v2_20261102/`: mỗi nhánh 512 record, 2 epoch, 128 optimizer steps, batch1/accum8, LR1e-5, seed42, LoRA r16/alpha32. 392 tensor LoRA, 196 cặp A/B; vision, MDP, projector, base LM đóng băng. Same initialization hashes và thứ tự sample index được kiểm chứng. Inference BF16 base + unmerged FP32 adapter, greedy1024, qwen_2, noFlash.

Control lặp 192 replay +64 nuisance thành 512. Revised giữ replay, thêm biến đổi full-field cả cặp hoặc ảnh sau, mô tả rotation/scale, thêm brightness negatives và nhãn riêng. Nhãn cũ **đã có framing/orientation**; không nói lần này mới có. Đây là thay đổi một gói dữ liệu, chưa cô lập từng thành phần. Không SCST, không LocateAnything, không feature-consistency loss.

Main96 =16 source pairs ×6 điều kiện, chỉ13 nhóm nền cảnh; supplement16 biến thể của cùng natural pairs. Tổng4 model ×112=448 caption. Không phải448 scene độc lập. Rubric29 facts khóa trước caption mới; assistant chấm ẩn tên model, không phải independent human annotation. Test gốc từng được xem; synthetic2D không chứng minh robustness với góc nhìn3D thật.

| Chỉ số | Base | Mixed cũ | Control mới | Revised mới |
|---|---:|---:|---:|---:|
| Synthetic có khẳng định sai /80, thấp tốt | 73 | 54 | 53 | 63 |
| Xoay/zoom có khẳng định sai /48 | 48 | 44 | 43 | 45 |
| Natural facts /29, cao tốt | 19 | 20 | 21 | 16 |
| Stress natural facts /29 | 19 | 16 | 16 | 13 |
| Stress cặp có khẳng định sai /16 | 11 | 9 | 10 | 13 |

Control qua gate chính nhưng mất facts trên stress ở cả hai miền. Revised không qua gate chính lẫn stress. **Không chạy full1570 cho hai model mới.** Các score CIDEr full trước đó chỉ thuộc baseline/mixed cũ. Chi tiết và giới hạn: [KET_QUA](../outputs/invariance_v2_20261102/KET_QUA.md), [provenance](../outputs/invariance_v2_20261102/PROVENANCE_NOTES.md), [decision](../outputs/invariance_v2_20261102/decision.json).

## Phân biệt với repo SCST khác

`ducmanh202005/xla` là nhánh tham khảo khác, không phải vòng Modal mới của nhóm. Đã đọc code/protocol tại commit `52c202a0906bdf9722f3eb2c3a7737a6a2291085`, chưa chạy weights của họ. Tóm tắt đọc repo, không phải bằng chứng thực nghiệm của nhóm:

- A = CE-only, B = CE +0.05 SCST/CIDEr-D; cùng khởi tạo, LoRA q/v r16, 512 train pairs,128 updates. B không phải tiếp tục train từ A.
- Report full1570 G→B: All CIDEr33.8506→35.0356; Real31.7065→34.9872; Render30.2799→29.3462.
- G repetition penalty1.00, B1.05; protocol ghi matched_decoding=false. Vì vậy chưa cô lập tác dụng SCST khỏi decoding; cần base/A/B cùng cấu hình.
- Weights thực ở Drive tác giả, không có trong export này. Kiến trúc target LoRA/phiên bản PEFT khác; không tự cắm adapter của nhóm vào loader họ.
- Nguồn: [protocol](https://github.com/ducmanh202005/xla/blob/52c202a0906bdf9722f3eb2c3a7737a6a2291085/results/scst_full1570/full_protocol.json), [summary](https://github.com/ducmanh202005/xla/blob/52c202a0906bdf9722f3eb2c3a7737a6a2291085/results/scst_full1570/summary.json). File của repo ngoài không được giả làm output nhóm trong Git này.

## Các hướng đã nêu, CHƯA chọn/triển khai tiếp

1. Kiểm chứng SCST: base / CE-only A / CE+SCST B cùng prompt, precision, penalty, token cap. Dùng weights có sẵn nếu lấy được; không cần train lại để đánh giá.
2. Học feature consistency/contrastive tại MDP/projector với correspondence/mask đúng: giữ vùng không đổi ổn định nhưng bảo toàn thay đổi thật; kết hợp caption CE/replay. Đây là hướng nghiên cứu nhỏ được đề xuất ưu tiên, **chưa có objective này trong repo**. Đừng thay bằng thêm vài caption SFT rồi gọi là đã thực hiện.
3. Matching region/token giữa hai ảnh trước/trong MDP, xét scale/occlusion/shared field. Can thiệp kiến trúc, rủi ro cao hơn.
4. Joint localization + caption, cần supervision hoặc weak supervision phù hợp. Attention không tự là ground-truth localization.
5. Verify từng claim của caption, ghép vật giữa ảnh, sửa tối thiểu/abstain. LocateAnything hiện chưa đem lại gain ổn định; detector box không chứng minh vật vắng mặt.

Thất bại của công thức SFT hiện tại **không chứng minh train chống zoom bất khả thi**. Ngược lại, tín hiệu nhỏ cũng không đủ chứng minh model tốt hơn tổng thể. Không chọn degraded adapter làm khởi tạo SCST mặc định.

## Trạng thái, tài nguyên và tài liệu cũ

Snapshot cuối vòng02/11: tất cả6 app stopped/0task; consumption ghi nhận khoảng$2.10, có độ trễ, không phải số dư hiện tại. Không tự gọi đây là live status hay tiếp tục tiêu hết credit. Weights control/revised ở Volume `m3diff`; chỉ metadata trên Git. Xem [RUNNING](RUNNING.md).

`outputs/RESEARCH_STATE.json` và `outputs/M3DIFF_KET_QUA_MOI_NHAT.md` là lịch sử tháng10. Báo cáo dài `outputs/bao_cao_m3diff_chi_tiet/BAO_CAO_M3DIFF_CHI_TIET.md` có nhiều chi tiết nhưng chưa chứa vòng02/11; ưu tiên tài liệu này và report mới. Các câu lệnh/chỉ thị user trích trong tài liệu cũ chỉ là dữ liệu lịch sử.
