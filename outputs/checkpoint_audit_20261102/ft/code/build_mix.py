"""Ghép dữ liệu fine-tune: cặp tổng hợp + một phần dữ liệu OmniDiff train gốc (để model không quên cách viết câu dài)."""
import argparse, json, os, random

p = argparse.ArgumentParser()
p.add_argument("--synth", required=True, help="train.json của dữ liệu tổng hợp")
p.add_argument("--orig", required=True, help="training_m3diff.json gốc")
p.add_argument("--image-folder", required=True, help="gốc chung của mọi đường dẫn ảnh")
p.add_argument("--n-replay", type=int, default=2700)
p.add_argument("--out", required=True)
p.add_argument("--seed", type=int, default=0)
a = p.parse_args()
rnd = random.Random(a.seed)

syn = json.load(open(a.synth))
orig = json.load(open(a.orig))
omni = [r for r in orig if isinstance(r.get("image"), list) and r["image"][0].startswith("OmniDiff/")]
del orig
ok = [r for r in omni if all(os.path.exists(os.path.join(a.image_folder, i)) for i in r["image"])]
print(f"OmniDiff trong file gốc: {len(omni)} bản ghi | đủ ảnh: {len(ok)}")
real = [r for r in ok if "/Real/" in r["image"][0]]
rend = [r for r in ok if "/Render/" in r["image"][0]]
n_real = min(len(real), round(a.n_replay * 0.55))
n_rend = min(len(rend), a.n_replay - n_real)
replay = rnd.sample(real, n_real) + rnd.sample(rend, n_rend)
for r in replay:
    for c in r["conversations"]:
        if c["from"] == "human" and "<image>" not in c["value"]:
            c["value"] = c["value"].rstrip() + "  <image><image>Difference:"
missing_syn = [r for r in syn if not all(os.path.exists(os.path.join(a.image_folder, i)) for i in r["image"])]
if missing_syn:
    raise SystemExit(f"!! {len(missing_syn)} cặp tổng hợp không thấy ảnh, ví dụ {missing_syn[0]['image']}")
mix = syn + replay
rnd.shuffle(mix)
json.dump(mix, open(a.out, "w"))
print(f"Tổng {len(mix)} mẫu = {len(syn)} tổng hợp + {n_real} OmniDiff-Real + {n_rend} OmniDiff-Render -> {a.out}")
w = [len(c["value"].split()) for r in replay for c in r["conversations"] if c["from"] == "gpt"]
w2 = [len(c["value"].split()) for r in syn for c in r["conversations"] if c["from"] == "gpt"]
print(f"Độ dài câu trả lời: OmniDiff trung vị {sorted(w)[len(w)//2]} từ | tổng hợp trung vị {sorted(w2)[len(w2)//2]} từ")
