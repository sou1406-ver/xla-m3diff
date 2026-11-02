# Precheck OmniDiff val200: base so với r64 — 02/11/2026

**Đã đánh giá xong200val cho mỗi model, cùng một container/GPUA10G. R64 giảm CIDEr ở cả Real và Render. Đã tắt app; chưa train v2, chưa chạy fulltest.**

| CIDEr×100, chấm riêng miền | Base | r64 | r64−base |
|---|---:|---:|---:|
| Real100 |94.4146|84.8258|**−9.5889**|
| Render100 |203.1659|163.9129|**−39.2529**|

Không lấy các điểm này so với test33.75/35.54hoặc pilot khác: đây là cohort100mỗi miền khác, CIDEr dùng corpus/DF khác. CIDEr có thể lớn hơn100. Đây là giảm điểm quan sát được trên cohort đã khóa, không tự tuyên bố mức có ý nghĩa thống kê hay chứng minh cơ chế quên kiến thức. Mức giảm vượt tham chiếu thực dụng−1.0ở cả hai miền, nên precheck bật cờ **cần tăng replay OmniDiff khi đề xuất recipev2**. Không cứu r64 bằng tín hiệu camera240để gọi là model tốt hơn tổng thể.

## Selection và khả năng so sánh

- Officialdataset revision`ed4a84cc51912c73e3d54c8643256d9469657552`,annotation15598cặp:train12452,val1576,test1570. Chọn100/799Realvalvà100/777Renderval bằng seed20261103, round-robin qua20và11connectedimagecomponents;259fileảnh. Manifest/hash khóa trước sinh caption và đã push trước khi có điểm tại commit70da267.
- Không dùng test1570. Trainmix r64 thực tế5420records (10840image references),không chứa valtheopath hay259ảnh chọn. Filename disjoint với train/testtrong officialannotation; không tuyên bố RGBdisjointtoàntrain/test hoặc sceneđộc lập. IMAGE_MANIFESTghi SHAfilevàdecodedRGBcủa259ảnh; chưa hash toàntrain/test. Không thấy valIDs trong localartifacts đã tìm, không bảo đảm tài khoản/máy khác chưa dùng.
- Cùng200IDs/thứ tự/prompt/reference/code, cùngphysicalGPUA10G23028MiB trong cùngcontainer. Không dùng lại captioncache. Prompt cố định lấy từ câu hỏi chính thức đầu tiên; không phải protocol10prompt của fulltest trước.
- Base và r64:BF16,greedy,noFlash,max1024,penalty1.05tường minh. Audit loadedgenerationconfigvàoverridescủa hai bản,86tensorMDP/projectorđềuBF16. Loader r64mergeLoRA như notebook cũ. Model.evaláp dụng cả hai. KhôngSCST,khôngquantization,khôngLoRAFP32unmerged.
- Tokenizer/scorerPTB+pycocoevalcapCIDEr; chấm riêng100cặp mỗi miền, lưu400per-pairscore. Mỗi reference mộtcaption; không tạo điểmAll bằng trung bình hai miền.

## Thời gian và dừng tài nguyên

- Base200:12phút42giây vòng sinh;827.99giây=13phút47.99giây gồm nạp model.
- R64200:10phút06giây vòng sinh;632.83giây=10phút32.83giây gồm nạp model.
- Toànjob1543.17giây=25phút43.17giây, gồm setup/suy luận/chấm/lưu. Ảnhvalđược tải local/uploadSDKtrước khi mởGPU.
- App`ap-74eeLU5H00J5JQmOlIepmg`stopped21:43:52GMT+7,0task. FINAL_APPS.jsonxác nhận; không có jobtrainv2/fulltest.
- Trần precheckđã kiểm tra trước:timeout3000giây,rateupper1.70USD/h,reservation1.51USD. Đây là dự phòng bảo thủ, không phải số tiền đã dùng thực tế. Không mua thêmcredit.

## Điều đã khóa thêm cho dữ liệu v2

`../r64_v2_final_round/CAPTION_POLICY.json`:caption camera bổ sung chỉ có3câu:perspectivechanged,zoomedin,zoomedout. Roll/pandùng câu chung,zoomin/outgiữhướng. Cả3được detectorđã khóa bắt; không sửa scorer. Giữ danh sách prefix/camera-transform/object-caption/hashpolicy trong manifest trainv2.

Policy áp dụng cho caption tổng hợp mới. Replaynhãn tác giả không bị tự sửa để ép vào template; phải audit/ghi riêng những diễn đạt camera ngoài danh sách trong replay. Model vẫn có thể tự sinh paraphrase mà detectorkhông bắt, nên hạn chếtemplate không chứng minh detectorrecallcao. Giữ rawcaptionvàchấmbổsung; không thêm exception sau v2.

## Việc còn lại trước một lượt train cuối

Chưa chốt exactrecipe/replaycounts/steps và trần train. Precheckủng hộ tăng replay từ mức cũ2700/5420≈49.8%; không chứng minh chỉ tăng replay là đủ khôi phục CIDEr. Tăng sốrecordcũng tăngsteps/thời gian nếu giữ1epoch, nên không mặc định vẫn train1giờ hoặc tổng5–6đô. Cần chốt manifest và budgettừ sốrecordthực trước GPUtrain. V2phải từbasegốc, đúng1ứng viên, đánh giá theo gateđã khóa; trượt thì dừng,khôngv3.

Artifact:SELECTION_LOCK.json,TRAIN_OVERLAP_AUDIT.json,IMAGE_MANIFEST.json,questions.json,selected_rows.json,hai reference,hai rawJSONL,generationaudits,runtime.json,metrics.json,per_pair_cider.json,timings.json,VALIDATED.json,FINAL_APPS.json. Annotationgốc/ảnh không đưa lênGit; tải lại từ revisionpinned. Schemaquestionsđược sửa sangconversationsTRƯỚCinference,giữ nguyênID/ảnh/prompt; locktrước sửa được giữ đểaudit.
