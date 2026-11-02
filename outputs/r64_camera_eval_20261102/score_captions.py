"""Chấm câu M3Diff sinh ra trên bộ test tổng hợp bằng bộ phân loại từ khoá.

3 chỉ số cho mỗi cặp có vật thể:
  - type_ok  : câu có nhắc đúng loại thay đổi (thêm/xoá/đổi màu/dời/đổi kích thước/đổi sáng)
  - obj_ok   : câu có nhắc đúng tên vật (kể cả từ đồng nghĩa)
  - joint_ok : cả hai
Đối chứng: false_alarm = câu có nhắc một thay đổi cụ thể (thêm/xoá/màu/dời/kích thước/sáng).

Chế độ --validate: đọc file đã được nhóm gán nhãn tay -> Precision/Recall/F1 của bộ phân loại từ khoá.
"""
import argparse, json, os, re, sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from synth_common import TYPES, CONTROLS, OBJECT_TYPES, TYPE_VI, load_manifest, wilson  # noqa: E402

COLORS = r"(red|orange|yellow|green|blue|purple|violet|pink|brown|black|white|gr[ae]y|cyan|magenta|teal|beige|golden|silver|maroon|navy|turquoise)"
PAT = {
    "add": r"\b(appear(s|ed|ing)?|added|adds?|adding|newly|a new|an new|introduc(ed|es)|emerg(ed|es)|now (present|visible|there|appears?|sits?|stands?)|there (is|are) now|has been placed|have been placed|been put)\b",
    "remove": r"\b(disappear(s|ed|ing)?|removed|remov(es|ing)|missing|no longer|gone|absent|taken away|vanish(ed|es)?|(is|are) not (present|visible)|been taken)\b",
    "color": r"\b(colou?r(s|ed)?|hue|tint)\b|\b(turned|became|become|becomes|now|changed to|painted)\s+(a\s+|an\s+)?(light\s+|dark\s+|bright\s+)?" + COLORS + r"\b|\bfrom\s+(a\s+)?(light\s+|dark\s+)?" + COLORS + r"\b[^.]{0,40}?\bto\s+(a\s+)?(light\s+|dark\s+)?" + COLORS + r"\b",
    "move": r"\b(mov(ed|es|ing)|shift(ed|s|ing)?|relocat(ed|es|ing)|reposition(ed|s)?|different (position|location|place|spot)|(position|location) (has |have )?changed|changed (its |their )?(position|location)|slid|displaced|moved to)\b",
    "size": r"\b(larger|bigger|smaller|enlarged|shrunk|shrank|shrink(s|ing)?|grown|grew|expanded|increased in size|decreased in size|reduced in size|size|scaled)\b",
    "light": r"\b(brighter|darker|dimmer|dimmed|brightness|lighting|illuminat\w*|exposure|lighter|light (level|intensity|condition)s?|more light|less light)\b",
}
VIEW = r"\b(camera|viewpoint|perspective|angle|zoom(ed|s|ing)?|vantage|field of view)\b"
NOCHANGE = r"\b(no (visible |noticeable |significant |apparent |obvious )?(changes?|differences?|modifications?|alterations?)|(are|look|appear|remain) (identical|the same|exactly the same)|nothing (has )?changed|identical)\b"
SYN = {
    "bottle": ["bottle"], "cup": ["cup", "mug", "glass"], "bowl": ["bowl", "dish"], "vase": ["vase"],
    "chair": ["chair", "seat", "stool"], "potted plant": ["plant", "flowerpot", "potted", "flower", "pot"],
    "teddy bear": ["teddy", "bear", "stuffed", "plush", "toy"], "backpack": ["backpack", "bag", "rucksack", "knapsack"],
    "umbrella": ["umbrella", "parasol"], "suitcase": ["suitcase", "luggage", "bag", "case", "trolley"],
    "laptop": ["laptop", "computer", "notebook"], "book": ["book", "notebook"], "clock": ["clock"],
    "dog": ["dog", "puppy"], "cat": ["cat", "kitten"], "bicycle": ["bicycle", "bike"],
    "car": ["car", "vehicle", "automobile", "sedan", "suv"], "apple": ["apple", "fruit"],
    "banana": ["banana", "fruit"], "handbag": ["handbag", "bag", "purse"],
}
RX = {k: re.compile(v, re.I) for k, v in PAT.items()}
RX_VIEW, RX_NO = re.compile(VIEW, re.I), re.compile(NOCHANGE, re.I)
TRUE_TYPE = {t: t for t in TYPES}


def classify(caption):
    sents = re.split(r"(?<=[.!?;])\s+", caption)
    lab = {k: bool(r.search(caption)) for k, r in RX.items()}
    # 'shifted/moved' trong câu nói về máy ảnh là đổi góc nhìn, không phải dời vật
    lab["move"] = any(RX["move"].search(s) and not RX_VIEW.search(s) for s in sents)
    return lab | {
        "view": bool(RX_VIEW.search(caption)), "nochange": bool(RX_NO.search(caption))}


def mentions_object(caption, category):
    if not isinstance(category, str):
        return False
    words = SYN.get(category, [category])
    return any(re.search(r"\b" + re.escape(w) + r"(s|es)?\b", caption, re.I) for w in words)


def parse():
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True, help="thư mục bộ tổng hợp (có manifest.jsonl)")
    p.add_argument("--answers", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--n-manual", type=int, default=20, help="số câu mỗi loại đưa ra để gán nhãn tay")
    p.add_argument("--validate", default=None, help="file CSV đã gán nhãn tay -> P/R/F1")
    return p.parse_args()


def score(a):
    man = pd.DataFrame(load_manifest(a.root))
    ans = {}
    for l in open(a.answers):
        if l.strip():
            r = json.loads(l)
            ans[r["id"]] = r["caption"]
    man["caption"] = man["pair_id"].map(ans)
    miss = man["caption"].isna().sum()
    if miss:
        print(f"!! Thiếu câu trả lời cho {miss} cặp — chỉ chấm các cặp đã có")
    df = man.dropna(subset=["caption"]).copy()
    lab = pd.DataFrame([classify(c) for c in df["caption"]], index=df.index)
    df = pd.concat([df, lab.add_prefix("m_")], axis=1)
    df["n_words"] = df["caption"].str.split().map(len)
    df["type_ok"] = [row[f"m_{row['cond']}"] if row["cond"] in TYPES else np.nan for _, row in df.iterrows()]
    df["obj_ok"] = [mentions_object(row["caption"], row["category"]) if row["cond"] in OBJECT_TYPES else np.nan
                    for _, row in df.iterrows()]
    df["joint_ok"] = [(row["type_ok"] and row["obj_ok"]) if row["cond"] in OBJECT_TYPES else np.nan
                      for _, row in df.iterrows()]
    df["false_alarm"] = [any(row[f"m_{t}"] for t in TYPES) if row["cond"] in CONTROLS else np.nan
                         for _, row in df.iterrows()]
    os.makedirs(a.out, exist_ok=True)
    keep = [c for c in df.columns if not c.startswith("_")]
    df[keep].to_csv(os.path.join(a.out, "per_pair.csv"), index=False)

    # ---- bảng theo loại × mức ----
    rows = []
    for (cond, lvl), g in df[df["cond"].isin(TYPES)].groupby(["cond", "level"]):
        r = {"cond": cond, "level": lvl, "level_value": g["level_value"].iloc[0], "n": len(g)}
        for m in ["type_ok", "obj_ok", "joint_ok"]:
            v = g[m].dropna()
            if len(v):
                p, lo, hi = wilson(int(v.sum()), len(v))
                r[m] = p; r[m + "_lo"] = lo; r[m + "_hi"] = hi
        rows.append(r)
    summ = pd.DataFrame(rows)
    order = {t: i for i, t in enumerate(TYPES)}
    summ = summ.sort_values(["cond", "level"], key=lambda s: s.map(order) if s.name == "cond" else s)
    summ.to_csv(os.path.join(a.out, "summary_by_level.csv"), index=False)

    print("\n== Tỉ lệ đúng theo loại × mức (%, khoảng tin cậy 95% Wilson) ==")
    print(f"{'Loại':<16}{'Mức':>4}{'Giá trị':>9}{'n':>4}   {'Đúng loại':<17}{'Đúng vật':<17}{'Đúng cả hai':<17}")
    fmt = lambda r, m: (f"{r[m]*100:5.1f} [{r[m+'_lo']*100:3.0f}–{r[m+'_hi']*100:3.0f}]"
                        if m in r and pd.notna(r.get(m)) else "   —")
    for _, r in summ.iterrows():
        print(f"{TYPE_VI[r['cond']]:<16}{r['level']:>4}{r['level_value']:>9}{r['n']:>4}   "
              f"{fmt(r,'type_ok'):<17}{fmt(r,'obj_ok'):<17}{fmt(r,'joint_ok'):<17}")

    print("\n== Tổng theo loại (gộp 3 mức) ==")
    for t in TYPES:
        g = df[df["cond"] == t]
        if len(g):
            s = f"{TYPE_VI[t]:<16} n={len(g):<4} đúng loại {g['type_ok'].mean()*100:5.1f}%"
            if t in OBJECT_TYPES:
                s += f" | đúng vật {g['obj_ok'].mean()*100:5.1f}% | cả hai {g['joint_ok'].mean()*100:5.1f}%"
            print(s)

    print("\n== Đối chứng (không có thay đổi ngữ nghĩa) ==")
    for t in CONTROLS:
        g = df[df["cond"] == t]
        if len(g):
            p, lo, hi = wilson(int(g["false_alarm"].sum()), len(g))
            print(f"{TYPE_VI[t]:<24} n={len(g):<4} báo thay đổi giả: {p*100:5.1f}% [{lo*100:.0f}–{hi*100:.0f}] | "
                  f"nói 'không đổi': {g['m_nochange'].mean()*100:5.1f}% | nhắc góc máy: {g['m_view'].mean()*100:5.1f}%")

    # ---- ma trận: loại thật -> các loại được nhắc tới ----
    cols = TYPES + ["view", "nochange"]
    mat = df.groupby("cond")[[f"m_{c}" for c in cols]].mean() * 100
    mat.columns = cols
    mat = mat.reindex([t for t in TYPES + CONTROLS if t in mat.index])
    mat.to_csv(os.path.join(a.out, "mention_matrix.csv"))
    print("\n== Ma trận nhắc tới (% câu của mỗi loại thật có nhắc tới từng loại) ==")
    print(mat.round(0).astype(int).to_string())

    plots(df, summ, mat, a.out)
    export_manual(df, a)
    return df


def plots(df, summ, mat, out):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    ink, muted, grid = "#0b0b0b", "#52525b", "#e4e4e7"
    pal = ["#2a78d6", "#1f9d74", "#d97706", "#c2415d", "#7c5cd6", "#4a5568"]
    xlabels = {"add": ["1%", "4%", "10%"], "remove": ["1%", "4%", "10%"], "color": ["30°", "60°", "120°"],
               "move": ["10%", "25%", "50%"], "size": ["×0.6", "×1.5", "×2"], "light": ["γ1.25", "γ1.6", "γ2.2"]}
    fig, axes = plt.subplots(1, 6, figsize=(22, 4.2), sharey=True, facecolor="#fcfcfb")
    for ax, t, c in zip(axes, TYPES, pal):
        g = summ[summ["cond"] == t]
        if not len(g):
            ax.axis("off"); continue
        x = np.arange(len(g))
        ax.plot(x, g["type_ok"] * 100, "-o", color=c, lw=2, label="Đúng loại")
        ax.fill_between(x, g["type_ok_lo"] * 100, g["type_ok_hi"] * 100, color=c, alpha=0.12, lw=0)
        if t in OBJECT_TYPES:
            ax.plot(x, g["joint_ok"] * 100, "--s", color=c, lw=1.5, alpha=0.7, label="Đúng loại + đúng vật")
        ax.set_xticks(x); ax.set_xticklabels(xlabels[t][:len(g)], color=muted)
        ax.set_title(TYPE_VI[t], loc="left", fontsize=11, color=ink)
        ax.set_ylim(0, 100); ax.grid(axis="y", color=grid, lw=0.8)
        for s in ["top", "right"]:
            ax.spines[s].set_visible(False)
        ax.tick_params(colors=muted)
        ax.legend(frameon=False, fontsize=8, loc="lower right")
    axes[0].set_ylabel("% cặp", color=muted)
    fig.suptitle("Tỉ lệ M³Diff mô tả đúng theo mức độ thay đổi (vùng mờ: khoảng tin cậy 95%)",
                 x=0.01, ha="left", fontsize=12, color=ink)
    fig.tight_layout(); fig.savefig(os.path.join(out, "detection_by_level.png"), dpi=120, facecolor="#fcfcfb")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5), facecolor="#fcfcfb")
    im = ax.imshow(mat.values, cmap="Blues", vmin=0, vmax=100, aspect="auto")
    ax.set_xticks(range(mat.shape[1]))
    ax.set_xticklabels(["thêm", "xoá", "màu", "dời", "kích thước", "sáng", "góc máy", "'không đổi'"],
                       rotation=30, ha="right", color=muted)
    ax.set_yticks(range(mat.shape[0])); ax.set_yticklabels([TYPE_VI[t] for t in mat.index], color=muted)
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            v = mat.values[i, j]
            ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=9, color="white" if v > 55 else ink)
    ax.set_xlabel("Câu model sinh ra có nhắc tới", color=muted); ax.set_ylabel("Loại thay đổi thật", color=muted)
    ax.set_title("Ma trận nhắc tới (%)", loc="left", color=ink)
    fig.colorbar(im, ax=ax, fraction=0.03)
    fig.tight_layout(); fig.savefig(os.path.join(out, "mention_matrix.png"), dpi=120, facecolor="#fcfcfb")
    plt.close(fig)


def export_manual(df, a):
    """Xuất ~20 câu/loại để nhóm gán nhãn tay. KHÔNG kèm nhãn tự động (tránh thiên lệch)."""
    rng = np.random.default_rng(7)
    parts = []
    for t in TYPES:
        g = df[df["cond"] == t]
        if len(g):
            parts.append(g.iloc[rng.permutation(len(g))[:a.n_manual]])
    if not parts:
        return
    s = pd.concat(parts)
    s = s.iloc[rng.permutation(len(s))]                       # xáo để người gán không biết loại thật
    out = s[["pair_id", "category", "caption"]].copy()
    for c in ["add", "remove", "color", "move", "size", "light", "object"]:
        out["tay_" + c] = ""
    path = os.path.join(a.out, "manual_check.csv")
    out.to_csv(path, index=False, encoding="utf-8-sig")
    print(f"\nĐã xuất {len(out)} câu để gán nhãn tay: {path}")


def validate(a):
    man = pd.read_csv(a.validate, encoding="utf-8-sig")
    auto = pd.read_csv(os.path.join(a.out, "per_pair.csv")).set_index("pair_id")
    rows = []
    for c in ["add", "remove", "color", "move", "size", "light", "object"]:
        col = "tay_" + c
        v = pd.to_numeric(man[col], errors="coerce")
        m = man[v.isin([0, 1])]
        if c == "object":
            m = m[m["category"].map(lambda x: isinstance(x, str))]     # loại 'đổi sáng' không có vật
        y = pd.to_numeric(m[col]).astype(int).values
        if c == "object":
            yhat = np.array([mentions_object(r["caption"], r["category"]) for _, r in m.iterrows()], int)
        else:
            yhat = auto.loc[m["pair_id"], f"m_{c}"].astype(int).values
        tp, fp, fn = int(((y == 1) & (yhat == 1)).sum()), int(((y == 0) & (yhat == 1)).sum()), int(((y == 1) & (yhat == 0)).sum())
        prec = tp / (tp + fp) if tp + fp else float("nan")
        rec = tp / (tp + fn) if tp + fn else float("nan")
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else float("nan")
        rows.append({"nhãn": c, "n": len(m), "dương (tay)": int(y.sum()), "precision": prec, "recall": rec, "f1": f1,
                     "accuracy": float((y == yhat).mean()) if len(m) else float("nan")})
    r = pd.DataFrame(rows)
    r.to_csv(os.path.join(a.out, "classifier_validation.csv"), index=False)
    print("== Độ chính xác của bộ phân loại từ khoá so với nhãn tay ==")
    print(r.round(3).to_string(index=False))


if __name__ == "__main__":
    args = parse()
    validate(args) if args.validate else score(args)
