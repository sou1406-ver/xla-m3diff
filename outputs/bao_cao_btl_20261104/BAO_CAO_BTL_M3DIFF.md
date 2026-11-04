# Tái lập và đánh giá cải tiến M3Diff cho mô tả khác biệt ảnh

BÁO CÁO BÀI TẬP LỚN MÔN XỬ LÝ ẢNH • Cập nhật ngày 04 tháng 11 năm 2026

### Tóm tắt

Bài tập khảo sát mô tả khác biệt giữa hai ảnh khi thay đổi khung hình, zoom hoặc xoay có thể bị nhầm thành thay đổi vật thể. Nhóm tái lập suy luận từ checkpoint M3Diff công bố và đánh giá đủ 1.570 cặp OmniDiff test. Sau đó, nhóm khảo sát căn chỉnh ảnh, xử lý caption, định vị vật thể, fine-tune bằng dữ liệu tổng hợp và chọn caption bằng consensus MBR. Các thí nghiệm được phân biệt theo tập đánh giá, cấu hình giải mã và mức độ kiểm chứng. [R1–R10]

Kết quả dương rõ nhất là ở bước giải mã: trên full test Render, MBR tăng CIDEr từ 30,18 lên 33,80; chênh lệch +3,62 có khoảng bootstrap mô tả 95% [1,09; 5,98]. Trên Real, điểm thay đổi 34,58 xuống 34,36, chưa cho thấy lợi ích. Fine-tune r64 và V2 giảm cờ bịa vật thể trên camera tổng hợp nhưng trượt những kiểm tra bảo toàn khác. Lượt MBR camera chỉ hoàn tất 174/240 cặp; cờ vật thể giảm nhẹ 127 xuống 121, chưa kiểm tra được 60 cặp camera kèm thay đổi thật. [R6–R10]

### Vấn đề nghiên cứu

Ảnh sau có thể chỉ là một bản crop hoặc zoom của ảnh trước. Vật ở mép ảnh biến mất khỏi khung hình không đủ chứng minh vật đã bị xóa khỏi cảnh; kích thước biểu kiến tăng cũng không đủ chứng minh vật tự lớn lên. Ngược lại, trả câu “góc chụp đã thay đổi” cho mọi cặp sẽ bỏ sót vật thực sự được thêm, xóa hoặc di chuyển. Do đó mục tiêu phải đồng thời giảm báo sai và giữ khả năng mô tả thay đổi thật.

### Phạm vi đóng góp của nhóm

Nhóm xây dựng quy trình tái lập suy luận có ghi cấu hình và nguồn dữ liệu; xây các đối chứng camera-only và camera+object; lưu các kết quả âm cùng quy tắc dừng; và kiểm chứng một phương pháp chọn caption trên toàn bộ test. Báo cáo không nhận là đã huấn luyện M3Diff từ đầu hoặc đã giải quyết ổn định góc nhìn 3D. Những nhánh thất bại được giữ để xác định giới hạn của phương pháp, thay vì chỉ chọn vài ví dụ thuận lợi.

Mạch lập luận: tái lập baseline → nhận diện lỗi camera và vật thể → thử giải pháp → kiểm tra đánh đổi → kết luận theo từng miền và từng loại bằng chứng. Tám ca minh họa cuối báo cáo giúp đối chiếu nhận xét với ảnh và caption gốc.

## 1 Mô hình nền và phạm vi tái lập

Theo tài liệu chính thức, M3Diff mở rộng LLaVA OneVision 7B bằng mô đun Multi-scale Differential Perception, gọi tắt là MDP. MDP kết hợp tín hiệu khác biệt ở nhiều tầng đặc trưng thị giác trước khi mô hình ngôn ngữ sinh mô tả. Trong bài tập này, nhóm sử dụng checkpoint đã được tác giả huấn luyện; phần tái lập là cài môi trường, tải đúng tài nguyên, chạy suy luận và chấm điểm. [R1, R2]

### Dữ liệu và đơn vị đánh giá

| Tập OmniDiff | Real | Render | Tổng |
| --- | --- | --- | --- |
| Train | 7.007 | 5.445 | 12.452 |
| Validation | 799 | 777 | 1.576 |
| Test | 803 | 767 | 1.570 |

Các số trên là cặp ảnh, không phải số cảnh độc lập. Nhiều cặp dùng chung ảnh hoặc nền. Riêng bộ val 200 lấy 100 cặp mỗi miền và được khóa theo manifest; bộ camera 240 gồm 180 cặp chỉ đổi camera và 60 cặp vừa đổi camera vừa thêm hoặc xóa vật. Bộ tổng hợp 600 không áp camera transform, gồm sáu loại thay đổi, mỗi loại 90 cặp, cùng 30 cặp giống hệt và 30 cặp JPEG. [R5–R8]

### Thiết lập tái lập

| Thành phần | Thiết lập đã lưu |
| --- | --- |
| Code | Yuan-Liu-01/M3Diff, commit 4e346e5 |
| Checkpoint | IVC-liuyuan/M3Diff, revision d6a8880 |
| Dataset | IVC-liuyuan/OmniDiff, revision ed4a84c |
| Suy luận | BF16, greedy, beam 1, tối đa 1.024 token |
| Giải mã | repetition_penalty 1,05; không quantize; không FlashAttention |
| Môi trường MBR | PyTorch 2.2.2, Transformers 4.40.0, PEFT 0.4.0 |
| Tài nguyên tái lập | A10; ảnh và weights nằm trên Volume m3diff |

generation_config.json của checkpoint có repetition_penalty 1,05. Lượt dùng penalty 1,00 phải được ghi là biến thể giải mã, không tự gọi là baseline chuẩn. Hash câu hỏi, reference, revision và cấu hình được lưu để kiểm tra lại. MDP/projector để FP32 trong một số protocol cũ cũng cần phân biệt với các lượt BF16 toàn bộ. [R2, R3]

Tái lập hoàn tất ở mức chạy lại suy luận và đánh giá checkpoint công bố. Nhóm không tái tạo quy trình tiền huấn luyện hay toàn bộ instruction tuning gốc; vì vậy không tuyên bố tái lập từ đầu mọi chi tiết của công trình.

## 2 Đánh giá công bằng và cách đọc số liệu

BLEU, METEOR, ROUGE L và CIDEr được dùng để đo mức tương đồng giữa caption sinh và reference. Trong các bảng định lượng, điểm được nhân 100. Không chạy SPICE. Metric caption không tự chứng minh một câu đúng về mọi vật thể, cũng không đo trực tiếp khả năng hiểu hình học. Cờ regex và nhận xét nhìn ảnh vì vậy được trình bày riêng. [R2, R6–R10]

### Baseline tái lập và baseline của phép so MBR

| Lượt và miền | N | BLEU 4 | METEOR | ROUGE L | CIDEr |
| --- | --- | --- | --- | --- | --- |
| Tái lập Real | 803 | 14.27 | 19.49 | 32.61 | 33.75 |
| Tái lập Render | 767 | 16.92 | 20.14 | 35.75 | 30.49 |
| MBR full greedy Real | 803 | 14,88 | 19,61 | 32,79 | 34,58 |
| MBR full greedy Render | 767 | 17,04 | 20,31 | 35,68 | 30,18 |

Không trộn hai baseline trên để tính gain. Khi đánh giá MBR, greedy của chính từng cặp được sinh cùng phiên với tám mẫu sampling. Lượt baseline lịch sử Real CIDEr 35,54 và lượt tái lập 33,75 khác 456/803 caption, còn Render gần như khớp. Nguyên nhân chưa được cô lập; sai số số học hoặc khác môi trường là giả thuyết, không phải kết luận. Không có căn cứ đặt một ngưỡng “nhiễu cố định 2 CIDEr”. [R3, R9]

### Ba mức bằng chứng cần tách riêng

| Bằng chứng | Dùng để kết luận | Giới hạn |
| --- | --- | --- |
| Metric caption | Chất lượng theo reference trên đúng cohort | Không bảo đảm factual accuracy hay hình học |
| Regex và gate | Quyết định thực dụng theo định nghĩa đã khóa | Có bắt nhầm, bỏ sót và lỗi phủ định |
| Xem ảnh và caption | Giải thích những ca cụ thể | Assistant review không phải nhãn người độc lập |

CIDEr phụ thuộc corpus reference và document frequency. Vì vậy điểm val 100 cặp mỗi miền có thể lớn hơn 100 và không được so trực tiếp với điểm test 803 hoặc 767 cặp. Cũng không cộng các pilot khác mẫu, prompt và rubric thành một phép đo chung.

Các gate V2 được khóa trước kết quả: camera-only tối đa 54/180 cờ vật thể; camera+object tối thiểu 35/60 đúng loại và tên; synth tối đa 30/600 cờ camera; mỗi loại không thấp hơn base quá hai câu; val CIDEr từng miền không giảm quá 1,0. Đây là dung sai thực dụng, không phải kiểm định non-inferiority. Nếu trượt, dừng thay vì đổi gate. [R7]

## 3 Các hướng xử lý ảnh và caption đã khảo sát

Nhóm đã thử nhiều can thiệp ngoài huấn luyện. Mỗi nhánh có câu hỏi riêng: căn chỉnh có tránh nhầm đổi khung hình hay không; detector có xác minh được vật trong câu hay không; xử lý câu có giảm lặp mà giữ nội dung hay không. Kết quả ở pilot không được dùng để mặc nhiên thay model nền. [R4, R11, R12]

| Hướng | Quan sát chính | Quyết định |
| --- | --- | --- |
| Căn chỉnh SIFT và RANSAC | Diagnostic cũ: cờ lỗi validation camera 14/18 xuống 5/18 | Chưa đủ để bật tự động |
| Stress căn chỉnh mở rộng | 20/56 appearance stress bị trả nhầm không đổi | Chỉ giữ làm gợi ý |
| LocateAnything và verifier | Định vị một số vật; chưa có gain ổn định trên caption | Không chọn làm giải pháp chính |
| Grounded rewrite pilot 24 | CIDEr Real 11,43→19,06; Render 16,42→7,47 | Không suy thành gain hai miền |
| Lọc lặp và giới hạn độ dài | Có thể đổi metric và độ dài câu | Không gọi là cải thiện thị giác |

### Căn chỉnh đã thực hiện như thế nào

Pipeline cũ dùng SIFT, ghép đặc trưng và cv2.estimateAffinePartial2D với RANSAC để ước lượng biến đổi toàn ảnh. Đây là affine một phần, không phải đã triển khai homography tổng quát. Bộ chặn xem số inlier, tỉ lệ inlier, độ bao phủ, overlap và residual sau căn chỉnh; chỉ khi đạt ngưỡng đã khóa mới thay caption bằng mô tả không đổi vật trong vùng chung. [R4]

Trong diagnostic cũ, validation nhận 12/18 cặp chỉ xoay hoặc zoom, giảm cờ bịa vật 14/18 xuống 5/18; stress ban đầu chưa có lỗi. Kiểm tra CPU trên tám scene khác sau đó phát hiện 20/56 stress appearance bị bỏ qua, bao gồm cả cặp vừa biến đổi hình học vừa sửa vùng nhỏ. Như vậy kết quả diagnostic ban đầu vẫn đúng trên mẫu đó, nhưng chưa đủ chứng minh an toàn ngoài mẫu. [R4]

Quyết định cuối là chỉ tự trả không đổi khi ảnh giống hệt sau giải mã. Với ảnh không giống hệt, căn chỉnh gần đúng chỉ đưa lời khuyên kiểm tra, giữ caption model. Hai hình cuối phụ lục minh họa cả cơ chế có ích lẫn phản ví dụ. Đánh giá này dùng lại pipeline và kết quả CPU đã có; báo cáo hiện tại không mở một đợt thử ngưỡng mới.

LocateAnything định vị vật được truy vấn nhưng riêng một box không chứng minh vật đã biến mất khỏi cảnh. Các probe định vị và rewrite chưa chứng minh tăng chất lượng tổng thể; không coi chúng là quá trình train M3Diff hoặc bằng chứng đã giải được che khuất.

## 4 Các vòng fine tune và kết quả r64

Các vòng SFT tức fine-tune có giám sát gồm lấy mẫu random hoặc hard, sửa nhãn, invariance, cân bằng prompt và đối chứng control/mixed. Chúng không đồng nhất về tham số trainable: một số cập nhật LoRA cùng MDP/projector, các vòng invariance sau chỉ LoRA. Mixed full test làm CIDEr Real 33,75 xuống 32,13 và Render 30,49 xuống 20,00; không chọn model này làm mặc định. Hai nhánh r16 ngày 02/11 cũng không qua toàn bộ gate bảo toàn. [R11]

### Ứng viên r64

R64 dùng LoRA r64, alpha 128, learning rate 4e-5, một epoch, 338 optimizer steps, khoảng 59 phút. Tập thực tế có 5.420 record, khoảng một nửa camera hoặc thay đổi tổng hợp và một nửa replay OmniDiff train. Đây là fine-tune từ base công bố, không phải train từ đầu. R64 riêng này khác các adapter r16; không áp kết quả loại r16 sang r64. [R5, R6]

| Camera tổng hợp và kiểm tra giữ kiến thức | Base | r64 |
| --- | --- | --- |
| Cờ vật thể trên camera-only /180 | 134 | 43 |
| Đúng loại+tên trên camera+object /60 | 35 | 43 |
| Nhắc camera trên camera-only /180 | 0 | 149 |
| Cờ camera-motion trên synth /600 | 0 | 33 |
| Nhận loại đổi màu /90 | 69 | 61 |
| CIDEr val Real 100 cặp | 94,41 | 84,83 |
| CIDEr val Render 100 cặp | 203,17 | 163,91 |

Camera và synth so với base lưu sẵn; chỉ val 200 chạy matched cùng phiên. Camera giảm cờ mạnh và proxy camera+object tăng. Nhưng synth r64 vượt 5% cờ camera-motion, đồng thời giảm đổi màu. Số cờ union ban đầu là 35/600; hai câu thực ra dùng camera như tên thiết bị, nên báo riêng 33/600 cờ motion mà không sửa lại kết quả gate. Điều này cho thấy cần phân biệt detector rộng với camera-motion thực sự. [R6]

Precheck val 200 chạy lại base và r64 cùng container A10G, cùng câu hỏi, BF16 và decoding. CIDEr giảm 9,59 ở Real và 39,25 ở Render. Đây là bằng chứng suy giảm trên cohort đó, không chứng minh cơ chế quên kiến thức; caption ngắn hơn và chuyển thói quen nói camera chỉ là các giả thuyết cần đối chứng. Không chạy full test cho r64 rồi nhận nó là model cải thiện tổng thể. [R6]

Xem ảnh bổ sung 40 ca do assistant chấm cho thấy regex có cả bỏ sót và bắt nhầm. Vì vậy 134→43 là giảm cờ theo scorer, không tự đổi thành tỉ lệ hallucination ngữ nghĩa đã được người gán nhãn xác thực.

## 5 V2 giữ tín hiệu camera nhưng trượt bảo toàn

Theo quy tắc một ứng viên cuối, V2 khởi tạo lại từ base. Dữ liệu gồm 5.400 replay riêng biệt có thứ tự, chia 3.039 Real và 2.361 Render, cùng 1.800 cặp tổng hợp. Tăng mẫu light/same/JPEG, tăng đổi màu, thêm caption nhiều thay đổi; xoay và pan dùng câu camera chung, zoom giữ in/out. Giữ 1.115 cặp replay trùng r64 và ghi rõ trong manifest. Đây là gói thay đổi dữ liệu, chưa cô lập tác động từng thành phần. [R7]

Huấn luyện LoRA r64/alpha128 và MDP/projector, đóng băng vision và base LM, đủ 450/450 optimizer steps trong 76 phút 46 giây trên A100 80GB. Không train tiếp từ r64. Loss giảm và tham số hữu hạn chỉ xác nhận train chạy, không phải bằng chứng chất lượng tăng. [R7]

| Gate camera 240 | Base | r64 | V2 | Ngưỡng V2 |
| --- | --- | --- | --- | --- |
| Cờ vật thể /180 | 134 | 43 | 40 | ≤54 đạt |
| Đúng loại+tên /60 | 35 | 43 | 41 | ≥35 đạt |

| Synth không camera | Base | r64 | V2 | Sàn V2 |
| --- | --- | --- | --- | --- |
| Cờ camera /600 | 0 | 33 | 124 | ≤30 trượt |
| Add đúng loại /90 | 86 | 90 | 83 | 84 trượt |
| Remove /90 | 83 | 87 | 67 | 81 trượt |
| Color /90 | 69 | 61 | 83 | 67 đạt |
| Move /90 | 41 | 61 | 24 | 39 trượt |
| Size /90 | 23 | 60 | 25 | 21 đạt |
| Light /90 | 60 | 63 | 52 | 58 trượt |

V2 giảm cờ camera ở nhóm light từ 19/90 của r64 xuống 5/90, nhưng cờ lại tập trung ở remove, move và size. Trong 180 cặp camera-only, câu “The shooting perspective has changed.” xuất hiện 79 lần. Hành vi này phù hợp giả thuyết học một câu trả lời quá rộng cho thay đổi vị trí; chưa đủ chứng minh đó là cơ chế nội tại duy nhất. [R7]

V2 bị loại vì trượt synth. Không chạy val 200 hay full 1.570 cho V2, do đó không có CIDEr OmniDiff của V2 để kết luận giữ hoặc mất điểm. Không làm V3. Hình đổi màu trong phụ lục chỉ minh họa một sự kiện được mô tả đúng; nó không bù cho các loại bị suy giảm.

## 6 Consensus MBR cải thiện bước chọn caption

MBR viết tắt Minimum Bayes Risk, ở đây không cập nhật trọng số. Với mỗi cặp ảnh, base sinh một caption greedy và tám caption sampling, cố định temperature 0,7, top_p 0,8, top_k 20, repetition_penalty 1,05, beam 1 và tối đa 1.024 token. Embedding thị giác/MDP được tính một lần cho mỗi cặp; sampling dùng batch 2 bốn lần. Không có chia sẻ prefix KV cache giữa các lần generate. [R8, R9]

Bộ chọn PTB-tokenize chín caption rồi lấy caption có CIDEr-D trung bình cao nhất khi so với tám caption còn lại. Loại tự so với chính mình; giữ các caption trùng; hòa điểm ưu tiên greedy rồi chỉ số nhỏ. IDF lấy từ reference train, không dùng reference test để chọn. Đây là consensus MBR xấp xỉ; pool có greedy và các mẫu trùng nên không gọi là ước lượng rủi ro hậu nghiệm không chệch. Seed cố định theo ID. [R8, R9]

### Pilot và full test phải đọc riêng

| Cohort và miền | Greedy | MBR | Chênh CIDEr |
| --- | --- | --- | --- |
| Val Real 100 | 85,62 | 106,53 | +20,91 |
| Val Render 100 | 201,47 | 206,70 | +5,23 |
| Test Real 803 | 34,58 | 34,36 | −0,22 |
| Test Render 767 | 30,18 | 33,80 | +3,62 |

Val qua gate tăng ít nhất 1,0 ở từng miền, nhưng khoảng bootstrap Render val rất rộng. Full test xác nhận gain Render, không tái hiện gain Real. Không dùng mức điểm tuyệt đối val và test để suy model chạy tốt hay xấu đi vì chúng khác corpus DF. [R8, R9]

| Full test | Chênh CIDEr | CI mô tả 95% | Nhóm ảnh |
| --- | --- | --- | --- |
| Real | −0,22 | [−3,56; +3,32] | 20 |
| Render | +3,62 | [+1,09; +5,98] | 10 |

CI lấy 5.000 bootstrap theo thành phần liên thông ảnh, giữ DF reference full-domain cố định; seed 20261109. Đây là CI có điều kiện, không tính lại DF trong từng mẫu bootstrap. Real có CI chứa 0 không chứng minh tương đương hay bảo toàn. Test gồm ba phiên GPU: 550 Real; 253 Real +565 Render; 202 Render. Greedy và sampling của mỗi cặp cùng phiên, nhưng toàn benchmark không cùng một GPU/container duy nhất. 550 raw cũ được giữ nguyên byte. [R9]

Review 40 cặp val thay câu, che tên model, cho MBR tốt hơn 13, greedy tốt hơn 7, tương đương 15, chưa chắc 5. Người chấm là assistant, không phải nhãn người độc lập; Render review đã biết metric tổng hợp. Gain metric Render chưa đủ cho kết luận giảm mọi lỗi factual hoặc hiểu camera tốt hơn. Sinh chín ứng viên làm tăng chi phí và độ trễ suy luận.

## 7 MBR camera chỉ có bằng chứng một phần

Lượt camera giữ base gốc, greedy mới và tám mẫu sampling cùng phiên A10, seed/selector/config như full. Trần 2 USD và không GPU retry. Lượt này dừng ở 174/240 cặp trước timeout. Log provider ghi cancellation khoảng 00:23–00:25 ngày 04/11; chưa xác định được nguồn lệnh hủy. Không ghi đó là preemption hoặc hết giờ khi chưa có bằng chứng. Chấm CPU sau khi xác nhận app gốc không còn container. [R10]

| Camera-only matched | Greedy mới | MBR |
| --- | --- | --- |
| Cờ vật thể /174 | 127 (73,0%) | 121 (69,5%) |
| Nhắc camera /174 | 0 | 0 |
| Đúng hướng theo detector /174 | 0 | 0 |
| Số từ trung bình | 50,64 | 42,20 |
| Trung vị từ | 42 | 38 |

Có 15 cặp hết cờ và 9 cặp phát sinh cờ: giảm ròng 6, tương đương 3,45 điểm phần trăm. McNemar mô tả khoảng p=0,31, chưa xử lý phụ thuộc ảnh; không dùng để tuyên bố cải thiện có ý nghĩa. Caption ngắn hơn khoảng 16,7%, nhưng chưa cô lập việc này có gây giảm cờ hay không. [R10]

| Loại camera | Đủ cặp | Thiếu |
| --- | --- | --- |
| Zoom in | 45/45 | 0 |
| Zoom out | 45/45 | 0 |
| Rotate | 45/45 | 0 |
| Pan | 39/45 | 6 |
| Camera + add | 0/30 | 30 |
| Camera + remove | 0/30 | 30 |

Thiếu toàn bộ 60 cặp có thay đổi vật thể thật, nên khả năng giữ đúng loại và tên vật là chưa đo được, không phải 0% và cũng không phải đã qua gate. Các cặp lưu là prefix có thứ tự, không phải mẫu ngẫu nhiên. Chỉ báo matched 174 cặp, không ngoại suy thành kết quả đầy đủ camera 240. Base lịch sử 134/180 không phải đối chứng chính của lượt này.

Trong 1.566 caption ứng viên, detector camera cũ bắt được hai câu thuộc hai cặp; cả hai không được chọn. Điều này gợi ý pool ít câu camera để bộ chọn khai thác, nhưng detector có thể bỏ sót diễn đạt khác. Nó không chứng minh nguyên nhân nằm riêng tại vision, MDP hoặc decoder. Bộ 600 cho MBR không chạy. [R10]

## 8 Tổng hợp đóng góp và giới hạn

| Câu hỏi | Bằng chứng hiện có | Kết luận cho báo cáo |
| --- | --- | --- |
| Chạy lại M3Diff được chưa | Đủ 1.570 test, có revision, cấu hình và raw | Hoàn tất tái lập suy luận |
| Căn chỉnh có luôn an toàn | Diagnostic tốt nhưng bỏ qua 20/56 stress | Không tự thay caption bằng gần đúng |
| Camera SFT có tốt hơn tổng thể | r64 và V2 giảm cờ camera nhưng trượt gate khác | Không chọn adapter làm mặc định |
| MBR tăng điểm benchmark | Render +3,62; Real −0,22 trên matched full | Gain giải mã ở Render |
| MBR giải được zoom/xoay chưa | Partial 174 giảm 6 cờ; thiếu camera+object | Chưa đủ bằng chứng |

### Những cách giải thích còn là giả thuyết

Dữ liệu camera tổng hợp có thể khiến model học lối tắt, chẳng hạn xem mọi thay đổi vị trí là camera hoặc dùng câu trả lời chung. Replay nhiều hơn có thể giảm quên kiến thức nhưng V2 thay đồng thời nhiều yếu tố. Caption ngắn có thể giảm cơ hội phát biểu sai nhưng cũng có thể bỏ sót thay đổi. Các hiện tượng này phù hợp kết quả quan sát, chưa được cô lập bằng ablation riêng từng yếu tố.

### Giới hạn thực nghiệm

Camera train/test dùng cùng bộ sinh 2D; nhiều ảnh có nền hoặc vật lặp, cutout và nhãn không hoàn hảo. Bộ test gốc đã được dùng trong các vòng trước, không phải holdout mù hoàn toàn. Regex chưa có đánh giá precision/recall đủ lớn bằng nhãn người; assistant review không thay thế người gán nhãn độc lập. Cấu hình hoặc môi trường thay đổi giữa các lượt có thể làm caption greedy khác; so matched từng cặp được ưu tiên, không tự quy mọi chênh lệch cho phương pháp.

### Kết luận và hướng tiếp theo

Nhóm đã xây được một quy trình từ tái lập, phân tích lỗi, thử giải pháp đến kiểm tra đánh đổi. Đóng góp dương rõ nhất là consensus MBR tăng CIDEr Render trên full test; đóng góp phân tích là chỉ ra giảm cờ camera không bảo đảm bảo toàn thay đổi thật. Bài toán phân biệt camera motion với object change vẫn chưa được giải quyết ổn định trong phạm vi thí nghiệm này.

Giữ base greedy làm mặc định và công bố cả kết quả âm. Ưu tiên hoàn thiện nhãn người, hình minh họa và tài liệu tái lập. Nếu sau này nghiên cứu tiếp căn chỉnh, nên đánh giá độ tin cậy, vùng chồng lấp và bảo toàn vùng thay đổi trước khi ghép lại với model. Feature consistency loss hoặc sửa kiến trúc vẫn là đề xuất chưa thực hiện, không được liệt kê thành đóng góp đã làm. Nhánh SCST của repo bên ngoài cũng không phải kết quả huấn luyện được kiểm chứng trong báo cáo này.

## 9 Nguồn bằng chứng và cách kiểm tra lại

Mã R trong nội dung trỏ tới các tài liệu dưới đây. Số liệu của nhóm lấy từ raw, CSV và JSON đã lưu; không lấy điểm công bố của tác giả làm kết quả tự chạy. Repo nhóm: https://github.com/sou1406-ver/xla-m3diff. Các nguồn kết quả mới đã có trước bản tổng hợp này tại commit 4fca43c.

[R1] M3Diff và OmniDiff của tác giả. Nguồn: https://github.com/Yuan-Liu-01/M3Diff. Kiến trúc nền và tài nguyên công bố; truy cập 04/11/2026.

[R2] Baseline tái lập. Nguồn: baseline_results/REPORT.md. run_config.json; summary_x100.csv; raw nguồn trong Volume.

[R3] Audit cấu hình và baseline. Nguồn: ../docs/BASELINE_SOURCE_AUDIT_20261102.md. CONFIG_AUDIT_20261102.md; khác biệt các lượt baseline.

[R4] Căn chỉnh và phản ví dụ. Nguồn: viewpoint_extension/KET_QUA.md. viewpoint_diagnostic/KET_QUA.md; registration_gate.py; case_results.csv.

[R5] Đánh giá r64 camera 240. Nguồn: r64_camera_eval_20261102/KET_QUA.md. camtest_compare.csv; raw base/r64; manifest240.

[R6] r64 synth và val. Nguồn: r64_val_precheck_20261102/KET_QUA.md. r64_synth_eval_20261102/KET_QUA.md; metrics và raw riêng từng cohort.

[R7] V2 cuối và protocol đã khóa. Nguồn: r64_v2_final_round/KET_QUA.md. PROTOCOL.md; gates.json; DATA_RECIPE.json; evaluation/GATE_RESULT.json.

[R8] MBR val200. Nguồn: mbr_pilot_20261103/KET_QUA_VAL200.md. utility.py; trainIDF hash; review 40; generation audit.

[R9] MBR full 1570. Nguồn: mbr_pilot_20261103/KET_QUA_FULL1570.md. METRICS, PER_PAIR và CONFIDENCE_INTERVALS trong combined_full1570.

[R10] MBR camera partial 174. Nguồn: mbr_pilot_20261103/camera240/KET_QUA.md. partial_diagnostic/COVERAGE.json,METRICS.json; raw174; provider.log.

[R11] Bản đồ các nhánh cũ. Nguồn: ../docs/EXPERIMENTS.md. mixed_full_benchmark; invariance_v2_20261102; LocateAnything và cleanup.

[R12] Báo cáo giai đoạn trước. Nguồn: bao_cao_m3diff_chi_tiet/BAO_CAO_M3DIFF_CHI_TIET.md. Bổ sung chi tiết nhánh trước 02/11; không dùng thay kết quả mới.

### Kiểm tra lại mà không chạy GPU

Đối chiếu METRICS với PER_PAIR và ID manifest; xem chín caption ứng viên trong raw; kiểm tra SELECTION chọn theo train-IDF; đọc SESSION_ASSIGNMENTS để thấy ba phiên của full. Với camera partial, xem coverage trước khi đọc tỷ lệ. Với V2, đọc gate trượt trước khi suy luận về chất lượng OmniDiff. Thông tin revision đầy đủ và hash nằm trong run_config, LOCK, ADMISSION và VERIFICATION tương ứng.

CASES.json ghi 8 ID, ảnh nguồn, caption nguyên văn, cách chọn và nhận xét. Đây là lựa chọn minh họa có chủ đích sau kết quả; không dùng để ước lượng tỷ lệ model thắng. Các nhận xét ảnh trong phụ lục là assistant review không blind và không thay nhãn người. Ảnh không được đưa lên Git riêng; bản Word trên máy nhúng ảnh, còn repo giữ văn bản, manifest và script để tái tạo từ cache/Volume đã có.

## Phụ lục hình 1 Giảm nhầm thay đổi vật thể trên một cặp zoom tổng hợp

ID `zoom_in_L1_08`

*Hình 1 nằm trong bản Word có ảnh tại workspace; xem CASES.json để truy nguồn. Ảnh dataset không phân phối trong Git.*

**Base lưu sẵn**: The blue box with a white border on the left side of the lower bed has been moved to the right side of the blue box. The orange rectangular pillow on the right side of the upper bed has increased in size.

**r64**: The shooting perspective has slightly zoomed in.

**V2**: The shooting perspective has changed.

Ảnh sau được tạo bằng zoom 2D; vật thể gốc không được thêm hay xóa. r64 nêu zoom in. Chỉ minh họa một ca; kết quả tổng hợp mới quyết định đánh đổi.

Cách chọn: Một ca zoom có dir_ok của r64; chọn có chủ đích để giải thích hành vi, không ước lượng tỷ lệ.

Nguồn: `r64_camera_eval_20261102/camtest_compare.csv`

## Phụ lục hình 2 V2 gọi thay đổi vị trí vật thể là thay đổi góc chụp

ID `move_L1_01`

*Hình 2 nằm trong bản Word có ảnh tại workspace; xem CASES.json để truy nguồn. Ảnh dataset không phân phối trong Git.*

**Base lưu sẵn**: The yellow glass goblet on the central table has appeared. The yellow coffee maker on the left side of the dining table has appeared. The yellow coffee maker on the black countertop at the back right of the scene has appeared. The white plate with food in the center of the round wooden table has appeared.

**r64**: The orange cup on the left side of the scene has moved to the right.

**V2**: The shooting perspective has changed.

Bộ sinh chỉ di chuyển cutout vật thể, không biến đổi camera. V2 trả câu perspective changed và bỏ qua sự kiện di chuyển mục tiêu.

Cách chọn: Ca đã có output, dùng để đối chiếu lỗi vị trí và tín hiệu đổi màu; không đại diện toàn tập.

Nguồn: `r64_v2_final_round/evaluation/synth_scores/per_pair.csv`

## Phụ lục hình 3 Một kết quả tốt hẹp không đủ để chọn V2

ID `color_L1_01`

*Hình 3 nằm trong bản Word có ảnh tại workspace; xem CASES.json để truy nguồn. Ảnh dataset không phân phối trong Git.*

**Base lưu sẵn**: The bananas in the lower left corner of the image have changed color from yellow to green.

**r64**: The yellow banana in the lower part of the scene has turned green.

**V2**: The color of the banana in the scene has changed.

Bộ sinh đổi màu vật thể, giữ camera. V2 nêu đổi màu; phải xem đồng thời các loại remove và move bị giảm trong bảng tổng hợp.

Cách chọn: Ca đã có output, dùng để đối chiếu lỗi vị trí và tín hiệu đổi màu; không đại diện toàn tập.

Nguồn: `r64_v2_final_round/evaluation/synth_scores/per_pair.csv`

## Phụ lục hình 4 MBR chọn mô tả vị trí phù hợp hơn

ID `render_val_pair_000090`

*Hình 4 nằm trong bản Word có ảnh tại workspace; xem CASES.json để truy nguồn. Ảnh dataset không phân phối trong Git.*

**Greedy cùng phiên**: A new illuminated sign displaying the word "Camp" in large blue letters has appeared on the wooden wall to the right of the bed, above a picture frame and next to a plant.

**MBR cùng phiên**: A glowing blue sign displaying the word "Camp" has appeared on the wooden wall above the bed, to the right of a framed wall decoration.

Assistant review cũ cho rằng vị trí chữ Camp bên phải khung tranh phù hợp hơn mô tả chữ ở phía trên. Phụ lục này kiểm tra lại bằng ảnh; không dùng CIDEr từng cặp để gọi caption đúng.

Cách chọn: Từ review A/B cũ: một ca MBR tốt, một ca greedy tốt, một ca cả hai yếu; chọn có chủ đích sau kết quả.

Nguồn: `mbr_pilot_20261103/val200/ASSISTANT_REVIEW_RENDER.json`

## Phụ lục hình 5 MBR thêm một chi tiết không được ảnh hỗ trợ rõ

ID `render_val_pair_000108`

*Hình 5 nằm trong bản Word có ảnh tại workspace; xem CASES.json để truy nguồn. Ảnh dataset không phân phối trong Git.*

**Greedy cùng phiên**: A new illuminated sign displaying the word "Cowp" has appeared on the wooden wall to the right of the bed, positioned above a plant and next to a framed wall decoration. The color of the ring-shaped chair on the left side of the coffee table in the room has changed from purple to dark brown.

**MBR cùng phiên**: A newly added illuminated sign displaying the word "Cowp" has appeared on the wooden wall to the right of the bed, positioned above a plant and next to a framed wall decoration. The black lampshade on the ceiling fixture located in the center of the room has disappeared. The color of the ring-shaped chair on the left side of the coffee table has changed from purple to dark brown.

Assistant review cũ đánh giá greedy tốt hơn vì MBR thêm khẳng định đèn trần biến mất trong khi đèn vẫn có thể thấy. Tên chữ trong caption có thể nhận sai; không coi mọi chi tiết còn lại đều đúng.

Cách chọn: Từ review A/B cũ: một ca MBR tốt, một ca greedy tốt, một ca cả hai yếu; chọn có chủ đích sau kết quả.

Nguồn: `mbr_pilot_20261103/val200/ASSISTANT_REVIEW_RENDER.json`

## Phụ lục hình 6 MBR vẫn giữ nhầm lẫn camera và vật thể

ID `real_val_pair_000627`

*Hình 6 nằm trong bản Word có ảnh tại workspace; xem CASES.json để truy nguồn. Ảnh dataset không phân phối trong Git.*

**Greedy cùng phiên**: The black shoes on the far right of the middle shelf have disappeared. The red men's leather shoes on the far right of the bottom shelf have disappeared. The gray shoes on the left side of the shoe rack have moved to the far right of the middle shelf.

**MBR cùng phiên**: The gray shoes on the left side of the shoe rack have moved to the right side. The black shoes on the far right of the middle shelf have changed from a horizontal arrangement to a vertical one.

Hai ảnh đổi khung hình và góc nhìn. Hai caption đều khẳng định giày đổi vị trí; ảnh có che khuất nên không suy mọi vật ngoài khung là bị xóa. Assistant review cũ đánh giá cả hai đều yếu.

Cách chọn: Từ review A/B cũ: một ca MBR tốt, một ca greedy tốt, một ca cả hai yếu; chọn có chủ đích sau kết quả.

Nguồn: `mbr_pilot_20261103/val200/ASSISTANT_REVIEW_REAL.json`

## Phụ lục hình 7 Căn chỉnh chấp nhận một cặp zoom không có sửa vật thể

ID `kitchen__zoom_1p10`

*Hình 7 nằm trong bản Word có ảnh tại workspace; xem CASES.json để truy nguồn. Ảnh dataset không phân phối trong Git.*

**M3Diff sau lọc lặp**: The ambient lighting has brightened.

**Bộ chặn v1**: Only the image framing, scale, or rotation changes; no object changes are detected in the shared visible area.

Ước lượng hình học đủ tin cậy và residual thấp khiến bộ chặn v1 thay caption. Đây là hành vi của pipeline CPU, không phải model đã học góc nhìn. Xem ca tiếp theo trước khi kết luận an toàn.

Cách chọn: Một ca validation zoom được v1 chấp nhận; chọn minh họa cơ chế.

Nguồn: `viewpoint_diagnostic/registration_decisions.json`

## Phụ lục hình 8 Căn chỉnh bỏ qua một thay đổi pixel đã biết

ID `basin_shelf__square32_delta16`

*Hình 8 nằm trong bản Word có ảnh tại workspace; xem CASES.json để truy nguồn. Ảnh dataset không phân phối trong Git.*

**Quyết định v1**: Trả không đổi dù đã có chỉnh sửa appearance 32×32.

Ảnh minh họa có trước, sau và chênh lệch pixel khuếch đại. Đây là phản ví dụ appearance tổng hợp, không phải bằng chứng một vật thể tự nhiên bị xóa. V1 có thể căn chỉnh tốt nhưng bộ chặn vẫn bỏ qua residual nhỏ.

Cách chọn: Một phản ví dụ đã có trong failure_previews, không chạy lại hoặc dò ngưỡng.

Nguồn: `viewpoint_extension/case_results.csv`
