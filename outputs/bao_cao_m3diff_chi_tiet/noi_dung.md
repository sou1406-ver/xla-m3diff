# Báo cáo tái lập M3Diff và các hướng cải thiện đã thực nghiệm

Ngày lập báo cáo 28 tháng 10 năm 2026

## 1 Tóm tắt kết quả và phạm vi kết luận

Mục tiêu công việc là dựng lại quy trình chạy M3Diff trên bộ dữ liệu OmniDiff, xác định điểm yếu khi hai ảnh khác góc chụp hoặc mức phóng đại, sau đó thử các hướng cải thiện chất lượng mô tả khác biệt. Các hướng đã được triển khai gồm định vị vật bằng LocateAnything, viết lại và kiểm chứng caption, continued supervised fine tuning, bổ sung cặp không thay đổi vật, thay đổi prompt, căn chỉnh ảnh, xử lý câu lặp và kiểm soát độ dài sinh.

Kết quả tái lập đã hoàn tất trên 1.570 cặp test chính thức, gồm 803 Real và 767 Render. Đã có notebook, cấu hình, caption, bộ chấm và hồ sơ phiên bản để chạy lại từ checkpoint công bố. Phần này là tái lập suy luận và đánh giá, không phải huấn luyện lại toàn bộ M3Diff từ backbone ban đầu.

Chưa thu được checkpoint fine tune tốt hơn model gốc trên toàn bộ mục tiêu. Bản mixed objective giảm lỗi bịa thay đổi vật trong các phép thử xoay và zoom có kiểm soát, nhưng không giảm tổng lỗi ở bộ xác nhận khi tính thêm ánh sáng và giải thích hình học. Trên full test, CIDEr sau cùng bộ lọc giảm từ 33,754 xuống 32,138 ở Real và từ 30,647 xuống 19,963 ở Render. Vì vậy, không chọn checkpoint này thay bản gốc.

Cải thiện được giữ lại là xử lý câu lặp nguyên văn sau sinh. Trên đúng 1.570 caption baseline, chỉ 15 caption bị thay đổi; BLEU 4 tăng ở cả hai miền, còn CIDEr tăng rất ít. Đây là cải thiện pipeline đầu ra, chưa phải bằng chứng model hiểu hình ảnh hay góc chụp tốt hơn.

LocateAnything chạy được và có thể cung cấp vùng chứa vật cho bước kiểm chứng caption. Tuy nhiên, định vị một vật không đồng nghĩa đã xác định đúng vật tương ứng giữa hai ảnh, cũng không chứng minh vật xuất hiện hay biến mất. Pipeline viết lại toàn caption có kết quả trái chiều giữa hai miền; bộ kiểm chứng thận trọng hơn có độ bao phủ sửa lỗi quá thấp trên tập kiểm tra mới.

Các kết quả nhỏ trong báo cáo là bằng chứng thăm dò hoặc phát triển, không được diễn đạt thành tăng chất lượng tổng quát. Những đánh giá đọc ảnh và chấm fact do trợ lý thực hiện, có lưu nhãn trước khi mở khóa tên nhánh ở các lượt phù hợp; chưa có người chấm độc lập xác nhận. Nguồn chính cho kết luận tổng thể là [H01], [H15], [H16] và [H20].

## 2 Bài toán và cấu trúc M3Diff

### 2.1 Bài toán mô tả khác biệt giữa hai ảnh

Đầu vào là một cặp ảnh trước và sau cùng câu hỏi về khác biệt. Đầu ra là đoạn văn mô tả các thay đổi được ảnh hỗ trợ. Một caption tốt cần phát hiện thay đổi, gọi đúng vật, xác định đúng thuộc tính hoặc hành động, và tránh thêm chi tiết không có bằng chứng. Chỉ viết câu trôi chảy hoặc nhắc đúng danh từ chưa đáp ứng yêu cầu.

Vấn đề người dùng quan tâm là model có thể coi ảnh xoay, crop, zoom hoặc đổi góc nhìn là vật đã di chuyển, đổi tư thế, xuất hiện hay biến mất. Cần phân biệt biến đổi hình ảnh với thay đổi nội dung cảnh. Biến đổi xoay 2D trong thử nghiệm cũng cần phân biệt với camera thực sự đổi góc nhìn 3D, vì trường hợp sau có phối cảnh, parallax và che khuất phức tạp hơn.

### 2.2 Các thành phần liên quan đến cải thiện

Theo tài liệu chính thức, M3Diff mở rộng LLaVA OneVision 7B bằng mô đun Multi scale Differential Perception, viết tắt MDP. MDP đưa thông tin sai khác từ nhiều mức đặc trưng thị giác vào mô hình ngôn ngữ. Báo cáo sử dụng mô tả kiến trúc này làm nền; các kết quả đánh giá là số đo của lần triển khai, không tự động coi là khớp mọi kết quả trong paper. [T01] [T02]

| Thành phần | Vai trò | Những gì đã can thiệp |
|---|---|---|
| Bộ mã hóa ảnh | Biểu diễn nội dung thị giác | Chủ yếu đóng băng trong các nhánh SFT đã chạy |
| Projector | Chuyển đặc trưng sang không gian phù hợp với LLM | Đóng băng trong các công thức nêu trong báo cáo |
| MDP | Biểu diễn khác biệt giữa hai ảnh | Có nhánh SFT cho học MDP và nhánh đối chứng đóng băng MDP |
| Mô hình ngôn ngữ | Sinh mô tả từ ảnh và câu hỏi | Fine tune bằng LoRA trong nhiều nhánh |
| Prompt và giải mã | Điều khiển nội dung yêu cầu và quá trình sinh | Đã thử prompt xét camera và giới hạn token |
| Kiểm chứng sau sinh | Kiểm tra hoặc sửa caption nháp | Đã thử LocateAnything, hình học và quy tắc màu |
| Hậu xử lý văn bản | Loại phần lặp trong caption | Đã đo trên full test và giữ lại |

Như vậy, không chính xác nếu mô tả toàn bộ công việc là chỉ can thiệp phần ảnh hoặc chưa can thiệp bước sinh caption. Có cả can thiệp vào tham số phần ngôn ngữ, prompt, độ dài giải mã và kiểm chứng sau sinh. Điều chưa đạt là một cơ chế kiểm chứng ngữ nghĩa đủ bao phủ và đáng tin cậy để cải thiện chất lượng tổng thể.

## 3 Tiêu chí đánh giá và cách đọc số liệu

### 3.1 Các thước đo caption

BLEU đo độ khớp các cụm từ với caption tham chiếu; bảng chính sử dụng BLEU 4. METEOR đánh giá khớp từ theo cách khác BLEU. ROUGE L dựa trên chuỗi con chung dài nhất. CIDEr sử dụng sự đồng thuận giữa caption và tham chiếu với trọng số cho các cụm từ. Các giá trị trong bảng được nhân 100 trừ khi nêu rõ khác đi. Lần chạy baseline này không tính SPICE.

Không thước đo văn bản nào tự chứng minh phát biểu trong caption đúng với ảnh. Một mô tả ngắn hơn có thể tăng điểm vì bớt lặp nhưng cũng có thể bỏ sót thay đổi. Một caption giống cách viết tham chiếu hơn có thể tăng điểm mà vẫn sai một chi tiết quan trọng. Do đó, công việc còn ghi lỗi bịa vật, lỗi ánh sáng, số fact đúng và phát biểu không được ảnh hỗ trợ.

CIDEr của các tập con trong báo cáo được tính lại với document frequency của chính tập con. Vì vậy, không so trực tiếp điểm CIDEr trên 12, 32 hay 128 cặp với điểm full test. Chỉ so các nhánh trong cùng bảng, cùng tập ảnh, cùng reference và cùng cách xử lý. Không dùng mức tăng ở pilot này để cộng vào điểm full của pilot khác.

### 3.2 Đánh giá thay đổi thật và lỗi do hình học

Một fact là một thay đổi cụ thể trong ảnh được ghi trước khi đọc output ở các lượt có rubric khóa trước. Ví dụ, fact có thể là người mới xuất hiện hoặc gối đổi từ xanh dương sang xanh lá. Fact đúng không đồng nghĩa toàn bộ caption đúng; một câu có thể vừa nhận đúng một thay đổi vừa thêm một vật không có thật.

Physical false positive là cặp có ít nhất một khẳng định thay đổi vật không được ảnh hỗ trợ. Khẳng định ánh sáng hoặc độ rõ được ghi riêng. Chỉ nhìn số lỗi vật giảm là chưa đủ, vì model có thể thay lời bịa vật bằng lời suy diễn ánh sáng. Với câu kiểu “more visible”, có trường hợp nó ám chỉ khung hình rộng hơn, nên báo cáo giữ cả nhãn rộng lẫn phân tích bảo thủ thay vì mặc định coi mọi câu như vậy là sai ánh sáng.

Các chỉ số đếm theo cặp không phải số phát biểu. Một cặp có ba lỗi và một cặp có một lỗi đều có thể được tính là một cặp có lỗi. Các fact trong một cảnh và các biến thể của cùng ảnh có tương quan, nên không coi chúng là các mẫu độc lập hoàn toàn.

### 3.3 Quy tắc đối chứng

Khi so SFT, cần giữ càng nhiều yếu tố giống nhau càng tốt: ảnh, target, seed, khởi tạo, thứ tự mẫu, số update, prompt và giải mã. Khi so hậu xử lý, hai nhánh phải được áp dụng cùng bộ lọc hoặc so raw với raw. Khi dùng LocateAnything, cần có nhánh chỉ viết lại caption nhưng không thêm quan sát định vị để tách tác động đổi prompt khỏi tác động grounding.

Ở các lượt đánh giá ẩn tên, trợ lý lưu nhận xét trước rồi mới mở khóa nhánh. Đây là biện pháp giảm thiên lệch trong thao tác, không tương đương nghiên cứu chấm mù bởi nhiều người độc lập. Những nhãn tái sử dụng phải có cùng ID, câu hỏi và toàn bộ caption, không chỉ có nội dung gần giống.

## 4 Danh mục các lượt thực nghiệm

Các mã dưới đây phục vụ tra cứu theo hướng xử lý. Đây không phải danh sách các tập test độc lập; nhiều lượt sử dụng lại ảnh, caption hoặc bối cảnh của lượt trước.

| Mã | Hướng thực nghiệm | Quy mô đánh giá chính | Trạng thái cuối |
|---|---|---|---|
| E01 | Tái lập checkpoint gốc | 1.570 cặp | Hoàn thành |
| E02 | LocateAnything định tính và COCO nhỏ | 4 truy vấn demo, 13 truy vấn stress, 48 truy vấn COCO | Định vị được nhưng có rủi ro ép sinh box |
| E03 | Viết lại caption bằng quan sát định vị | 24 cặp, 3 nhánh | Tăng Real, giảm Render |
| E04 | Kiểm chứng từng mệnh đề và màu | 24 cặp phát triển rồi 24 cặp kiểm tra mới | Sửa được 1 ca dev, không sửa ca mới |
| E05 | Continued SFT random và hard | 64 cặp, 4 nhánh | Tín hiệu nhỏ, bất định lớn |
| E06 | SFT nhãn rà trực quan | 256 cặp, nhiều đối chứng | Không đạt điều kiện cả hai miền |
| E07 | Lọc câu lặp | Full 1.570 caption baseline | Giữ lại trong pipeline |
| E08 | Prompt nhắc phân biệt camera | 60 cặp, 2 prompt | Giảm một loại lỗi nhưng mất fact |
| E09 | Căn chỉnh hình học và stress mở rộng | Diagnostic 60 cặp, mở rộng 8 cảnh | Loại bỏ tự động chặn theo khớp gần đúng |
| E10 | LoRA bất biến hình học ban đầu | 108 cặp, 2 nhánh | Không đạt điều kiện giữ fact Render |
| E11 | Merge BF16 so với LoRA FP32 riêng | 108 cặp, 2 chế độ | Khác số học không chuyển thành tăng chất lượng |
| E12 | Đối chứng loss không đổi | 72 cặp, 3 nhánh | Mixed đủ điều kiện pilot hẹp |
| E13 | Xác nhận trên cặp ảnh khác | 80 cặp, 3 nhánh | Tổng lỗi hình học không giảm |
| E14 | Cân bằng câu hỏi và probe template | 72 cặp và 4 ca nhân 10 câu hỏi | Chưa sửa được đánh đổi chất lượng |
| E15 | Full test adapter đã chọn | 1.570 cặp | Điểm giảm ở cả Real và Render |
| E16 | Kiểm soát độ dài caption | 3 lượt 23 ca, thêm 19 đối chứng cùng GPU | Giới hạn chiều dài, không sửa nhận diện ảnh |
| E17 | Đóng gói và kiểm tra chuyển máy | 4 file adapter, 392 tensor, 2 smoke case | Hoàn thành gói inference độc lập |

## 5 Tái lập baseline từ checkpoint công bố

### 5.1 Nguồn và phiên bản cố định

Repository là Yuan Liu 01 M3Diff. Checkpoint là IVC liuyuan M3Diff, dữ liệu ảnh là OmniDiff. Mã nguồn, weights và ảnh là các thành phần riêng; clone repo không tự có đủ trọng số hoặc ảnh. Tệp run_config của lần chạy ghi commit, revision và hash prompt, reference, runner. [H01]

{{VERSIONS}}

Các hash đầy đủ được giữ trong phụ lục nguồn và file cấu hình. Chốt revision giúp tránh việc người khác tải bản mới rồi cho rằng đang chạy đúng cùng một thực nghiệm.

### 5.2 Môi trường và suy luận

Lần chạy baseline dùng NVIDIA A10 với khoảng 23.028 MiB VRAM được công cụ báo cáo, BF16, không lượng tử hóa, temperature bằng 0, beam bằng 1, tối đa 1.024 token, cache bật, FlashAttention tắt và conversation mode qwen_2. Nhóm môi trường suy luận M3Diff về sau sử dụng Python 3.10, torch 2.2.2, transformers 4.40.0, peft 0.4.0 và accelerate 0.29.1; hồ sơ pip freeze là căn cứ chi tiết, không thay bằng mô tả môi trường chung.

Quy trình gồm chuẩn bị môi trường, tải repo và weights, tải ảnh đúng split, kiểm tra prompt, chạy smoke test, chạy hai tập test, kiểm tra đủ ID rồi chấm điểm. Kết quả được ghi JSONL và flush xuống đĩa theo từng caption. Khi ngắt, các ID đã hoàn thành được giữ lại và phần thiếu được chạy tiếp. Không được lấy một file 800 caption để báo đủ 803 cặp Real.

Notebook m3diff baseline full được chuẩn bị để chạy toàn quy trình trong môi trường Linux có GPU. Phần thực thi trên Modal dùng app và Volume để job có thể tách khỏi giao diện notebook. Vì thế, số thứ tự cell đang đứng không phản ánh phần trăm tổng công việc. Một cell có thể chứa vòng lặp hàng trăm cặp; những caption lặp dài có thể mất khoảng vài chục giây cho một cặp.

### 5.3 Kết quả baseline đầy đủ

{{BASELINE}}

Lần chạy hoàn tất đủ 803 Real và 767 Render. Đây là điểm baseline đo được của triển khai. Báo cáo không tự khẳng định bằng đúng bảng paper, vì muốn xác nhận điều đó cần đối chiếu cùng protocol, scorer, split và điều kiện giải mã của paper.

### 5.4 Điều gì đã được tái lập

Đã tái lập được đường đi từ cặp ảnh và câu hỏi tới caption, cách nạp checkpoint, quy trình đánh giá full test và lưu kết quả có thể kiểm tra. Chưa thực hiện lại toàn bộ pretraining hoặc instruction tuning quy mô ban đầu của tác giả. Việc tải một checkpoint rồi hiển thị vài ảnh demo sẽ yếu hơn bằng chứng hiện có, vì ở đây đã có toàn bộ caption và số đo full test.

## 6 LocateAnything và khả năng định vị vật

### 6.1 Vai trò trong pipeline

LocateAnything được dùng như bộ định vị theo mô tả để tìm vùng chứa vật được nhắc đến trong caption. Đầu ra chính trong các lượt thử là bounding box và văn bản tham chiếu. Nó không tự giải quyết toàn bộ bài toán ghép cùng một instance giữa hai ảnh, xác minh vật có biến mất hoặc xác định thuộc tính nào thay đổi. Các công dụng rộng hơn của model được trình bày trong model card chính thức; kết luận ở đây chỉ dựa trên các lượt đã chạy. [T03] [H02]

Một câu “hộp xanh biến mất” đòi hỏi ít nhất ba điều khác nhau: tìm được hộp trước thay đổi, tìm hoặc loại trừ cùng hộp sau thay đổi, và loại trừ khả năng bị khuất hoặc ra ngoài khung hình. Chỉ có box ở cả hai ảnh chưa bảo đảm cùng chiếc hộp; không có box cũng chưa chứng minh vật không tồn tại.

### 6.2 Demo và stress định tính

Đã chạy 4 truy vấn demo, gồm tìm hộp xanh trước và sau, tìm các hộp cùng tủ, và tìm người trong ảnh Render. Sau đó chạy 13 truy vấn trên ảnh gốc, ảnh nghiêng thật, xoay 2D, phóng ảnh bằng crop, thu ảnh có viền xám, ảnh nhỏ và các ảnh không có vật mục tiêu. Cấu hình LocateAnything dùng BF16, SDPA, hybrid decoding, seed 42; revision và môi trường torch 2.6.0 được lưu riêng, không trộn với môi trường M3Diff. [H02]

Quan sát bằng mắt cho thấy model có thể trả box quanh hộp xanh dưới nhiều biến đổi. Tuy nhiên, cảnh có nhiều hộp xanh nên chưa chứng minh tính nhất quán instance. Prompt single trả box sai trên cả 3 ảnh âm được thử. Với prompt all, hai ảnh âm sàn và phần cảnh dưới được trả None; chưa đủ dữ liệu để khẳng định all luôn từ chối đúng.

### 6.3 Kiểm tra nhỏ có annotation COCO

Đã dùng 12 cặp ảnh và truy vấn dương, 12 cặp âm theo annotation COCO, với 6 lớp car, chair, dog, cat, bottle và cup. Mỗi cặp được chạy cả single và all, tổng cộng 48 truy vấn. Việc không có annotation được dùng làm proxy cho ảnh âm, không coi là bảo đảm không có vật trong ảnh. Lựa chọn từ ảnh cache thuận tiện, không phải tái lập benchmark chính thức của LocateAnything. [H03]

{{COCO}}

Ở prompt all, 15 trong 22 box ground truth được ghép ở IoU ít nhất 0,5. Việc 11 trong 12 ảnh dương có ít nhất một hit không đồng nghĩa đã tìm đủ tất cả vật. Chỉ số đầu tiên là mức thành công theo truy vấn; 15 trên 22 phản ánh độ bao phủ box trong mẫu nhỏ này.

Kết quả cho thấy prompt có thể ảnh hưởng mạnh đến hành vi từ chối khi không có vật. Do đó, không dùng single như bằng chứng vật tồn tại hoặc dùng một box có vẻ hợp lý để hợp thức hóa caption. Đây là kết quả kiểm tra bộ định vị, chưa phải kết quả cải thiện M3Diff.

## 7 Ghép LocateAnything vào bước sinh caption

### 7.1 Thiết kế pilot viết lại caption

Pilot gồm 24 cặp tập trung vào vật, 12 Real và 12 Render. Danh sách chọn bằng seed và từ vựng vật trong caption baseline; reference không dùng để chọn hoặc quyết định sửa. Số truy vấn định vị bị giới hạn tối đa 2 trên mỗi cặp. Ba nhánh gồm baseline, control chỉ viết lại caption nháp, và grounded viết lại với các quan sát định vị. Không train thêm. [H04]

Nhánh control cần thiết vì thay prompt và yêu cầu viết lại tự nó có thể làm caption tốt hoặc xấu hơn. Nếu chỉ so baseline với grounded, không biết thay đổi điểm đến từ thông tin định vị hay cách yêu cầu LLM diễn đạt lại.

### 7.2 Kết quả pilot

{{GROUNDED}}

Ở Real, CIDEr grounded tăng từ 11,43 lên 19,06 so với baseline, trong khi một số metric khác không tăng. Ở Render, CIDEr giảm từ 16,42 xuống 7,47. Nhánh control cũng giảm mạnh ở Render, nên đổi prompt và viết lại toàn caption là một yếu tố cần lưu ý. Không thể dùng kết quả này để kết luận LocateAnything làm mọi miền kém đi, cũng không thể chỉ lấy mức tăng Real để tuyên bố pipeline tốt hơn.

### 7.3 Những giới hạn được phát hiện

Từ vựng truy vấn lấy từ caption nháp nên vật model bỏ sót ban đầu có thể không bao giờ được kiểm tra. Hai box cùng lớp chưa xác nhận cùng instance. Prompt có màu như “hộp xanh” có thể bỏ qua một hộp vẫn còn nhưng đã đổi màu. Một vật bị che khuất hoặc crop khỏi ảnh có thể bị nhầm là mất. Ngoài ra, yêu cầu viết lại toàn bộ caption có thể sửa đúng một câu nhưng tạo thêm lỗi ở câu khác.

Vì vậy, pipeline đã chuyển sang hướng sửa tối thiểu từng mệnh đề thay vì xem toàn bộ quan sát box là căn cứ đủ mạnh để sinh lại cả đoạn.

## 8 Bộ kiểm chứng từng mệnh đề và quy tắc màu

### 8.1 Phạm vi hỗ trợ

Mã kiểm chứng tách các mệnh đề xuất hiện hoặc biến mất theo mẫu ngôn ngữ và từ vựng được hỗ trợ. Vật được LocateAnything tìm bằng mô tả chung; hình học ước lượng vùng tương ứng; bằng chứng màu hoặc cấu trúc được dùng để xem mệnh đề có cần sửa. Đây là pipeline theo quy tắc và độ chắc của bằng chứng, không phải bộ hiểu mọi loại thay đổi. [H05]

Bản V4 tập trung một tình huống hẹp: caption nói vật biến mất nhưng vật có thể còn đó và đổi màu. Các điều kiện gồm định vị đủ rõ, ghép hình học đáng tin, IoU sau căn chỉnh ít nhất 0,8, ít nhất 30 pixel phần trong vùng nguồn phù hợp, tỷ lệ màu đích ít nhất 0,8 và erosion vùng nguồn 3 pixel. Màu tối hoặc trắng có các nhập nhằng riêng nên không được coi như mọi màu sắc khác. Ngưỡng là một phần của công thức đã chạy, không phải chuẩn đúng cho mọi ảnh.

### 8.2 Kết quả phát triển và kiểm tra mới

Trên 24 cặp phát triển đã sử dụng ở các vòng trước, V4 sửa 1 caption. Ở Render, CIDEr tăng từ 16,42 lên 20,87 trong khi BLEU 4 giảm từ 15,98 xuống 15,56. Real giữ nguyên. Đây là hiệu ứng tập trung vào một ca đã biết, không phải 24 ca độc lập mới đều được cải thiện.

{{VERIFIER_DEV}}

Sau khi khóa code và ngưỡng, pipeline chạy trên 24 cặp mới, 12 mỗi miền. Toàn bộ 48 ảnh không trùng ảnh phát triển hoặc trùng nhau trong đợt này; chưa bảo đảm tách scene. Có 8 truy vấn LocateAnything cần thiết. Kết quả là 0 trong 24 caption được sửa và toàn bộ metric giữ nguyên. [H06]

{{VERIFIER_VALIDATION}}

### 8.3 Ý nghĩa của kết quả không sửa

Không sửa khi bằng chứng thiếu giúp tránh tự thêm lỗi trong đợt này. Tuy nhiên, không sửa không chứng minh pipeline cải thiện caption; vấn đề chính là độ bao phủ thấp. Một quy tắc rất chặt có thể chỉ xử lý được ca nổi bật đã biết, còn phần lớn lỗi diễn đạt, tư thế, số lượng, OCR hoặc quan hệ giữa vật vẫn nằm ngoài phạm vi.

Hướng LocateAnything do đó chưa bị bác bỏ về nguyên tắc. Điều chưa thành công là cách ghép box, hình học và quy tắc hẹp đã thử. Cần phân biệt “có công cụ định vị chạy được”, “có một ca sửa đúng” và “có hệ thống kiểm chứng cải thiện trên tập mới”. Ba mức bằng chứng này không tương đương.

## 9 Continued SFT với mẫu ngẫu nhiên và mẫu khó

### 9.1 Giả thuyết và đối chứng

Giả thuyết của lượt này là continued SFT trên ảnh thật, đặc biệt các mẫu train baseline có CIDEr thấp, có thể sửa lỗi tốt hơn chỉ dùng mẫu ngẫu nhiên. Hai nhánh mới dùng 256 cặp mỗi nhánh, gồm 128 mẫu chính và cùng 128 mẫu replay. Nhánh hard lấy 128 mẫu khó theo train CIDEr; nhánh random lấy ngẫu nhiên từ cùng nhóm ứng viên. Cùng seed, số update và lịch huấn luyện. MDP được phép học, vision và projector đóng băng. [H07]

Lượt này dùng LoRA r16, alpha 32, learning rate 0,00001 và một epoch. Có thêm checkpoint fine tune cũ để đối chiếu thực dụng, nhưng nó khác dữ liệu và công thức nên không dùng riêng sự chênh lệch của nó để quy nguyên nhân.

### 9.2 Kết quả trên 64 cặp cố định

{{REAL_SFT}}

Nhánh random có tín hiệu tăng CIDEr ở cả hai miền trên tập con này. Tuy nhiên, khoảng bootstrap ghép cặp 95 phần trăm cho chênh lệch CIDEr so với baseline chứa 0: Real khoảng từ âm 26,26 đến dương 28,55; Render từ âm 8,55 đến dương 44,11. Đây là bootstrap giữ document frequency của tập con, chưa tính hết phụ thuộc scene hay biến thiên seed train.

Nhánh hard không tốt hơn random trên chỉ số chính; Real còn giảm rõ trong số đo điểm. Việc một mẫu có train CIDEr thấp không bảo đảm nó là ví dụ học tốt: có thể có nhãn mơ hồ, biến đổi khó, khác cách diễn đạt hoặc thông tin không nhìn thấy rõ. Điều này là diễn giải hợp lý cần kiểm tra, không phải nguyên nhân đã được tách bằng thực nghiệm riêng.

## 10 SFT với nhãn được rà trực quan

### 10.1 Chuẩn bị dữ liệu và các nhánh

Đã rà 48 cặp train và giữ 44 cặp, chia đều 22 Real và 22 Render; loại 4 cặp mơ hồ hoặc baseline đã mô tả hợp lý. Người rà là trợ lý, chưa có người gán nhãn độc lập xác nhận. Caption sửa thay cả nội dung lẫn độ dài và cách diễn đạt: trung vị nhãn gốc 77,5 từ và nhãn sửa 42 từ. Vì vậy, tác động chất lượng nhãn không được tách hoàn toàn khỏi tác động phong cách và độ chi tiết. [H08]

Mỗi nhánh gồm 216 bản ghi tương ứng 172 cặp duy nhất: 44 cặp được lặp hai lần và 128 cặp replay. Có ba đối chứng chính là nhãn gốc với LoRA và MDP, nhãn sửa với LoRA và MDP, và nhãn sửa chỉ LoRA khi MDP đóng băng. Cùng seed 42, r16, alpha 32, learning rate 0,00001, batch 1, tích lũy 8 và 27 update. Đã kiểm tra hash khởi tạo và thứ tự mẫu thực tế.

### 10.2 Kết quả và kiểm tra trực quan

Bộ đánh giá gồm 256 cặp, 128 mỗi miền. Real sử dụng ảnh mới so với các pilot trước; Render chỉ có 9 cặp dùng ảnh mới, phần còn lại có thể chia sẻ ảnh đã xem. Loại ID hoặc cặp ảnh trùng không bảo đảm loại được phụ thuộc giữa các scene. Baseline được chạy lại trên GPU họ A100 cho so sánh tập con, không lấy điểm full A10 làm baseline của bảng này.

{{CURATED}}

Nhánh nhãn sửa và MDP tăng CIDEr Real khoảng 3,87 nhưng giảm Render khoảng 3,71 so với baseline cùng bảng. Nhánh nhãn sửa chỉ LoRA tăng Real khoảng 3,30 nhưng giảm Render khoảng 2,77. Nhãn sửa cũng chưa vượt nhãn gốc trên cả hai miền. Khoảng bootstrap theo cụm ảnh chung cho chênh lệch Real của nhánh nhãn sửa và MDP chứa 0, khoảng âm 1,64 đến dương 12,71.

Trên 16 cặp chấm trực quan ẩn tên, nhãn sửa và MDP có 2 thắng, 3 thua, 11 hòa so với baseline; nhãn sửa chỉ LoRA có 3 thắng, 2 thua, 11 hòa. Hòa hoặc thắng tương đối không có nghĩa caption đúng hoàn toàn: nhiều cặp cả hai bản vẫn có cùng lỗi về tư thế, vật mất hoặc đồ vật thay thế.

Hai nhánh nhãn sửa không đạt điều kiện tăng CIDEr ở cả hai miền. Vì vậy, không chọn chúng làm checkpoint thay baseline và không dùng kết quả pilot để tự suy ra cải thiện chống xoay hay zoom.

## 11 Lọc câu lặp nguyên văn sau sinh

### 11.1 Cơ chế và phạm vi

Bộ lọc giữ nguyên các phát biểu khác nhau và loại phần lặp nguyên văn sau chuẩn hóa khoảng trắng trong những trường hợp được hỗ trợ. Nó không paraphrase, không tự đổi tên vật, không xác minh ảnh và không tự sửa mệnh đề xuất hiện hoặc biến mất. Câu nhắc ghế bên trái khác câu nhắc ghế bên phải; chuỗi OCR khác hoa thường có thể mang ý nghĩa khác, nên không gộp theo mức gần nghĩa tùy tiện. [H09]

Bộ lọc được chấm trên toàn bộ caption baseline đã lưu, không cần gọi lại GPU. Kết quả trước và sau vì thế khác nhau ở xử lý văn bản, không khác lần suy luận hay hardware.

{{DEDUP}}

Chỉ 15 trong 1.570 caption thay đổi, gồm 3 Real và 12 Render; 1.555 caption còn lại giữ nguyên. BLEU 4 tăng chủ yếu do cắt những vòng lặp dài. CIDEr tăng ít, phù hợp với nhận định đây là chỉnh chất lượng trình bày hơn là thêm năng lực nhận diện khác biệt.

### 11.2 Phiên bản xử lý câu dính liền

Bản v2 xử lý thêm các câu lặp dính liền sau dấu chấm, có kiểm tra dấu nháy, số thập phân, từ viết tắt, vị trí trái phải và thứ tự hàng. Bộ kiểm tra trên 3.860 caption xác nhận đầu ra là chuỗi con theo thứ tự token của văn bản vào và giữ các mệnh đề hoàn chỉnh khác nhau theo cách tách câu đang sử dụng. Chỉ 1 caption pilot khác v1; trên full baseline và full candidate, v1 và v2 cho cùng dự đoán và điểm. [H19]

Những kiểm tra chuỗi không phải chứng minh đúng ngữ nghĩa trên mọi văn bản. Một chuỗi mô tả hàng thứ ba, thứ tư và thứ năm khác nhau không bị xóa chỉ vì model đang liệt kê bịa; muốn sửa bịa cần bằng chứng ảnh.

## 12 Diagnostic xoay và zoom cùng thử nghiệm prompt

### 12.1 Thiết kế dữ liệu

Diagnostic dùng 12 cảnh đã được xem trong quá trình phát triển. Mỗi cảnh có 4 cặp kiểm soát cùng ảnh và 1 cặp tự nhiên: identity, zoom 1,10 lần, xoay 8 độ có crop phù hợp, xoay âm 8 độ kèm zoom, và cặp có thay đổi tự nhiên. Tổng 60 cặp, hai prompt và 120 caption. Tách 6 cảnh dev và 6 cảnh validation chỉ áp dụng bên trong diagnostic này. [H10]

Hai prompt là câu hỏi gốc và câu hỏi nhắc phân biệt camera hoặc crop với thay đổi vật. Model và cấu hình giải mã giữ nguyên, không train thêm. Fact của các cặp tự nhiên được ghi trước khi đọc output mới; caption được cùng lọc lặp trước khi chấm ẩn tên prompt.

### 12.2 Kết quả đổi prompt

{{PROMPT_GEOMETRY}}

{{PROMPT_GEOMETRY_ERRORS}}

{{PROMPT_FACTS}}

Ở validation, prompt camera giảm lỗi bịa vật trên 18 cặp xoay zoom từ 14 xuống 12. Tuy nhiên, khẳng định ánh sáng đổi tăng từ 6 lên 14, và không caption nào nêu rõ camera hoặc framing đổi. Tổng fact đúng trên 12 cặp tự nhiên của cả diagnostic giảm từ 9 trên 22 xuống 6 trên 22. Không thể lấy mức giảm một loại lỗi để kết luận prompt đã giúp model hiểu hình học.

Một vài điều kiện hẹp ở validation có tín hiệu thuận lợi, nhưng kết quả toàn diagnostic chưa phù hợp để thay cấu hình chính. Không tiếp tục dùng prompt camera làm mặc định.

## 13 Căn chỉnh ảnh trước khi chốt caption

### 13.1 Cách làm và kết quả ban đầu

Bộ căn chỉnh sử dụng SIFT và RANSAC để ước lượng biến đổi toàn ảnh. Nếu phần ảnh chung khớp rất sát và phần sai khác còn lại đủ nhỏ theo ngưỡng, phiên bản ban đầu có thể thay caption bằng mô tả đổi khung hình hoặc không đổi vật. Ảnh không đủ bằng chứng thì giữ caption M3Diff. Đây là sửa pipeline, không train lại model. [H10]

Ngưỡng được chọn trên 6 cảnh dev rồi khóa cho 6 cảnh validation. Diagnostic ban đầu nhận 27 trong 36 cặp chỉ xoay zoom và 12 trong 12 identity; không chặn nhầm 12 cặp tự nhiên trong mẫu đó. Lỗi vật trên 24 cặp validation gồm identity và hình học giảm từ 19 xuống 5. Những số này từng tạo tín hiệu tích cực nhưng chưa đủ bao phủ thay đổi nhỏ.

### 13.2 Kiểm tra mở rộng làm thay đổi quyết định

Đã mở rộng sang 8 bố cục khác và kiểm tra các chỉnh sửa pixel biết trước, gồm đảo màu mảng nhỏ, nét mảnh, thay sáng và kết hợp biến đổi hình học với sửa nội dung. Trên 56 stress appearance chính, phiên bản căn chỉnh trả nhầm không đổi ở 20 trường hợp. Với mảng 32 nhân 32 và biến đổi kèm theo, có trường hợp thay đổi thật bị ngưỡng dung sai hoặc vùng chung che mất. [H11]

{{REGISTRATION_COVERAGE}}

{{REGISTRATION_STRESS}}

{{REGISTRATION_COMPOSED}}

Các bảng stress cơ bản có 32 ca và stress kết hợp có 24 ca, tổng 56 ca chính. Tổng số chặn nhầm tương ứng là 9 cộng 11 bằng 20; không nhầm mẫu số 56 với 7 cặp tự nhiên được xác nhận riêng.

Trong 7 cặp tự nhiên được xác nhận có thay đổi rõ, không có ca bị chặn nhầm. Kết quả đó không xóa các phản ví dụ synthetic. Ngược lại, stress pixel cũng không phải ước lượng tỷ lệ bỏ sót vật thể tự nhiên ngoài đời; nó chỉ chứng minh cơ chế chặn có thể bỏ qua một chỉnh sửa đã biết.

### 13.3 Chính sách giữ lại sau kiểm tra

Bản safe pipeline chỉ tự trả không đổi khi hai ảnh sau giải mã RGB có cùng kích thước và giống từng pixel. Những ảnh chỉ gần giống, đã xoay hoặc zoom vẫn đi qua model. Căn chỉnh gần đúng chỉ tạo thông tin gợi ý để rà soát, không ghi đè caption. Đã chạy kiểm tra CLI cho identity, zoom out, sửa mảng màu, vừa zoom vừa sửa mảng và cặp tự nhiên có thêm người.

Exact identity guard không giúp xử lý thay đổi camera ngoài đời. Nó giải quyết một miền nhỏ nhưng có điều kiện kiểm chứng rõ: ảnh đầu vào được model nhìn thấy giống nhau sau giải mã. Không diễn đạt kết quả này thành hệ thống đã có khả năng xác minh không thay đổi dưới mọi góc chụp.

## 14 LoRA bất biến hình học ban đầu

### 14.1 Dữ liệu và công thức train

Mục tiêu là cho model thấy các cặp khác hình học nhưng không đổi vật, thay vì chỉ sửa lời nhắc lúc inference. Tập gồm 64 negative từ 16 ảnh train gốc và 192 positive. Bốn điều kiện negative gồm identity, zoom in, roll và zoom out đảo chiều. Positive gồm replay và các cặp đã rà trực quan. Không đưa các ảnh stress sửa pixel của evaluation vào train. [H12]

Đã kiểm tra hash RGB của 360 ảnh train gốc và 40 ảnh đánh giá gốc, không phát hiện trùng chính xác. Kiểm tra này không bảo đảm tách scene, không loại mọi ảnh tương tự và không làm mất thực tế checkpoint gốc đã học dữ liệu train chính thức từ trước.

LoRA dùng r16, alpha 32, learning rate 0,000005, một epoch, batch 1, gradient accumulation 8 và 32 update. Vision, projector và MDP đóng băng. Sau train có kiểm tra chỉ tham số LoRA được cập nhật.

### 14.2 Kết quả trên 108 cặp

Baseline và candidate được chạy trong cùng GPU container trên 60 cặp diagnostic cũ và 48 cặp từ phần mở rộng, tổng 108 cặp mỗi nhánh. Không bật căn chỉnh hay prompt camera để tránh trộn tác động. Hai bên được cùng lọc lặp, đánh giá ẩn tên rồi giải khóa.

{{INVARIANCE_FIRST}}

{{INVARIANCE_FACTS}}

Trên 32 cặp hình học ở 8 cảnh mới của lượt này, lỗi vật giảm 31 xuống 28. Nhưng fact mới ở Render giảm từ 4 trên 8 xuống 3 trên 8, trong khi tổng fact mới chỉ giữ 5 trên 12 ở cả hai bản. Nhánh không đạt điều kiện bảo toàn fact theo miền. Ít bịa hơn không bù được việc bỏ mất hoặc mô tả sai thay đổi thật.

## 15 Kiểm tra độ chính xác số của LoRA

### 15.1 Vì sao kiểm tra merge

Khi delta LoRA nhỏ được gộp vào trọng số nền BF16, một phần cập nhật có thể bị làm tròn. Do đó, trước khi cho rằng công thức dữ liệu hoàn toàn không có tác động, đã kiểm tra liệu bước nạp hoặc merge có đang làm mất cập nhật đã học hay không. Đây là kiểm tra kỹ thuật để xác nhận model đang thực sự sử dụng adapter. [H13]

Phép đo trên 21 ma trận lấy mẫu ở các tầng 0, 14 và 27 cho thấy chỉ khoảng 5,539 phần trăm phần tử trọng số nền thay đổi sau merge BF16; sai số L2 tương đối trung bình của cập nhật so với phép cộng FP32 là khoảng 0,951. Không được diễn giải con số 0,951 thành mất 95,1 phần trăm accuracy hoặc 95,1 phần trăm caption sai.

### 15.2 So caption cùng checkpoint

So sánh merge BF16 với giữ adapter FP32 riêng trên cùng 108 cặp. Đã xác nhận 392 tensor adapter được nạp và FP32 khôi phục đúng giá trị đã lưu. Tất cả LoRA B được kiểm tra khác 0.

{{PRECISION}}

{{PRECISION_FACTS}}

Giữ LoRA FP32 riêng không giúp tăng chất lượng trong phép thử này: lỗi vật mới tăng từ 28 lên 30 trên 32 cặp, và fact cũ Real giảm từ 7 xuống 6 trên 12. Có 51 trong 108 caption hiển thị trùng giữa hai chế độ. Kết quả loại bỏ suy luận đơn giản rằng chỉ cần tránh merge là sửa được lỗi mô tả. Các thí nghiệm tiếp dùng FP32 riêng để giữ cập nhật rõ ràng về số học, không vì chế độ này đã chứng minh chất lượng tốt hơn.

## 16 Đối chứng loss không đổi với công thức mạnh hơn

### 16.1 Thiết kế để tách tác động negative

Lượt này giữ đúng 256 bản ghi với 192 positive và 64 negative. Hai nhánh bắt đầu cùng khởi tạo, cùng ảnh, câu hỏi, target, thứ tự epoch và lịch optimizer. Nhánh positive control vẫn forward negative nhưng nhân loss của chúng với 0; nhánh mixed objective nhân với 1. Như vậy, khác biệt chủ định là đóng góp gradient từ mục tiêu không đổi. [H14]

Cả hai dùng learning rate 0,00002, hai epoch và 64 update, r16, alpha 32; vision, projector và MDP đều đóng băng. Mỗi nhánh forward 384 lượt positive và 128 lượt negative. Có kiểm tra khởi tạo LoRA và MDP, hai thứ tự epoch, finite loss và trạng thái chỉ LoRA trainable. Zero weight không có nghĩa hoàn toàn không tham gia lịch optimizer, nhưng hai nhánh được giữ lịch như nhau.

### 16.2 Kết quả trên 72 cặp

Bộ gồm các cặp hình học và tự nhiên mới trong đợt phát triển, cùng các cặp tự nhiên và identity cũ. Tổng 216 caption của ba model. Các caption được chấm trước khi giải khóa; nhãn chỉ tái dùng nếu case, câu hỏi và caption khớp hoàn toàn.

{{ABLATION}}

Mixed giảm lỗi vật từ 31 xuống 21 trên 32 cặp hình học, trong khi positive control còn 27. Tổng fact tự nhiên ở các nhóm được xác nhận là baseline 14 trên 34, control 11 trên 34 và mixed 15 trên 34. Mixed đạt điều kiện pilot hẹp để tiếp tục đặc tả rộng hơn; control không đạt vì mất fact cũ.

Tuy vậy, mixed tăng số suy diễn ánh sáng từ 7 lên 15 trên 32 cặp. Tổng lỗi vật, ánh sáng và giải thích hình học chỉ giảm từ 32 xuống 29. Có một trường hợp nói xoay 90 độ trong cặp thực tế chỉ zoom out. Không coi câu này là nhận ra camera đúng.

Kết quả là tín hiệu cho giả thuyết học negative, không phải bằng chứng model mới tốt hơn tổng thể. Những ảnh này đã được xem ở các vòng trước, chỉ một seed và một họ augmentation 2D.

## 17 Xác nhận trên 80 cặp khác

### 17.1 Chọn ảnh và khóa fact

Chọn 16 cặp nguồn, 8 Real và 8 Render, rồi tạo identity, zoom in, roll, zoom out và cặp tự nhiên cho mỗi nguồn, tổng 80 cặp. Ba model sinh 240 caption trong cùng một GPU container A10. Ảnh được loại trùng RGB với nguồn train, diagnostic và gallery trước; fact tự nhiên được ghi sau khi xem ảnh và trước khi đọc caption mới. [H15]

Giới hạn quan trọng là 11 trong 16 cặp vẫn có bối cảnh quen. Chỉ 5 bối cảnh Real ít quen với diagnostic trước và không có Render mới hoàn toàn theo bối cảnh. Một số cặp Render còn chia sẻ bối cảnh trong chính lượt này. Vì vậy, không gọi đây là 16 scene độc lập chưa thấy.

### 17.2 Kết quả chính

{{CONFIRMATION}}

Mixed giảm lỗi vật từ 36 xuống 29 trên 48 biến thể hình học. Nhưng tổng lỗi rộng giữ nguyên 44 trên 48. Trên 16 identity, số cặp bịa khác biệt giảm từ 16 xuống 6. Fact tự nhiên tăng từ 19 trên 24 lên 20 trên 24; số cặp tự nhiên có claim không được hỗ trợ giữ nguyên 9 trên 16.

Ở 5 bối cảnh Real ít quen, lỗi vật giảm 11 xuống 5 trên 15 cặp, nhưng tổng lỗi vẫn 12 trên 15. Điều này củng cố nhận định có chuyển loại lỗi chứ chưa chứng minh khắc phục vấn đề hình học tổng thể.

### 17.3 Vì sao vẫn chấm full test

Candidate đã được chọn từ pilot trước khi đọc điểm full, và giữ nguyên lựa chọn để đo hậu quả trên benchmark rộng hơn. Lượt full là đặc tả thêm checkpoint đã chọn, không dùng để đổi sang một adapter khác có điểm đẹp hơn. Tuy nhiên, bộ xác nhận đã cho thấy điều kiện tổng lỗi không cải thiện, nên không được trình bày full test như bước xác nhận một phương pháp đã thành công.

## 18 Kiểm tra mất cân bằng cách hỏi

### 18.1 Phát hiện từ dữ liệu

Dữ liệu positive có 10 kiểu câu hỏi với tần suất khoảng 16 đến 25 bản ghi mỗi kiểu. Toàn bộ 64 negative lại dùng cùng câu “What's the difference between 2 images?”. Sự tương quan này tạo nguy cơ model học tín hiệu ngôn ngữ để trả lời không đổi thay vì học sự bất biến hình học. Đây là nguy cơ quan sát được trong dữ liệu; không tự chứng minh shortcut thực sự là nguyên nhân của mọi kết quả. [H17]

### 18.2 Nhánh cân bằng template

Nhánh mới giữ ảnh, target, thứ tự, khởi tạo và 64 update, chỉ phân phối câu hỏi của negative vào 10 kiểu. Kiểm tra xác nhận cùng khởi tạo và thứ tự hai epoch; không khẳng định dropout mask giống nhau khi độ dài câu hỏi đổi.

{{BALANCED}}

Lỗi vật giảm 31 xuống 20 trên 32 cặp, nhưng fact cũ Real giảm 7 xuống 6. Có trường hợp động tác gập người về trước bị gọi thành uốn người ra sau. Nhánh không đạt điều kiện bảo toàn fact đã định, nên không chọn cho full benchmark.

### 18.3 Probe 10 template trên 4 ca

Đã lấy 4 ca nguồn cố định và chạy 10 kiểu câu hỏi cho mỗi ca, ba model và tổng 120 caption. Đây là 4 ca lặp ngôn ngữ, không phải 40 scene độc lập. [H18]

{{TEMPLATE_PROBE}}

Mixed có 22 trên 40 lỗi vật so với baseline 40 trên 40, nhưng nhãn lỗi rộng vẫn 39 trên 40. Nếu loại những câu độ rõ mơ hồ khỏi lỗi chắc thì mixed còn 29 trên 40; balanced còn 30 trên 40. Cả hai có 10 câu chỉ nói more visible. Không coi câu mơ hồ đó là hiểu đúng cơ chế camera, cũng không tự kết tội nó là thay đổi nguồn sáng.

Probe chưa chứng minh mọi tiến bộ chỉ xuất hiện ở đúng một template train. Việc cân bằng template cũng chưa khắc phục đánh đổi fact. Không dùng probe để đảo quyết định loại nhánh balanced đã thất bại ở tiêu chí factual.

## 19 Full benchmark của adapter mixed đã chọn

### 19.1 Protocol và kiểm tra hoàn tất

Giữ 10 kiểu câu hỏi chính thức và đúng 1.570 cặp. Không thay toàn bộ câu hỏi bằng prompt cố định của diagnostic. Base chạy BF16, adapter FP32 riêng, greedy, beam 1, tối đa 1.024 token và không FlashAttention. Không bật exact identity guard hoặc căn chỉnh để tránh trộn tác động vào model. [H16]

Danh sách Real rồi Render được chia thành 5 chunk: 320, 320, 320, 320 và 290. Thứ tự dispatch được khóa là 0, 3, 1, 2, 4 để có dữ liệu cả hai miền nếu ngân sách buộc dừng. Mỗi job có timeout tối đa 1.800 giây, ngắt subprocess sớm hơn 100 giây để lưu kết quả. Trên thực tế cả 5 chunk đều hoàn tất, không cần lượt resume dở dang.

{{BATCHES}}

Các bước kiểm tra xác nhận đủ 1.570 ID duy nhất, đúng tập ID từng chunk, caption không rỗng, hash adapter giống nhau, 392 tensor được phục hồi FP32 và pip freeze giống nhau giữa 5 chunk. Tổng thời gian function được ghi cho 5 lượt khoảng 95,3 phút, riêng phần full candidate; không phải tổng thời gian mọi công việc hoặc tổng thời gian training.

Baseline full dùng A10; candidate có 4 chunk A10G và 1 chunk A10. Đây là cùng họ GPU nhưng không phải phép thử hai model trên cùng GPU vật lý cho mọi cặp. Lượt đối chứng pilot có kiểm soát GPU chặt hơn; full benchmark ghi nhận điểm thực tế triển khai và giới hạn hardware này. Không khẳng định greedy luôn khớp từng ký tự khi đổi thiết bị.

### 19.2 Kết quả raw và sau cùng bộ lọc

{{FULL_PRIMARY}}

Ở cả hai miền, mixed thấp hơn baseline trên BLEU 4, METEOR, ROUGE L và CIDEr. Sau lọc lặp, CIDEr Real giảm khoảng 1,617 điểm và Render giảm khoảng 10,684 điểm. Không so baseline raw với candidate clean để tạo cảm giác nhánh mới tốt hơn. Cùng bộ lọc v1 và v2 cho cùng đầu ra full test trong cả hai model.

### 19.3 Độ dài và hành vi lặp

{{BEHAVIOR}}

Caption mixed có trung vị ngắn hơn, nhưng số caption Render từ 500 từ theo cách tách khoảng trắng trở lên tăng từ 11 lên 19. Như vậy, ngắn hơn ở trung vị không có nghĩa lỗi đuôi dài đã được giải quyết. Thống kê từ theo khoảng trắng không đồng nghĩa số token của tokenizer.

### 19.4 Quyết định triển khai

Không chọn mixed làm model chính. Nhánh đã không giảm tổng lỗi trên confirmation và còn giảm metric caption ở full test. Trọng số vẫn được lưu để nghiên cứu và đối chứng. Bản khuyến nghị hiện tại là checkpoint công bố, có thể kèm lọc lặp nguyên văn và guard identity với điều kiện pixel rõ ràng.

## 20 Kiểm soát độ dài sinh caption

### 20.1 Mục tiêu và thiết kế

Các ca sinh lặp gần 1.000 từ làm inference chậm, nên đã thử giới hạn 256 và 128 token. Đây là thử nghiệm vận hành sau benchmark, không thay điểm full hoặc mặc định tái lập 1.024 token. Không train thêm. [H20]

Lượt LoRA 256 gồm 19 cặp natural từ pilot đã có rubric, loại cặp clothesline chưa chắc, và 4 caption dài nhất trong phần full candidate đã hoàn tất lúc khóa danh sách. Lượt baseline dùng cùng 19 natural và 4 ca dài nhất của full baseline. Mỗi lượt gồm 23 ca; các ca dài của hai model không giống nhau, nên không dùng chúng làm tập so chất lượng trực tiếp giữa hai model.

### 20.2 Tách so sánh cache và đối chứng cùng GPU

Cache natural trước đó chạy A100, còn các lượt cap dùng A10 hoặc A10G. Chỉ 8 trên 19 natural của LoRA 256 và 6 trên 19 baseline 256 khớp cache cũ, dù không ca natural nào chạm 256. Do đó, không quy mọi thay đổi caption cho cap; biến thiên giữa lượt và thiết bị là yếu tố cần kiểm soát.

Lượt baseline 128 bổ sung đối chứng ngay trên cùng loaded model, cùng GPU và cùng tensor ảnh: sinh 1.024 token tối đa trước, rồi sinh 128 cho 19 ca natural. Bốn ca dài chỉ sinh cap nhỏ; không chạy đối chứng dài 1.024 cùng lượt nên không có số tăng tốc ghép cặp cho nhóm dài.

{{CAPS}}

### 20.3 Kết quả và giới hạn

Trong đối chứng cùng GPU, 18 trên 19 natural ở 128 khớp hoàn toàn caption 1.024. Một caption kitchen có output control 149 slot token và bị chặn ở 128. Nó mất phần đuôi mô tả; không mặc định coi phần bị cắt là fact thật, vì caption control vẫn có thể có claim bịa.

Các ca rất dài đều chạm giới hạn 128 hoặc 256, với phần văn bản trước điểm cắt khớp phần đầu cache trong các ca đã kiểm tra. Điều này chứng minh cap có tác dụng giới hạn chiều dài, không chứng minh nó làm nội dung đúng hơn. Ở natural, trung vị thời gian sinh control khoảng 2,78 giây và candidate khoảng 2,72 giây, nhưng control luôn chạy trước nên có yếu tố warm up và thứ tự; không diễn giải thành tăng tốc tổng thể đáng kể.

Một lượt phụ ban đầu lỗi do thiếu import sys trước khi gọi subprocess; đã sửa và chạy lại đủ 23 ca. Lỗi này không làm thay đổi caption hoặc điểm full benchmark. Kết quả thành công và source các lượt probe đều được lưu riêng.

Giữ mặc định 1.024 cho tái lập. Mốc 256 có thể là tùy chọn demo khi chấp nhận khả năng cắt đầu ra trên ảnh khác; chưa có full test với cap 256 để gọi là cấu hình chất lượng tốt hơn. Không chọn 128 làm mặc định vì đã có phản ví dụ cắt cụt caption natural.

## 21 Kiểm tra nạp trọng số và chuyển máy

### 21.1 Những thành phần cần mang theo

Gói portable gồm adapter LoRA đã train, cấu hình, runner, requirements, notebook và báo cáo đánh giá. Base M3Diff đúng revision được tải riêng. Chuyển máy chỉ yêu cầu cài môi trường và nạp weights, không cần train lại. Chỉ copy notebook mà không có adapter không mang theo phần đã học. [H21]

Adapter selected có 161.616.362 byte và 392 tensor, tương ứng 196 cặp ma trận LoRA A và B; khoảng 40,37 triệu tham số trainable. Trạng thái ngoài LoRA trong nhánh này rỗng vì các thành phần nền đóng băng. Runner giữ LoRA FP32 riêng và base BF16.

### 21.2 Kiểm tra tính toàn vẹn

Đã đối chiếu hash của 4 file adapter với file đã nạp trên GPU, kiểm tra CRC toàn bộ file weights dạng torch ZIP, xác nhận nạp đủ 392 tensor và khôi phục đúng giá trị lưu. Một lần tải file lớn ban đầu có lỗi CRC dù dung lượng đúng, nên đã thay bằng tải tuần tự và chỉ nhận file sau khi SHA và CRC đều đạt.

Portable runner khớp 2 trên 2 caption với runner tham chiếu trên cùng GPU trong smoke test. Đây là kiểm tra đường nạp và hai ca cụ thể, không bảo đảm mọi caption trên GPU khác khớp từng chữ. Kiểm tra còn xác nhận đổi tên thư mục adapter không làm loader chọn nhầm kiến trúc, và base được truyền bằng đường dẫn ở máy mới thay vì phụ thuộc đường dẫn cũ trên Modal.

### 21.3 Tránh lấy nhầm kết quả đã lưu

Runner lưu fingerprint câu hỏi, file ảnh, adapter, cấu hình và source cùng output. Nếu đổi ảnh nhưng giữ cùng tên hoặc ID, runner chặn dùng lại output cũ. CPU check đã kiểm tra ảnh cùng RGB nhưng metadata khác, cùng input resume được, một pixel khác không tự coi là giống hệt, và ghi đè ảnh cùng đường dẫn làm stale output bị từ chối.

Các kiểm tra này ngăn một số lỗi quy trình, không thay đánh giá ngữ nghĩa ảnh. Fingerprint base trong runner không phải phép kiểm tra hash toàn bộ hàng chục GB shard base cho mỗi lượt; nguồn base phải được chuẩn bị đúng revision như hướng dẫn.

### 21.4 Trạng thái sản phẩm

Notebook portable mặc định USE_ADAPTER bằng False để dùng model gốc. Bật True mới chạy adapter thử nghiệm đã giảm điểm. Requirements và cấu hình đã dùng dành cho Linux hoặc WSL và server GPU có môi trường phù hợp; không khẳng định chạy được trên Windows CPU thuần hoặc mọi GPU. Notebook đã kiểm tra cú pháp và CLI đã chạy GPU, chưa có một lượt Run all độc lập trên một máy GPU mới hoàn toàn.

{{ARTIFACTS}}

## 22 Tổng hợp hướng nào có hiệu quả

| Hướng | Tín hiệu đạt được | Điều chưa đạt | Quyết định |
|---|---|---|---|
| Tái lập checkpoint | Đủ 1.570 caption và metric | Không train lại quy mô tác giả | Hoàn thành phần tái lập |
| Lọc lặp | BLEU 4 full tăng hai miền | Không xác minh câu bịa | Giữ trong pipeline |
| Exact identity guard | Nhận trường hợp RGB giống hệt | Không xử lý góc nhìn gần giống | Giữ như nhánh đặc biệt |
| LocateAnything | Định vị chạy được, all có tín hiệu từ chối tốt hơn single trong mẫu nhỏ | Không tự ghép instance và xác minh thay đổi | Có tiềm năng nhưng chưa đủ bằng chứng cải thiện M3Diff |
| Viết lại toàn caption có grounding | CIDEr Real pilot tăng | Render giảm mạnh | Không áp dụng mặc định |
| Verifier màu V4 | Sửa 1 ca phát triển | 0 ca được sửa trên validation mới | Chưa khái quát |
| Random hoặc hard SFT | Một số điểm pilot tăng | Bất định và phụ thuộc miền lớn | Chưa chọn thay baseline |
| SFT nhãn sửa | Có tăng Real | Giảm Render, style và độ dài cùng đổi | Không đạt điều kiện |
| Prompt xét camera | Giảm lỗi vật hẹp | Suy ánh sáng tăng, tổng fact giảm | Không dùng mặc định |
| Căn chỉnh gần đúng | Diagnostic đầu đẹp | Bỏ sót 20 trên 56 stress mở rộng | Không cho tự ghi đè caption |
| LoRA không đổi | Giảm lỗi vật trong diagnostic | Tổng lỗi confirmation không giảm, full điểm giảm | Checkpoint nghiên cứu |
| Giữ LoRA FP32 | Đảm bảo giá trị adapter rõ ràng | Không tự tăng chất lượng | Giữ cho kiểm soát kỹ thuật |
| Giới hạn token | Chặn chiều dài ở ca lặp | Có thể cắt cụt mô tả | Tùy chọn vận hành, chưa đổi mặc định |

## 23 Giải thích lựa chọn và những điều cần rút kinh nghiệm

### 23.1 Vì sao đã thử fine tune với cặp không đổi

Giả thuyết ban đầu là model nhầm thay đổi góc nhìn với thay đổi vật, nên cần thêm ví dụ huấn luyện mà hai ảnh khác hình học nhưng không đổi nội dung. LoRA có thể kiểm tra giả thuyết với số tham số nhỏ hơn train toàn model, giữ checkpoint nền và cho phép đối chứng. Dữ liệu negative đi kèm positive để tránh chỉ dạy model trả không đổi.

Kết quả cho thấy một phần hành vi ngôn ngữ thay đổi theo hướng ít nói vật biến đổi hơn. Tuy nhiên, nhánh chủ yếu cập nhật phần ngôn ngữ khi vision và MDP đóng băng, nên chưa chứng minh nó đã học biểu diễn hình học tốt hơn. Việc chuyển sang mô tả ánh sáng là dấu hiệu cần nghi ngờ học chiến lược trả lời thay vì hiểu camera. Đây là diễn giải từ hành vi, không phải phép đo nhân quả trực tiếp bên trong model.

### 23.2 Vì sao định vị vật không tự làm caption tốt hơn

LocateAnything giải một phần của grounding; caption khác biệt cần thêm quan hệ giữa hai thời điểm. “Tìm được ghế” khác “ghép đúng ghế đó”, và lại khác “xác minh ghế đổi màu hay bị khuất”. Nếu bước sửa không xử lý được các mối quan hệ này, thông tin box có thể làm LLM tự tin hơn về một câu sai.

Thử nghiệm đã có hai mức can thiệp: viết lại cả đoạn và sửa từng mệnh đề. Mức đầu có rủi ro thay đổi phân phối diễn đạt và thêm lỗi; mức sau tránh sửa bừa nhưng độ bao phủ thấp. Hướng cần tiếp tục là bộ kiểm chứng thay đổi có scope rõ và có trường hợp không kết luận, không đơn thuần gắn thêm một lượt định vị vào cuối caption.

### 23.3 Điều cần làm khác ở vòng nghiên cứu sau

Cần chốt trước tiêu chí tổng lỗi và giữ fact theo miền, thay vì để số lỗi vật giảm trở thành tín hiệu chính quá lâu. Cần một validation tách scene chưa dùng cho phát triển và một tập kiểm tra cuối không dùng để chọn nhánh. Các nhánh bị giảm Render hoặc không giảm tổng lỗi phải được xem là thất bại theo mục tiêu chính, dù vẫn đáng lưu để phân tích.

Full benchmark giúp phát hiện mức suy giảm lớn mà pilot chưa cho thấy, nhưng không thể sửa chất lượng bằng việc chấm nhiều hơn. Phần việc tiếp theo nên tập trung vào một giả thuyết và một thí nghiệm phân biệt được nguyên nhân, rồi mới mở rộng đánh giá. Không tiếp tục dò nhiều ngưỡng trên chính các ca vừa dùng để báo cáo thành công.

## 24 Hướng đề xuất tiếp theo cho kiểm chứng caption

Phần này là đề xuất nghiên cứu, chưa được triển khai và chưa có kết quả cải thiện mới. Các nguồn về change captioning dưới distractor hoặc học biểu diễn bất biến chỉ cung cấp cơ sở tham khảo, không bảo đảm ghép vào M3Diff sẽ thành công. [T04] [T05]

### 24.1 Pipeline kiểm chứng theo từng phát biểu

M3Diff sinh caption nháp. Bước phân tích tách từng mệnh đề thành vật, thuộc tính, quan hệ trước sau và loại thay đổi. LocateAnything định vị bằng mô tả phù hợp ở cả hai ảnh, tránh ép tồn tại bằng prompt single. Bộ ghép instance sử dụng bằng chứng vùng ảnh và cấu trúc cảnh; khi có nhiều vật giống nhau hoặc không đủ tin cậy thì không tự sửa.

Tiếp theo, bộ kiểm tra riêng cho loại claim xác định liệu có bằng chứng bác bỏ hoặc xác nhận câu đó. Với claim đổi màu, cần so vùng nội thất vật và kiểm soát ánh sáng. Với claim biến mất, cần xác định vật nguồn có nằm trong vùng quan sát được của ảnh đích và có bị khuất không. Với claim di chuyển, cần loại phần chuyển dịch toàn ảnh do camera trước khi kết luận vật tự di chuyển.

Chỉ sửa mệnh đề được hỗ trợ rõ, giữ nguyên phần khác và lưu lý do sửa. Nếu chưa đủ bằng chứng, giữ baseline hoặc trả trạng thái cần xem lại ở lớp giao diện phân tích; không tự biến “không định vị được” thành “vật không tồn tại”. Tùy chọn tạo nhiều caption để chọn chỉ có ích nếu bộ kiểm chứng đủ tốt; nhiều ứng viên không tự giải quyết vấn đề bằng chứng ảnh.

### 24.2 Thí nghiệm nhỏ nên chạy trước

Nên bắt đầu với một loại claim như đổi màu bị gọi nhầm là biến mất, nhưng phải có đủ trường hợp đúng, sai và mơ hồ ở scene mới. Bộ dữ liệu cần gồm vật đổi màu, vật thật sự mất, vật chỉ bị khuất, vật ra ngoài khung, nhiều vật cùng loại và không có vật mục tiêu. Tập phát triển, validation và kiểm tra cuối phải tách theo scene, không chỉ theo tên ảnh.

Giữ ít nhất ba nhánh: baseline không sửa, viết lại bằng prompt nhưng không thêm bằng chứng, và sửa tối thiểu có kiểm chứng. Chấm caption tổng thể cùng số lỗi sửa đúng, số lỗi mới tạo, số thay đổi thật bị bỏ sót và coverage. Phần sửa phải được người rà độc lập xác nhận. Có quyền không kết luận, nhưng coverage quá thấp phải được ghi là hạn chế thay vì gọi là độ an toàn đã được chứng minh.

Chỉ mở rộng nếu nhánh sửa có lợi trên validation mới mà không làm giảm chất lượng ở một miền. Không dùng reference caption ở inference. Không dùng một LLM tự chấm không có đối chiếu ảnh làm bằng chứng duy nhất cho một claim đã được sửa đúng.

### 24.3 Nếu tiếp tục train

Cần tăng đa dạng dữ liệu và giữ các cặp có thay đổi thật, tránh chỉ bổ sung nhiều câu generic không đổi. Với cặp positive được augment, chỉ giữ caption mục tiêu nếu phần chứa thay đổi còn quan sát được; crop làm mất vật thì nhãn cũ có thể không còn đúng. Có thể nghiên cứu consistency ở đặc trưng hoặc mục tiêu giữ hành vi trên ảnh sạch, nhưng các lựa chọn đó chưa được thử trong hồ sơ này và cần đối chứng riêng.

Một vòng train mới cần ngân sách cho chuẩn bị dữ liệu, chạy nhánh đối chứng, đánh giá validation và xác nhận, không chỉ đủ tiền cho vài update. Không gộp những đề xuất chưa chạy vào thành tích đã đạt.

## 25 Cách trình bày kết quả trong báo cáo học thuật

Tên phù hợp là nghiên cứu tái lập M3Diff và khảo sát các hướng giảm lỗi mô tả dưới biến đổi hình học. Có thể trình bày các can thiệp là những phương án cải tiến đã đề xuất và kiểm nghiệm, với kết luận riêng cho từng phương án. Không gọi toàn bộ checkpoint mới là model cải tiến thành công nếu thước đo chính giảm.

Cách phát biểu có thể sử dụng: “Quy trình tái lập đã hoàn tất trên hai tập test OmniDiff. Hậu xử lý câu lặp nâng BLEU 4 trên caption baseline. Fine tune bổ sung cặp không đổi làm giảm một số lỗi bịa vật trong diagnostic nhưng chưa cải thiện tổng lỗi, đồng thời giảm chất lượng caption trên benchmark đầy đủ. Kết quả cho thấy cần kiểm chứng sự thay đổi giữa các vật được ghép tương ứng, thay vì chỉ thay đổi lời sinh hoặc dùng box như bằng chứng đủ.”

Không nên viết “đã giải quyết xoay góc và zoom”, “LocateAnything giúp caption tốt hơn” hay “đã tăng accuracy của M3Diff” nếu không nêu phạm vi, thước đo và đánh đổi. Trong các phép thử, chỉ số đếm fact và lỗi theo cặp cũng không phải một accuracy chuẩn duy nhất của bài toán.

## 26 Giới hạn tổng thể

Các tập nhỏ dùng chung ảnh, cảnh hoặc nguồn caption qua nhiều vòng phát triển. Việc lưu protocol trước một lượt inference giúp minh bạch trong lượt đó nhưng không biến cả chuỗi nghiên cứu thích ứng thành một kiểm định độc lập đăng ký trước. Full benchmark cũng đã được xem trong quá trình phát triển và không còn là một test mù hoàn toàn cho mọi quyết định tương lai.

Chỉ có một seed train ở nhiều nhánh, số bước ít, dữ liệu bổ sung nhỏ và người rà nhãn là trợ lý. Tách hash RGB chỉ ngăn trùng chính xác; scene, bố cục và vật có thể vẫn quen. Các phép hình học 2D chưa bao phủ góc nhìn 3D, che khuất mới hoặc thay đổi camera lớn. Các kết quả đọc ảnh cần được xác nhận bằng con người nếu dùng cho kết luận nghiên cứu chính thức.

Họ GPU, precision, merge và template có thể làm caption thay đổi. Những phép so cần suy nguyên nhân mạnh nên chạy ghép cặp trên cùng môi trường. Giới hạn này không có nghĩa bỏ qua các điểm giảm đã đo; nó xác định mức chắc của diễn giải vì sao chúng giảm.

Không có bằng chứng để suy kết quả một miền luôn áp dụng sang miền còn lại. Các nhánh có CIDEr Real tăng và Render giảm cho thấy cần đánh giá theo miền, không chỉ công bố trung bình hoặc chọn miền thuận lợi.

## 27 Hướng dẫn đọc và tái sử dụng sản phẩm

Để xem baseline đã dựng, mở notebook m3diff baseline full và các file trong baseline_results. Để xem so sánh full gần nhất, dùng summary_x100 trong mixed_full_benchmark cùng completion audit và full run validated. Để xem LocateAnything và verifier, bắt đầu từ các báo cáo grounded_caption_pilot và validation của m3diff_caption_verifier, sau đó đọc comparison và quyết định từng ca.

Để chạy hai ảnh trên máy GPU khác, giải nén gói portable, cài đúng môi trường theo README, tải base đúng revision và sửa đường dẫn ảnh trong notebook. Mặc định chạy base. Chọn adapter thử nghiệm bằng USE_ADAPTER nếu cần tái hiện nhánh mixed; đây không phải khuyến nghị dùng bản này trong sản phẩm.

Các mã train và caption được lưu theo từng nhánh trên workspace hoặc Modal Volume. Gói portable chỉ phục vụ inference với adapter đã học, không tự bao gồm toàn bộ ảnh train hoặc hàng chục GB checkpoint nền. Các app nghiên cứu đã được kiểm tra dừng sau lượt chạy cuối; không có endpoint hoặc lịch GPU thường trực được tạo để tiếp tục tiêu credit.

## 28 Kết luận

Phần dựng lại model từ checkpoint và đánh giá full test đã hoàn thành. Phần cải thiện có một kết quả giữ lại là lọc lặp đầu ra, một nhánh đặc biệt rõ điều kiện là nhận ảnh RGB giống hệt, và nhiều kết quả nghiên cứu có tín hiệu hẹp nhưng chưa đạt mục tiêu toàn hệ thống. Checkpoint mixed không nên thay baseline vì vừa không giảm tổng lỗi hình học trong confirmation vừa giảm điểm caption ở full test.

LocateAnything vẫn có vai trò hợp lý trong một hệ thống kiểm chứng theo vật, nhưng cần lớp ghép instance và xác minh loại thay đổi. Những thử nghiệm đã có cho thấy thêm box rồi viết lại caption không tự bảo đảm cải thiện. Hướng tiếp theo có cơ sở là sửa tối thiểu các claim có bằng chứng trên một validation mới tách scene, với báo cáo coverage, lỗi sửa đúng và lỗi mới tạo.

## Phụ lục A Bảng điểm BLEU đầy đủ của full benchmark

{{FULL_BLEU}}

## Phụ lục B Bảng điểm METEOR ROUGE L CIDEr đầy đủ

{{FULL_OTHER}}

## Phụ lục C Cấu hình và kiểm tra tính toàn vẹn

{{INTEGRITY}}

Các hash dài trong phụ lục dùng để đối chiếu file và phiên bản, không phải thước đo chất lượng model. Một file weights đúng dung lượng nhưng sai CRC hoặc SHA không được coi là checkpoint đã kiểm chứng.

## Phụ lục D Nguồn thực nghiệm và tài liệu tham khảo

{{SOURCES}}
