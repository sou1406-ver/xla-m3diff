"""So model gốc và model fine-tune trên bộ test chuyển động camera."""
import argparse, json, os, sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ft_common import CAM, camera_dir_ok, mcnemar  # noqa: E402

p = argparse.ArgumentParser()
p.add_argument("--root", required=True)
p.add_argument("--base", required=True)
p.add_argument("--ft", required=True)
p.add_argument("--synth-code", default="/mnt/m3diff/synth/code")
p.add_argument("--out", required=True)
a = p.parse_args()
sys.path.insert(0, a.synth_code)
from score_captions import classify, mentions_object  # noqa: E402

man = pd.DataFrame([json.loads(l) for l in open(os.path.join(a.root, "manifest.jsonl")) if l.strip()])
def load(fp):
    return {json.loads(l)["id"]: json.loads(l)["caption"] for l in open(fp) if l.strip()}
caps = {"base": load(a.base), "ft": load(a.ft)}
rows = []
for _, r in man.iterrows():
    for m, c in caps.items():
        cap = c.get(r["pair_id"])
        if cap is None:
            continue
        lab = classify(cap)
        d = {"pair_id": r["pair_id"], "cond": r["cond"], "level": r["level"], "model": m, "caption": cap,
             "cam_ok": bool(CAM.search(cap)), "dir_ok": camera_dir_ok(cap, r["cond"], r.get("camera_dir")),
             "false_obj": any(lab[k] for k in ["add", "remove", "color", "move", "size"])}
        if r["cond"] in ("cam_add", "cam_remove"):
            t = "add" if r["cond"] == "cam_add" else "remove"
            d["obj_type_ok"] = lab[t]
            d["obj_name_ok"] = mentions_object(cap, r.get("category"))
            d["false_obj"] = None
        rows.append(d)
df = pd.DataFrame(rows)
df.to_csv(a.out, index=False)

def pct(s):
    s = s.dropna()
    return f"{s.mean()*100:5.1f}" if len(s) else "   —"

print("== Chỉ camera chuyển động (không có vật nào đổi) ==")
print(f"{'Điều kiện':<11}{'Mức':>4}{'n':>4} | {'nhắc camera':>12} {'đúng hướng':>11} {'bịa đổi vật':>12} | (gốc → fine-tune)")
for (cond, lvl), g in df[~df.cond.isin(["cam_add", "cam_remove"])].groupby(["cond", "level"]):
    b, f = g[g.model == "base"], g[g.model == "ft"]
    print(f"{cond:<11}{lvl:>4}{len(b):>4} | {pct(b.cam_ok)} → {pct(f.cam_ok)}  {pct(b.dir_ok)} → {pct(f.dir_ok)}"
          f"  {pct(b.false_obj)} → {pct(f.false_obj)}")
cam_only = df[~df.cond.isin(["cam_add", "cam_remove"])]
b = cam_only[cam_only.model == "base"].set_index("pair_id")
f = cam_only[cam_only.model == "ft"].set_index("pair_id")
ids = b.index.intersection(f.index)
for col, vi in [("cam_ok", "nhắc camera"), ("dir_ok", "đúng hướng"), ("false_obj", "bịa đổi vật")]:
    pv, n01, n10 = mcnemar(b.loc[ids, col].astype(bool).tolist(), f.loc[ids, col].astype(bool).tolist())
    print(f"Tổng {len(ids)} cặp — {vi}: {b.loc[ids, col].mean()*100:.1f}% → {f.loc[ids, col].mean()*100:.1f}%"
          f"  (chỉ fine-tune đúng {n01}, chỉ gốc đúng {n10}, McNemar p = {pv:.2g})")

print("\n== Camera chuyển động + thêm/xoá vật ==")
for cond, g in df[df.cond.isin(["cam_add", "cam_remove"])].groupby("cond"):
    b, f = g[g.model == "base"], g[g.model == "ft"]
    print(f"{cond:<11} n={len(b):<3} đúng loại thay đổi vật {pct(b.obj_type_ok)} → {pct(f.obj_type_ok)} | "
          f"đúng tên vật {pct(b.obj_name_ok)} → {pct(f.obj_name_ok)} | nhắc camera {pct(b.cam_ok)} → {pct(f.cam_ok)}")
print(f"\nĐã lưu: {a.out}")
