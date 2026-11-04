**CameraMBR04/11 đã đóng partial174/240:** [Kết quả](../outputs/mbr_pilot_20261103/camera240/KET_QUA.md). Cờ vật thể127→121/174,nhắc camera0→0;thiếu6pan+toàn60cam_add/remove,khôngđo retention. Provider cancellation trướcdeadline,nguồnhủy chưa rõ,khôngGPUretry. ĐãchấmCPU/allGPUoff;~1.30USD+CPU nhỏ<trần2,creditAPI~2.62USDchưachốt. Không600/newGPU. Full1570Rendergain vẫn hợp lệ;chưaclaimcameraimprovement.

**LIVE camera240 MBR03/11 23:36GMT+7:** user ủy quyền mới base greedy+8sample matched A10, cap2USD/no retry. [Protocol](../outputs/mbr_pilot_20261103/camera240/README.md), commit68fc6b6. Appap-MUqFfsywpoTqauR577cjYH; đầu2cặp đã sinh, chưa điểm. GPUstart23:35:08, soft00:43:08/hard00:45:08 ngày04/11. Số dư API~3.91USD trước lượt. CPU tự chọn train-IDF/chấm sau GPU; localread-only watcher đang tải kết quả. Bộ600 chưa admit, chỉ sau đối soát còn>=2.5USD và uppercostfitsbuffer. Không train/retry/tune.

# Context bàn giao — cập nhật03/11/2026

**FULL ĐÃ HOÀN TẤT03/11:** [Kếtquảfull1570](../outputs/mbr_pilot_20261103/KET_QUA_FULL1570.md),COMPLETE_SCORED22:23:27GMT+7. Real34,58→34,36(−0,22),CI[−3,56;+3,32];Render30,18→33,80(+3,62),CI[+1,09;+5,98]. Đủ803/767,3phiên550+818+202,550rawbytescũgiữnguyên,CIđãtínhlạikhớp. Allapps stopped/0container. Continuationcost10,749USD<trần13,5;fullcảlượt550đầu15,4556USDkhônggồmpilot. CanonicalMETRICSởresume1020_v1/combined_full1570;FINAL_OUTCOME/PIPELINE_PHASE2_DONElàtrạngtháicuối. PIPELINE_DONEgốclàphase1dừngmốc,khôngphảifullthấtbạilầncuối. Giữbasegreedydefault,chỉkhẳngđịnhgainRender;khôngclaimgiảmhallucination/zoomrotation. CácLIVE/đangchạybêndướilàlịchsử.

**LIVE13.5USD:** phase1vẫnap-2LLzTT9FpCW7OGxuFpawMc;phase2CPUactiveap-VkUSKIKKsWLaYfYCDhFNbgchờnaturalend+ownerSDKreceiptoldapp0containers,xem[releasegate](../outputs/mbr_pilot_20261103/resume1020_v1/PHASE2_RELEASE_GATE.md). Localwatchersession6645;giữhost/appđếnchuyểnphiên.Native20:30đãcậpnhậtchốt13.5/healthwatcher. Quyếtđịnhfc83091trướcscore,finalgate719efce;GPUfinal23:04:57. NhữngappUN5/6MIpreflightđãdừng,khôngGPUphase2.

**Userduyệt13,5USDtổng:** [phase2plan](../outputs/mbr_pilot_20261103/resume1020_v1/PHASE2_PLAN.md),committrướcchấm;giữphase1đếnmốccũ21:49,phase2chỉsauoldapp0containers;khôngcancelphiênđangchạy. Uppercộngdồn13,48USD,finalGPUcutoff23:04:57GMT+7,khôngreset.Mọi550raw/config/seed/selectorđềugiữnguyên. Scheduled20:30đãcậpnhật13,5thay11. Cácnotes11USD/noresumephíadướilàlịchsử.

**Theo dõi20:30:** [monitor plan](../outputs/mbr_pilot_20261103/resume1020_v1/MONITOR_PLAN.md),heartbeatmộtlầnđãtạo. Userchophépnớideadlinecóđiềukiệntrướcchấm nếuETAkhôngkịp vàtổngcontinuation<=11USD;cầncommitrevisiontrướcápdụng. Hiệnchưanới,currentdeadline21:49:57. ChỉsửaSTATEkhôngđổitimerlive;cầnhandoffcheckpointcókiểmsoátnếucần.18:58log67cặpmới,chưaRenderthựctế.

**LIVE resume03/11:** [app tiếp1020cặp](https://modal.com/apps/sou1406-ver/main/ap-2LLzTT9FpCW7OGxuFpawMc)đangchạy,A10080GB;đãquaReal551. [Protocol/README](../outputs/mbr_pilot_20261103/resume1020_v1/README.md). Usercap11USD,upper10,95. Quyếtđịnh5845554vàrunner07049dd trướcchấm550. Old550giữnguyên;resumeatomic/mốcchung21:49:57GMT+7khôngreset. Chỉchấmđủ1570 vàkhai báo nhiều phiên. Khôngtrain/tune. Các trạngthái noresume/GPUoff phía dưới là lịch sử bị userủyquyềnmới thay thế.

**Quyếtđịnh mới user03/11:** [tiếp1020cặp,trần11USD](../outputs/mbr_pilot_20261103/resume1020_v1/README.md),cho phép resume theo protocol khóa trước,chưa chấm550cặp. Đây là ủy quyền mới thay no-resume cũ,chưa launch lúccommit. Giữ550rawbytes;253Real+767Rendercòn lại,cùngseed/config/selector;khai báo nhiều phiên,khôngclaimonesession. Upper10,95USD,mốcGPUchung11220s khôngreset,CPUchấm khiđủ1570.

**FULL đã đóng03/11:** [STOP_ERROR_NO_RETRY](../outputs/mbr_pilot_20261103/full1570/CLOSED_REPORT.md):550/1570 cặp đã lưu,550Real/0Render. Provider log xác nhận preemption;Modal restart bị attempt guard chặn,không resume. Không METRICS/PER_PAIR/SELECTION/CI full;không gọi partial là benchmark. App stopped09:04:17GMT+7,0app/container. Billing report riêng app4,70657624USD dưới trần18;workspace creditused15,31. Không chạy lại theo user. Pilot val200 vẫn dương nhưng chưa xác nhận full/Render. Các snapshot đang chạy phía dưới là lịch sử.

**LIVE full03/11:** user đã duyệt trần18USD; [full1570 đang chạy](../outputs/mbr_pilot_20261103/LIVE_FULL.md) trên [Modal app](https://modal.com/apps/sou1406-ver/main/ap-6kENLEhpd83ypqw6H1aAC8). Khóa trước prediction commitc303d9b; upper reservation17,70USD. Fresh greedy+8sample803Real/767Render,A10080GB. Các cặp đầu thành công; chưa có điểm full. CPU coordinator tự chấm sau inference, trả GPU trước chấm;hard timeout/khôngretry. Các trạng thái chưaadmit/GPUoff phía dưới là lịch sử pilot.

**Trạng thái mới nhất 03/11:** [MBR val200 đã hoàn tất và qua gate](../outputs/mbr_pilot_20261103/KET_QUA_VAL200.md): Real85,62→106,53(+20,91), Render201,47→206,70(+5,23). CI Render còn rộng; review40 là assistant, không phải nhãn người độc lập. Audit A100 dừng đúng soft limit18/20, canonical parity18/18. GPU đã tắt,0 app/container. **Full1570 chỉ mới chuẩn bị, chưa admit/chưa launch**: dự kiến~14USD,trần đề xuất18USD; user đang cân nhắc lợi/hại vì chi phí cao hơn dự đoán cũ. Không train/loss đặc trưng/v3. Các snapshot đang chạy phía dưới là lịch sử.

**MBR val200 đang chạy:** [pilot20 đủ và báo cáo](../outputs/mbr_pilot_20261103/KET_QUA_20.md);batch2rẻhơn1.417×,nhưngMBR20deltaReal−12.14/Render−41.42,oraclecao;khôngđổi sangpooltuầntựtốtđiểmsaukhiđọcref. [Val200app](https://modal.com/apps/sou1406-ver/main/ap-rH53YdWBmdC2pW9wD1QsTQ),mộtconfig,cap3.60USD;chưađiểmval,fullchưaadmit. Cácsnapshotpilot20đangchạybêndướilàlịchsử.

**MBR mới03/11:** user đồng ý decoding-only,khôngfeature-loss. [Pilot20](../outputs/mbr_pilot_20261103/STATUS.md)đangchạytừbase,8sampling+1greedy,sosequentialvàbatch;trần<1USD. Batch8/4đầuOOM,batch2chạyđược;chưaCIDEr/Oracle. Giữv2đãđóng. Sau20mớibudget-admitval200mộtconfig;fullchỉsaugate/qualreview/budget.

**Kết quả cuối03/11:** [V2 bị loại và đã dừng GPU](../outputs/r64_v2_final_round/KET_QUA.md). Train đủ450/450từbasegốc;camera240qua(40/180cờvật,41/60joint). Synth600trượt:124/600cờcamera;typeadd83/remove67/color83/move24/size25/light52 trên90mỗiloại. Khôngval200/full1570/v3,khôngchọnV2làmmặcđịnh. Toànvòngupper5.50USDdướitrần7;APIobserveddelta~4.58USDcóđộtrễ. A100dừng00:19:08,A10dừng02:35:24GMT+7;0task. Gate/scorernguyênhash;840rawcaptionvàCSVđãgiữ. Các snapshot “đang chạy” bên dưới là lịch sử, không phải trạng thái hiện tại.

**Mới nhất03/11 02:15:** v2[trainxong450/450](../outputs/r64_v2_final_round/STATUS.md),tham sốfinite,76m46strain/80m9sjob,A100đãtắt00:19. ĐangchạyA10camera240[app](https://modal.com/apps/sou1406-ver/main/ap-qGtoiJmu0YFjsOKgD5yMnD);trượtgateđầuthìdừng,khôngv3. Toànvòngupper6.62USDkểcảworstcaseeval,còntrần7USD. Chưacóđiểmv2/khôngtuyênbốcảithiện.

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
