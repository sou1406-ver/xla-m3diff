# V2 cuối đã dừng — 03/11/2026

**Không chọn V2. Train xong450/450; qua camera240, trượt synth600. GPU đã tắt; không val200/full1570/v3. Giữ base làm mặc định.**

Đọc [báo cáo kết quả](KET_QUA.md) và [SUMMARY.json](SUMMARY.json). Camera:40/180cờ vật thể(ngưỡng54),41/60joint(ngưỡng35). Synth:124/600cờcamera(ngưỡng30); type add83/remove67/color83/move24/size25/light52 trên90mỗiloại. Add/remove/move/light trượt sàn. Các con số là proxyregex,không phải chấmngườimọimệnhđề.

Điểm dương hẹp:color69→83soBase;camera trênlight19→5so r64;đối chứng same/JPEG cờ vật/ánh sáng0/30mỗi nhóm,nhưngJPEGcòn1cờcamera. Không suy thành cải tiến tổng thể.

Train76m46s,job80m9s trênA10080GB. Camera6m7s/Synth13m17sgồmload;jobA1020m31s. Adaptervànon-LoRAweights giữ trênVolume m3diff:r64_v2_final_round/m3diff-v2-final-lora;Gitchỉmetadata. Không cần train lại để đọc/chạy weights đó;modelkhông được khuyến nghị làm mặc định.

Toànvòngupper5.50USDdướitrần7,kểcảCPU/RAMvàlỗilaunchertrướctrain. APIghi nhậnconsumptiondelta~4.58USDcóđộtrễ,không phảihóađơntừngjob. Xem FINAL_BUDGET.json. FINAL_APPS.json/STOP_PROOF.json xácnhậnđãdừng.

Một ứng viên từbasegốc,khôngSCST/LocateAnything. Gate/scorernguyênhashkhóabanđầu;khôngchỉnhgatehaythêmv3saukếtquả. Prerequisites Volume trong báo cáo;cloneGitkhôngchứamodel/ảnh/môitrường.
