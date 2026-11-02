"""So model gốc và fine-tune trên bộ test tổng hợp của Notebook 1 (cùng 600 cặp, cùng bộ chấm)."""
import argparse, os, sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ft_common import mcnemar  # noqa: E402

p = argparse.ArgumentParser()
p.add_argument("--base", required=True, help="per_pair.csv của model gốc (Notebook 1)")
p.add_argument("--ft", required=True, help="per_pair.csv của model fine-tune")
a = p.parse_args()
b = pd.read_csv(a.base).set_index("pair_id")
f = pd.read_csv(a.ft).set_index("pair_id")
ids = b.index.intersection(f.index)
b, f = b.loc[ids], f.loc[ids]
VI = {"add": "Thêm vật", "remove": "Xoá vật", "color": "Đổi màu", "move": "Dời vật", "size": "Đổi kích thước",
      "light": "Đổi sáng", "same": "Đối chứng A == B", "jpeg": "Đối chứng JPEG"}
print(f"{'Loại':<18}{'n':>4} | {'đúng loại':^22} | {'đúng cả loại + vật':^22}")
for t in ["add", "remove", "color", "move", "size", "light"]:
    m = b["cond"] == t
    if not m.any():
        continue
    x, y = b.loc[m, "type_ok"].astype(bool), f.loc[m, "type_ok"].astype(bool)
    pv, *_ = mcnemar(x.tolist(), y.tolist())
    s = f"{VI[t]:<18}{m.sum():>4} | {x.mean()*100:5.1f} → {y.mean()*100:5.1f} (p={pv:.2g})"
    if t != "light":
        x2, y2 = b.loc[m, "joint_ok"].astype(bool), f.loc[m, "joint_ok"].astype(bool)
        pv2, *_ = mcnemar(x2.tolist(), y2.tolist())
        s += f" | {x2.mean()*100:5.1f} → {y2.mean()*100:5.1f} (p={pv2:.2g})"
    print(s)
print("\nĐối chứng — tỉ lệ bịa thay đổi (càng thấp càng tốt):")
for t in ["same", "jpeg"]:
    m = b["cond"] == t
    if m.any():
        x, y = b.loc[m, "false_alarm"].astype(bool), f.loc[m, "false_alarm"].astype(bool)
        pv, *_ = mcnemar(x.tolist(), y.tolist())
        print(f"  {VI[t]:<18} n={m.sum()} {x.mean()*100:5.1f}% → {y.mean()*100:5.1f}% (p={pv:.2g})")
print("\nTheo mức (đúng loại, gốc → fine-tune):")
for (t, l), g in b[b["cond"].isin(["move", "size", "light", "color"])].groupby(["cond", "level"]):
    print(f"  {VI[t]:<16} mức {l}: {g['type_ok'].mean()*100:5.1f} → {f.loc[g.index, 'type_ok'].mean()*100:5.1f}")
