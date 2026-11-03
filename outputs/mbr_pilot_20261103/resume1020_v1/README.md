# Hoàn tất benchmark bằng continuation1020cặp

**LIVE:** [app đang chạy](https://modal.com/apps/sou1406-ver/main/ap-2LLzTT9FpCW7OGxuFpawMc),snapshot2026-11-03T11:46:32.284027+00:00:12/1020cặp mớiđãlưu,tớireal_test_pair_000562. Quyếtđịnh5845554,bảnrunnercuối07049dd trước mọi điểmfull. DeadlineGPUchung21:49:57GMT+7ngày03/11. Các dòng chưa launch phía dưới là snapshot lúc commit quyếtđịnh.


User đã chọn chạy tiếp với trần11USD,cho phép resume sau interruption theo quy tắc khóa trước. Quyết định này thay chính sách khôngresume của lượt đã dừng;giữ nguyên toàn bộ file và kết quả cũ.

550cặp cũ chưa có điểm CIDEr;không chọn hyperparameter/selector dựa trên chúng. Giữ nguyên550dòng/bytes cóSHA9c2d55ad4d4cf6cb556255340c2cf2f7894d838d4eec7cf4f7d21089e4aa47fe. Chỉ sinhIDreal_test_pair_000551trở đi và toàn bộRender:253Real+767Render=1020.

Sampling,seed theoID,trainIDFselector và scorer giữ nguyên. Greedy+8samples của từng cặp phải sinh cùng một session;toànbenchmark cóít nhất2session. Không cam kết cùngseed sẽ ra caption giống tuyệt đối quaGPUkhác. GhiUUIDphiên trong mỗi cặp mới và SESSION_ASSIGNMENTS cho toàn1570.

Mỗi cặp mới được lưuatomic;commitVolume khoảng5giây. Sau preemption giữprefixđãpersist đầy đủ;chỉ làm lại cặp chưa được lưu,không chọn câu theo điểm. Cho phép tối đa3GPUworksession,1containerGPUcùnglúc. MốcdừngGPUchung11220giây từCPUcontroller,lưu trênVolume,không resetkhi restart. Watchdog vàcontrollercancel bảo vệ mốc chung. Reservation10,95USD gồmGPU10,75,CPUscore0,09,controller0,08,misc0,03;trần11USD.

Chỉ khi đủ550+1020mới ghép vào`resume1020_v1/combined_full1570/`vàchấm. Không ghi đèfolder`full1570/`cũ. CPU tự chạy fullscorer,CItheonhómảnhgiữDFcốđịnh vàsummarysession/domain. Khôngoracle test,khôngtune,khôngtựpromotemodel.

`RESUME_PROTOCOL.json`và`ADMISSION.json`làlockbeforeprediction/scoring. `STATE.json`ghi deadline/callIDbềnvững;`PIPELINE_DONE.json`làtrạngtháicuối. Nếu hếtngânsách/sốsessionthìdừng,khônggọi partial làbenchmark.

Trạngthái lúccommitquyếtđịnh:đãadmit,**chưalaunch,chưachấm550cặp**. Liveapp sẽ ghi trongDISPATCH.json saukhikhởichạy.
