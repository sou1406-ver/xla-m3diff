# M³Diff — Kết quả tái lập baseline

Repo commit: `4e346e52185620ec6fa17235d93b0c26a9d47a71`
GPU: NVIDIA A10, 23028 MiB
Thiết lập: BF16, không lượng tử hóa, temperature=0, beam=1, max_new_tokens=1024.
Khởi tạo từ checkpoint M³Diff công bố; không fine-tune hoặc căn chỉnh ảnh.
Scorer: pycocoevalcap BLEU, METEOR, ROUGE-L và CIDEr; không chạy SPICE.

| Tập | Số cặp | BLEU-4 | METEOR | ROUGE-L | CIDEr |
|---|---:|---:|---:|---:|---:|
| Real | 803 | 14.27 | 19.49 | 32.61 | 33.75 |
| Render | 767 | 16.92 | 20.14 | 35.75 | 30.49 |

Các điểm trong bảng được nhân 100. Không tự động khẳng định bằng kết quả paper.
run_config.json ghi revision weights/dataset, hash prompt/reference/runner và cấu hình suy luận.
environment_freeze.txt ghi thư viện; logs/ lưu log chạy.

## Ví dụ caption

### Real: real_test_pair_000001
The green storage box on top of the wooden cabinet has disappeared.

### Real: real_test_pair_000002
The scene has become darker.

### Real: real_test_pair_000003
The blue toy seat with a patterned plush toy on top has moved to the left side of the scene, now positioned in front of the blue toy car.

### Real: real_test_pair_000004
The blue toy train on the right side of the scene has changed from facing left to facing right. The blue and yellow toy on the entertainment stand in the back-right of the scene has disappeared.

### Real: real_test_pair_000005
A new train toy has appeared in front of the toy car on the left side of the scene.

### Render: render_test_pair_000001
The man in a brown coat, red backpack, and blue pants has turned his body to the left, facing the house on the right side of the picture.

### Render: render_test_pair_000002
The man wearing a green jacket, blue pants, and a red hat, who was on the left side of the screen, is no longer visible. The word "vila" in large blue letters has appeared on the road near the lower-left corner of the scene, positioned close to the sidewalk and in front of the colorful houses.

### Render: render_test_pair_000003
The man wearing a green jacket, blue pants, and a red hat, who was previously in the middle of the road facing the camera with his left hand in his pocket and his right hand holding a book, is no longer visible. The word "vila" in large white letters has appeared on the left side of the road, near the curb and close to the sidewalk, just in front of the red house on the left.

### Render: render_test_pair_000004
The man wearing a green jacket, blue pants, and a red hat who was in the middle of the road on the left side of the screen is no longer visible. The bicycle that was leaning against the right fence has moved to the center of the road.

### Render: render_test_pair_000005
The man wearing a hat, a yellow coat, and blue pants, who was previously facing the camera with his back to the screen, is no longer visible. The word "vila" in large blue letters has appeared on the left side of the road, near the curb and close to the sidewalk, just in front of the man who was standing there.
