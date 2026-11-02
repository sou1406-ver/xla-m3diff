"""Lưới kiểm tra dữ liệu fine-tune: mỗi hàng ảnh A | ảnh B, kèm câu mô tả (hoặc câu model sinh ra)."""
import argparse, json, os, textwrap
os.environ["MPLBACKEND"] = "Agg"
import cv2
import numpy as np
import matplotlib.pyplot as plt

p = argparse.ArgumentParser()
p.add_argument("--root", required=True)
p.add_argument("--out", required=True)
p.add_argument("--n", type=int, default=12)
p.add_argument("--conds", nargs="*", default=None)
p.add_argument("--answers", nargs="*", default=[], help="(tuỳ chọn) nhãn=đường_dẫn.jsonl để in câu model sinh ra")
a = p.parse_args()
recs = [json.loads(l) for l in open(os.path.join(a.root, "manifest.jsonl")) if l.strip()]
if a.conds:
    recs = [r for r in recs if r["cond"] in a.conds]
rng = np.random.default_rng(1)
recs = [recs[i] for i in sorted(rng.permutation(len(recs))[:a.n])]
ans = {}
for spec in a.answers:
    lab, fp = spec.split("=", 1)
    if os.path.exists(fp):
        ans[lab] = {json.loads(l)["id"]: json.loads(l)["caption"] for l in open(fp) if l.strip()}
fig, axes = plt.subplots(len(recs), 2, figsize=(13, 3.9 * len(recs)), facecolor="#fcfcfb", squeeze=False)
for (ax1, ax2), r in zip(axes, recs):
    for ax, k, t in [(ax1, "image_A", "A"), (ax2, "image_B", "B")]:
        ax.imshow(cv2.cvtColor(cv2.imread(os.path.join(a.root, r[k])), cv2.COLOR_BGR2RGB)); ax.axis("off")
    ax1.set_title(f"{r['pair_id']}", loc="left", fontsize=9)
    lines = [f"Đáp án: {r['caption']}"] + [f"{lab}: {d.get(r['pair_id'], '')}" for lab, d in ans.items()]
    ax2.set_title("\n".join(textwrap.fill(s[:300], 95) for s in lines), loc="left", fontsize=8)
fig.tight_layout()
fig.savefig(a.out, dpi=70, facecolor="#fcfcfb")
print(a.out)
