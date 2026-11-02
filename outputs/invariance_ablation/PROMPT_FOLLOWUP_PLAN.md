# Kiểm tra mất cân bằng câu hỏi trước benchmark đầy đủ

Phát hiện từ code/data, trước khi đọc caption/giải khóa lượt confirmation80:192 positive dùng10 template,64 negative chỉ dùng một template. Với câu hỏi đó,64/83 record là negative, trong khi9 template còn lại không có negative. Đây là nguy cơ học shortcut ngôn ngữ, chưa phải bằng chứng model đã dùng shortcut.

Một lượt đối chứng mới: giữ cùng256 ảnh/target/thứ tự, seed42, LoRA r16 alpha32, LR2e-5,2epoch64update; chỉ phân phối64 negative trên10 template theo tỷ lệ192 positive (Hamilton rounding). Mỗi nhóm16 negative identity/zoom-in/roll/zoom-out chứa cả10 template. Vision/projector/MDP vẫn đóng băng. Kiểm tra khởi tạo và hai thứ tự epoch với nhánh mixed trước.

Chạy lại baseline và balanced trên72 cặp cố định cùng GPU; chấm ẩn tên và bảo toàn fact cũ/mới theo từng miền như trước. Không điều chỉnh LR hoặc nhãn từ confirmation80.

Nếu đủ credit, probe40 câu: bốn case cố định (clothesline zoom-in; computer_desk roll8; bunk_bedroom zoom-out; bicycle_alley identity) nhân10 template. So sánh baseline, mixed cũ và balanced. Mỗi template có đúng cùng4 cặp ảnh. Báo physical FP lẫn lỗi ánh sáng và camera sai; không gọi đây là scene mới.

Chọn cho full benchmark trước xem full-test metric: balanced được ưu tiên khi qua gate factual72, giảm FP so với baseline, và lỗi joint trên40 prompt probe không cao hơn mixed cũ; nếu không giữ mixed cũ là candidate khảo sát. Nếu cả hai không bảo toàn fact thì baseline vẫn là bản chính. Không chọn bằng cách thử nhiều candidate trên full-test rồi lấy điểm cao nhất. Sửa kế hoạch full trước inference, giữ lịch sử lựa chọn này.

Lượt benchmark đầy đủ vẫn giữ nguyên từng câu hỏi gốc (10 cách hỏi); không thay bằng câu diagnostic cố định. Probe2 cặp có cùng prompt với baseline cũ có1 caption trùng nguyên văn; cặp còn lại chỉ khác mô tả quần blue jeans/dark pants. Môi trường, runner và thứ tự ảnh đã đối chiếu. Không tuyên bố tái lập bit-for-bit toàn bộ chỉ từ probe nhỏ.
