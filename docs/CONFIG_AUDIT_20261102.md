# Kiểm tra Volume không dùng GPU, 02/11/2026

Đọc trực tiếp Volume `m3diff` bằng SDK, không khởi chạy compute:

- `baseline_cache/M3Diff/generation_config.json` có **repetition_penalty=1.05**, do_sample=true, temperature=.7, top_k20, top_p.8. Runner baseline đã lưu gọi generate với do_sample=false, temperature0 và max_new_tokens1024, không truyền repetition_penalty; vì vậy code không chủ động reset penalty về1.00. Cần ghi effective runtime generation config trong lượt smoke kế tiếp để xác nhận loader không thay đổi nó.
- `results/OmniDiff_Real/scores.json` thực sự có CIDEr **35.53796249** và BLEU4 **14.65741786** (×100). Đây là baseline lịch sử khác với lượt dựng lại baseline33.752569 ở `outputs/baseline_results`; không được gộp hai lượt làm một. Chưa kiểm tra lại caption provenance/runner đầy đủ để giải thích chênh lệch.
- `ft/m3diff-ft-lora/adapter_config.json`: r64, alpha128, dropout.05,196 language projection targets. File adapter_model.bin646058922bytes, non_lora_trainables.bin161524428bytes; chưa tải/đọc tensor nên không kết luận phần ngoài LoRA đã cập nhật module nào chỉ từ tên file.
- trainer_state:338/338steps, epoch.99778598, num_train_epochs1, train_batch_size4. Xác nhận checkpoint này khác các adapter r16 gần đây.
- Liệt kê đệ quy `ft`: trong `ft/eval/` chỉ thấy `camtest_base.jsonl` (đã đọc:79626bytes); chưa thấy camtest_ft/synth_ft hay full predictions của adapter này ở cây `ft`. Không phải bằng chứng rằng chúng không tồn tại ở bất kỳ folder/tài khoản nào khác.

Kết luận: giả thuyết penalty1.05 có cơ sở từ config thật. **Chưa chứng minh penalty giải thích toàn bộ chênh lệch CIDEr**, do prompt, token cap, precision, loader và protocol khác nhau. Không kết luận B-SCST kém hơn base chuẩn chỉ bằng35.54vs34.99 từ hai protocol.

Ưu tiên kế tiếp: xác nhận effective config và provenance baseline cũ; kiểm tra có adapter A/B đúng phiên bản; đo throughput trên đoạn ngắn trước khi full. G/A/B cần cùng penalty1.05, prompt, max token và precision. Nếu dùng cấu hình chính thức1024token cho cả ba thì không cần thêm một lượt G1024 trùng. Nếu matched test dùng256 thì G1024 là mốc phụ khác protocol.

Checkpoint `/ft` đáng đánh giá riêng theo gate camera-only hallucination và camera+object fact retention trước full. Các gate thất bại của r16 không được gán cho r64 chưa đánh giá này.

Không khởi chạy50cặp hay full trong bước audit này. Cập nhật này bổ sung HANDOFF: nay đã xác nhận có một checkpoint r64 lịch sử cần đánh giá; nó không phải hai checkpoint ngày02/11.
