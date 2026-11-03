# MBR full1.570 đã hoàn tất: tăng Render, chưa tăng Real

Pipeline cuối `COMPLETE_SCORED` lúc **22:23:27 ngày03/11/2026, GMT+7**. Đủ803Real+767Render. Hai app continuation đã stopped,0task; container list rỗng. Không train hoặc đổi weights, không tự thay model mặc định.

## Kết quả đối chứng chính

Tất cả điểm bên dưới nhân100. Greedy và8sample của mỗi cặp sinh trong cùng một phiên; MBR chọn bằng train-IDF consensus đã khóa. Đây là full benchmark ghép từ3phiên, không gọi là cả1.570cặp sinh trong một container.

| Miền | Số cặp | Greedy CIDEr | MBR CIDEr | Chênh lệch | CI95% chênh lệch |
|---|---:|---:|---:|---:|---|
| Real | 803 | 34,5844 | 34,3619 | **−0,2225** | [−3,5640; +3,3177] |
| Render | 767 | 30,1822 | 33,7996 | **+3,6174** | **[+1,0924; +5,9766]** |

[METRICS.json](resume1020_v1/combined_full1570/METRICS.json), [CI riêng](resume1020_v1/combined_full1570/CONFIDENCE_INTERVALS.json), [PER_PAIR](resume1020_v1/combined_full1570/PER_PAIR.json), [SELECTION](resume1020_v1/combined_full1570/SELECTION.json).

CI là bootstrap theo nhóm ảnh liên thông,5.000lượt, seed20261109,20nhómReal/10nhómRender; giữ DF reference từng miền cố định. Không phải tính lại DF cho từng mẫu bootstrap. Đã tính lại từ PER_PAIR trên máy và khớp toàn bộ CI. Không coi803/767cặp là803/767cảnh độc lập.

**Cách diễn giải:** MBR có cải thiện CIDEr trên Render trong full test; CI mô tả đã khóa nằm phía dương. Real không có mức tăng điểm; CI chứa0 nên chưa có bằng chứng rõ về hướng chênh lệch. CI chứa0 không chứng minh tương đương/giữ điểm. Không kết luận cải thiện trên cả hai miền từ kết quả này.

## Các metric khác và độ dài

| Miền | BLEU-4 greedy→MBR | METEOR greedy→MBR | ROUGE-L greedy→MBR |
|---|---|---|---|
| Real | 14,8773→15,2496 | 19,6127→19,5711 | 32,7916→32,9527 |
| Render | 17,0432→19,7894 | 20,3143→20,8150 | 35,6814→36,1474 |

Render tăng ở cả các metric phụ này, nhưng đây là metric dựa trên caption reference, không phải nhãn factual của người. Chưa có human review mới trên full test. Không khẳng định giảm bịa vật thể, nhận đúng hướng camera hoặc nhìn ảnh tốt hơn.

Real có587/803cặp đổi caption, trung bình55,50→49,97từ, trung vị47→44. Render có522/767cặp đổi caption, trung bình62,28→50,10từ, trung vị47→47. Câu ngắn hơn về trung bình chưa đủ để kết luận bớt bỏ sót hoặc metric chỉ được tăng nhờ độ dài.

## Ba phiên và phần resume

| Phiên GPU | Đóng góp vào full | CIDEr delta trên phần tương ứng |
|---|---|---|
| Lượt đầu bị preempt | 550Real | +1,6230 |
| Continuationphase1 | 253Real+565Render=818 | Real−4,2343; Render+3,2817 |
| Continuationphase2 | 202Render cuối | +4,5563 |

[SESSION_ASSIGNMENTS](resume1020_v1/combined_full1570/SESSION_ASSIGNMENTS.json) và [SESSION_ANALYSIS](resume1020_v1/combined_full1570/SESSION_ANALYSIS.json) ghi đủ provenance. Các delta subset dùng cùng DF của full miền, không phải benchmark riêng. Các phiên chứa ID/cảnh khác nhau, nên không quy khác biệt giữa subset thành tác động thuần của GPU/container.

Lượt đầu dừng550cặp giữ nguyên; full raw bắt đầu bằng đúng550dòng/bytes cũ (SHA256 `9c2d55ad4d4cf6cb556255340c2cf2f7894d838d4eec7cf4f7d21089e4aa47fe`). Quyết định resume5845554 và nâng trầnfc83091 được commit trước khi chấm full. Chỉ cặp thiếu được sinh tiếp, không chọn lại ứng viên theo reference test.

Phase1 dừng theo mốc ngân sách21:49, nên `resume1020_v1/PIPELINE_DONE.json` ghi `STOP_ERROR_OR_GLOBAL_BUDGET`; đó là trạng thái phase1, không phải trạng thái cuối toàn benchmark. App phase1 stopped21:50:08, owner-SDK xác nhận0container lúc21:50:19; GPUphase2 mới bắt đầu21:54:05, không song song GPU cũ. Phase2 hoàn thành inference khoảng22:20 và chấm xong22:23. App phase2 stopped22:23:29.

Trạng thái cuối đúng là [FINAL_OUTCOME](resume1020_v1/FINAL_OUTCOME.json) và [PIPELINE_PHASE2_DONE](resume1020_v1/PIPELINE_PHASE2_DONE.json): `COMPLETE_SCORED`. Không ghi đè file lỗi/trạng thái phase1 hoặc lượt550cũ để che lịch sử.

## Audit và chi phí

[VERIFICATION](resume1020_v1/combined_full1570/VERIFICATION.json) kiểm tra1.570ID riêng biệt, đúng thứ tự câu hỏi gốc, đủ9ứng viên mỗi cặp, seed từngID, caption được chọn khớp raw/utility, meansCIDEr khớp PER_PAIR, CI tính lại khớp,550bytescũ nguyên vẹn. Raw full SHA256 `a5d67ee85de1f607fcd82faadefb80d5faeeb69578ddedfb659c76dc8fe33fb6`.

[Billing theo app](resume1020_v1/FINAL_BILLING_REPORT.json) ghi nhận **10,74902604USD** cho toàn lượt tiếp tục (gồm hai phase và các CPUpreflight), dưới trần13,5USD. Tính cả lượt550đầu4,70657624USD thì full generation+scoring có mức app usage ghi nhận khoảng**15,45560228USD**, không gồm pilot20/val200. Report sau16UTC bao phủ đầy đủ giờ kết thúc của các app; nhà cung cấp vẫn có thể đối soát lại. Đây không phải lấy reservation13,48USD làm số tiền thực tế.

Snapshot workspace cuối ghi creditused26,09USD,billed_cost0, tương ứng còn khoảng3,91USD trên hạn mức30USD. Hiệu số workspace continuation khoảng10,78USD hơi khác app report; có độ trễ/đối soát và rounding, không gọi app sum là hóa đơn cuối.

## Kết luận để báo cáo

Có thể viết: **“Consensus MBR decoding cải thiện caption benchmark Render: CIDEr30,18→33,80 (+3,62); trên Real34,58→34,36 (−0,22), chưa thấy cải thiện.”** Đây là cải tiến ở bước giải mã/chọn caption, không phải model đã được train lại hoặc đã khắc phục zoom/xoay. Pilot val200 từng tăng ở cả hai miền nhưng mức tăng đó không được tái hiện đầy đủ trên test.

Giữ base greedy là mặc định theo hướng dẫn repo. MBR là tùy chọn đã có kết quả Render dương và chi phí suy luận cao hơn; chưa tự xây pipeline chọn decoder theo miền sau khi xem test. Benchmark từng được dùng trong các vòng trước, không gọi đây là blind test hoàn toàn chưa từng xem.
