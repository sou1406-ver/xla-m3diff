"""Sinh dữ liệu tổng hợp cho fine-tune M3Diff và bộ test chuyển động camera.

--mode train   : ảnh nền lấy từ OmniDiff TRAIN, vật thể COCO không trùng bộ test -> train.json (định dạng LLaVA,
                 có câu trả lời kiểu OmniDiff: phần chỉ vật + phần thay đổi, kèm màu và vị trí của vật).
--mode camtest : ảnh nền lấy từ OmniDiff TEST, vật thể của bộ test Notebook 1 -> questions.json + manifest.jsonl
                 (camera zoom vào/ra, xoay, lia; camera + thêm/xoá vật). Dùng để so model gốc và model fine-tune.

Dùng lại các hàm dán vật / đổi màu / gamma của make_synth.py (Notebook 1).
"""
import argparse, glob, json, math, os, sys

import cv2
import numpy as np
import pandas as pd

p0 = argparse.ArgumentParser(add_help=False)
p0.add_argument("--synth-code", default="/mnt/m3diff/synth/code")
_a0, _ = p0.parse_known_args()
sys.path.insert(0, _a0.synth_code)
from make_synth import prepare_object, paste, sample_center, hue_shift, gamma, MARGIN  # noqa: E402

OUT_LONG = 768
SRC_LONG = 1024          # ảnh nguồn to hơn ảnh ra để có chỗ cho zoom/lia/xoay

TRAIN_PLAN = {"add": 380, "remove": 380, "color": 300, "move": 360, "size": 360, "light": 150,
              "zoom": 260, "rotate": 160, "pan": 160, "cam_obj": 160, "same": 50}
CAMTEST_LEVELS = {"zoom_in": [1.12, 1.25, 1.5], "zoom_out": [1.12, 1.25, 1.5],
                  "rotate": [3, 7, 15], "pan": [0.06, 0.12, 0.22]}
CAMTEST_OBJ = {"cam_add": 30, "cam_remove": 30}


def parse():
    p = argparse.ArgumentParser(parents=[p0])
    p.add_argument("--mode", choices=["train", "camtest"], required=True)
    p.add_argument("--omnidiff-root", required=True)
    p.add_argument("--bg-globs", nargs="*", default=[], help="(train) glob ảnh nền, tương đối với omnidiff-root")
    p.add_argument("--questions", nargs="*", default=[], help="(camtest) file câu hỏi OmniDiff test để lấy ảnh nền")
    p.add_argument("--prompt-questions", nargs="+", required=True, help="file câu hỏi OmniDiff để lấy mẫu prompt")
    p.add_argument("--objects-dir", required=True)
    p.add_argument("--objects-csv", default="objects.csv")
    p.add_argument("--out", required=True)
    p.add_argument("--n-bg", type=int, default=300, help="số ảnh nền mỗi nguồn")
    p.add_argument("--scale", type=float, default=1.0, help="(train) nhân số cặp mỗi loại")
    p.add_argument("--n-per-level", type=int, default=15, help="(camtest)")
    p.add_argument("--seed", type=int, default=7001)
    p.add_argument("--rel-prefix", default="", help="tiền tố đường dẫn ảnh ghi vào json (train)")
    return p.parse_args()


# ---------------- mô tả bằng chữ ----------------
def color_name(rgb, a):
    m = a > 0.5
    if m.sum() < 10:
        return ""
    hsv = cv2.cvtColor(np.clip(rgb, 0, 255).astype(np.uint8), cv2.COLOR_BGR2HSV)[m].astype(np.float32)
    h, s, v = hsv[:, 0] * 2.0, hsv[:, 1], hsv[:, 2]
    S, V = float(np.median(s)), float(np.median(v))
    if V < 55:
        return "black"
    if S < 45:
        return "white" if V > 190 else "gray"
    w = s * v + 1e-6
    ang = math.degrees(math.atan2((w * np.sin(np.radians(h))).sum(), (w * np.cos(np.radians(h))).sum())) % 360
    if ang < 15 or ang >= 345:
        return "red"
    if ang < 40:
        return "brown" if V < 150 else "orange"
    if ang < 70:
        return "yellow"
    if ang < 160:
        return "green"
    if ang < 195:
        return "cyan"
    if ang < 255:
        return "blue"
    if ang < 290:
        return "purple"
    return "pink"


def loc_phrase(cx, cy, W, H):
    hx = "left" if cx < W / 3 else ("right" if cx > 2 * W / 3 else "center")
    vy = "upper" if cy < H / 3 else ("lower" if cy > 2 * H / 3 else "middle")
    if hx == "center" and vy == "middle":
        return "in the center of the scene"
    if hx == "center":
        return f"in the {vy} part of the scene"
    if vy == "middle":
        return f"on the {hx} side of the scene"
    return f"in the {vy} {hx} part of the scene"


def np_(c, n):
    return f"{c} {n}" if c else n


def art(word):
    return "An" if word[:1].lower() in "aeiou" else "A"


def cap_add(rng, c, n, loc):
    d = np_(c, n)
    return rng.choice([f"{art(d)} {d} has appeared {loc}.", f"{art(d)} {d} has been added {loc}.",
                       f"{art(d)} new {d} is now present {loc}."])


def cap_remove(rng, c, n, loc):
    d = np_(c, n)
    return rng.choice([f"The {d} {loc} has disappeared.", f"The {d} {loc} is no longer present.",
                       f"The {d} that was {loc} has been removed."])


def cap_color(rng, c1, c2, n, loc):
    if c1 == c2 or not c1 or not c2:
        return f"The {n} {loc} has changed to a different shade of {c1 or 'color'}."
    return rng.choice([f"The {n} {loc} has changed from {c1} to {c2}.",
                       f"The color of the {n} {loc} has changed from {c1} to {c2}.",
                       f"The {c1} {n} {loc} has turned {c2}."])


def cap_move(rng, c, n, loc1, direction):
    d = np_(c, n)
    return rng.choice([f"The {d} {loc1} has moved to the {direction}.",
                       f"The {d} that was {loc1} has been moved to the {direction}.",
                       f"The {d} {loc1} has shifted toward the {direction} side of the scene."])


def cap_size(rng, c, n, loc, up):
    d = np_(c, n)
    if up:
        return rng.choice([f"The {d} {loc} has become larger.", f"The size of the {d} {loc} has increased.",
                           f"The {d} {loc} has been enlarged."])
    return rng.choice([f"The {d} {loc} has become smaller.", f"The size of the {d} {loc} has decreased.",
                       f"The {d} {loc} has shrunk."])


def cap_light(rng, up):
    if up:
        return rng.choice(["The scene has become brighter.", "The ambient lighting has brightened.",
                           "The lighting in the scene has increased."])
    return rng.choice(["The scene has become darker.", "The ambient lighting has dimmed.",
                       "The lighting in the scene has decreased."])


def cap_camera(rng, kind, val, extra):
    small = {"zoom": val < 1.2, "rotate": val < 5, "pan": val < 0.1}.get(kind, False)
    adv = "slightly " if small else ""
    if kind == "zoom":
        io = extra
        return rng.choice([f"The shooting perspective has {adv}zoomed {io}.",
                           f"The camera has {adv}zoomed {io}" + (", making objects appear larger." if io == "in"
                                                                 else ", so more of the scene is visible.")])
    if kind == "rotate":
        return rng.choice([f"The camera has rotated {adv}{extra}.", f"The shooting angle has tilted {adv}{extra}."])
    if kind == "pan":
        return rng.choice([f"The shooting perspective has {adv}shifted to the {extra}.",
                           f"The camera has {adv}panned to the {extra}."])
    raise ValueError(kind)


# ---------------- biến đổi camera ----------------
def fit_out(img):
    return resize_to_long(img, OUT_LONG)


def resize_to_long(img, side):
    s = side / max(img.shape[:2])
    return cv2.resize(img, (max(2, round(img.shape[1] * s)), max(2, round(img.shape[0] * s))),
                      interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)


def cam_zoom(src, f, rng):
    """A = toàn khung, B = cắt giữa 1/f (zoom vào). Tâm lệch ngẫu nhiên nhẹ."""
    H, W = src.shape[:2]
    w, h = W / f, H / f
    cx = W / 2 + rng.uniform(-0.25, 0.25) * (W - w)
    cy = H / 2 + rng.uniform(-0.25, 0.25) * (H - h)
    x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    B = cv2.resize(src[y0:y0 + int(h), x0:x0 + int(w)], (W, H), interpolation=cv2.INTER_CUBIC)
    return src, B


def cam_rotate(src, deg):
    """Xoay quanh tâm và phóng vừa đủ để không lộ viền đen."""
    H, W = src.shape[:2]
    t = math.radians(abs(deg))
    k = math.cos(t) + math.sin(t) * max(W / H, H / W)
    M = cv2.getRotationMatrix2D((W / 2, H / 2), deg, k)
    return src, cv2.warpAffine(src, M, (W, H), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)


def cam_pan(src, p, right):
    """Hai cửa sổ cùng cỡ lệch nhau p*W theo chiều ngang. right=True: máy lia sang phải (nội dung trôi sang trái)."""
    H, W = src.shape[:2]
    d = int(round(p * W))
    A, B = src[:, :W - d], src[:, d:]
    return (A, B) if right else (B, A)


def camera_pair(src, kind, val, rng):
    """Trả về (A, B, mô tả hướng) — chưa resize."""
    if kind == "zoom":
        io = "in" if val >= 1 else "out"
        f = val if val >= 1 else 1 / val
        A, B = cam_zoom(src, f, rng)
        return (A, B, "in") if io == "in" else (B, A, "out")
    if kind == "rotate":
        A, B = cam_rotate(src, val)
        # góc dương = nội dung quay ngược chiều kim đồng hồ = máy xoay cùng chiều kim đồng hồ
        return A, B, ("clockwise" if val > 0 else "counterclockwise")
    if kind == "pan":
        right = val > 0
        A, B = cam_pan(src, abs(val), right)
        return A, B, ("right" if right else "left")
    raise ValueError(kind)


# ---------------- sinh 1 cặp ----------------
def place(rng, bg, pool, area, center_zone=False):
    o = pool.iloc[int(rng.integers(len(pool)))]
    H, W = bg.shape[:2]
    rgb, a = prepare_object(o["_rgba"], area * W * H)
    if center_zone:      # để vật vẫn nằm trong khung sau khi zoom/lia
        c = (float(rng.uniform(0.35, 0.65) * W), float(rng.uniform(0.45, 0.75) * H))
    else:
        c = sample_center(rng, W, H, a.shape[1], a.shape[0])
        if c is None:
            return None
    img, am = paste(bg, rgb, a, *c)
    if img is None:
        return None
    return o, rgb, a, c, img


def make_one(kind, rng, bgs, objs, objs_color, level=None):
    bi = int(rng.integers(len(bgs)))
    name, src = bgs[bi]
    bg = fit_out(src)
    H, W = bg.shape[:2]
    meta = {"bg_source": name, "cond": kind}

    if kind in ("add", "remove"):
        area = level if level is not None else float(np.exp(rng.uniform(np.log(0.008), np.log(0.12))))
        r = place(rng, bg, objs, area)
        if r is None:
            return None
        o, rgb, a, c, img = r
        cn, loc = color_name(rgb, a), loc_phrase(*c, W, H)
        meta |= {"category": o["category"], "obj_id": int(o["obj_id"]), "area": round(area, 4)}
        if kind == "add":
            return bg, img, cap_add(rng, cn, o["category"], loc), meta
        return img, bg, cap_remove(rng, cn, o["category"], loc), meta

    if kind == "color":
        r = place(rng, bg, objs_color, float(rng.uniform(0.02, 0.07)))
        if r is None:
            return None
        o, rgb, a, c, img = r
        deg = float(rng.uniform(25, 150)) * (1 if rng.integers(2) else -1)
        rgb2 = hue_shift(rgb, deg)
        B, _ = paste(bg, rgb2, a, *c)
        cap = cap_color(rng, color_name(rgb, a), color_name(rgb2, a), o["category"], loc_phrase(*c, W, H))
        meta |= {"category": o["category"], "obj_id": int(o["obj_id"]), "hue_shift": round(deg, 1)}
        return img, B, cap, meta

    if kind == "move":
        r = place(rng, bg, objs, float(rng.uniform(0.015, 0.06)))
        if r is None:
            return None
        o, rgb, a, c, img = r
        frac = float(rng.uniform(0.08, 0.5))
        for sgn in ([1, -1] if rng.integers(2) else [-1, 1]):
            B, _ = paste(bg, rgb, a, c[0] + sgn * frac * W, c[1])
            if B is not None:
                cap = cap_move(rng, color_name(rgb, a), o["category"], loc_phrase(*c, W, H),
                               "right" if sgn > 0 else "left")
                meta |= {"category": o["category"], "obj_id": int(o["obj_id"]), "shift": round(sgn * frac, 3)}
                return img, B, cap, meta
        return None

    if kind == "size":
        base = float(rng.uniform(0.015, 0.05))
        r = place(rng, bg, objs, base)
        if r is None:
            return None
        o, rgb, a, c, img = r
        s = float(rng.choice([rng.uniform(0.5, 0.8), rng.uniform(1.3, 2.2)]))
        rgb2, a2 = prepare_object(o["_rgba"], base * W * H, scale=s)
        B, _ = paste(bg, rgb2, a2, c[0], c[1] + a.shape[0] / 2 - a2.shape[0] / 2)
        if B is None:
            return None
        cap = cap_size(rng, color_name(rgb, a), o["category"], loc_phrase(*c, W, H), s > 1)
        meta |= {"category": o["category"], "obj_id": int(o["obj_id"]), "scale": round(s, 3)}
        return img, B, cap, meta

    if kind == "light":
        g = float(rng.uniform(1.2, 2.4))
        up = bool(rng.integers(2))
        meta |= {"gamma": round(1 / g if up else g, 3)}
        return bg, gamma(bg, 1 / g if up else g), cap_light(rng, up), meta

    if kind == "same":
        B = bg.copy()
        if rng.integers(2):
            ok, enc = cv2.imencode(".jpg", bg, [cv2.IMWRITE_JPEG_QUALITY, int(rng.integers(70, 95))])
            B = cv2.imdecode(enc, cv2.IMREAD_COLOR)
        return bg, B, "There is no difference between the two images.", meta

    # ---- camera (có thể kèm thêm/xoá vật) ----
    src_big = resize_to_long(src, SRC_LONG)
    obj_change = None
    if kind in ("cam_obj", "cam_add", "cam_remove"):
        obj_change = {"cam_obj": rng.choice(["add", "remove"]), "cam_add": "add", "cam_remove": "remove"}[kind]
        cam_kind = rng.choice(["zoom", "rotate", "pan"])
    else:
        cam_kind = {"zoom_in": "zoom", "zoom_out": "zoom"}.get(kind, kind)

    if level is not None:
        val = level
        if kind == "zoom_out":
            val = 1 / level
        if cam_kind == "rotate":
            val = level * (1 if rng.integers(2) else -1)
        if cam_kind == "pan":
            val = level * (1 if rng.integers(2) else -1)
    else:
        val = {"zoom": (float(rng.uniform(1.08, 1.6)) if rng.integers(2) else 1 / float(rng.uniform(1.08, 1.6))),
               "rotate": float(rng.uniform(2, 18)) * (1 if rng.integers(2) else -1),
               "pan": float(rng.uniform(0.04, 0.25)) * (1 if rng.integers(2) else -1)}[cam_kind]

    with_obj = src_big
    if obj_change:
        r = place(rng, src_big, objs, float(rng.uniform(0.02, 0.06)), center_zone=True)
        if r is None:
            return None
        o, rgb, a, c, with_obj = r
        meta |= {"category": o["category"], "obj_id": int(o["obj_id"]), "obj_change": obj_change}
    win_seed = int(rng.integers(1 << 30))       # cùng cửa sổ camera cho ảnh có vật và không có vật
    A0, B0, extra = camera_pair(src_big, cam_kind, val, np.random.default_rng(win_seed))
    if obj_change:
        Aw, Bw, _ = camera_pair(with_obj, cam_kind, val, np.random.default_rng(win_seed))
        A0, B0 = (A0, Bw) if obj_change == "add" else (Aw, B0)
    A, B = fit_out(A0), fit_out(B0)
    if A.shape != B.shape:
        B = cv2.resize(B, (A.shape[1], A.shape[0]), interpolation=cv2.INTER_AREA)
    cap = cap_camera(rng, cam_kind, abs(val) if cam_kind != "zoom" else (val if val >= 1 else 1 / val), extra)
    if obj_change:
        cn = color_name(rgb, a)
        loc = "in the center of the scene"
        sent_obj = cap_add(rng, cn, o["category"], loc) if obj_change == "add" else cap_remove(rng, cn, o["category"], loc)
        cap = f"{cap} {sent_obj}"
    meta |= {"camera": cam_kind, "camera_value": round(float(val), 4), "camera_dir": extra}
    return A, B, cap, meta


# ---------------- main ----------------
def load_objects(a):
    df = pd.read_csv(os.path.join(a.objects_dir, a.objects_csv))
    df["_rgba"] = [cv2.imread(os.path.join(a.objects_dir, f), cv2.IMREAD_UNCHANGED) for f in df["file"]]
    df = df[df["_rgba"].map(lambda x: x is not None and x.ndim == 3 and x.shape[2] == 4)].reset_index(drop=True)
    return df, df[df["mean_sat"] >= 70].reset_index(drop=True)


def load_bgs(a, rng):
    paths = []
    if a.mode == "train":
        for g in a.bg_globs:
            fs = sorted(glob.glob(os.path.join(a.omnidiff_root, g)))
            paths += [fs[i] for i in rng.permutation(len(fs))[:a.n_bg]]
    else:
        for qf in a.questions:
            uniq = sorted({q["image"][0] for q in json.load(open(qf))})
            paths += [os.path.join(a.omnidiff_root, uniq[i]) for i in rng.permutation(len(uniq))[:a.n_bg]]
    bgs = []
    for pth in paths:
        img = cv2.imread(pth, cv2.IMREAD_COLOR)
        if img is not None:
            bgs.append((os.path.relpath(pth, a.omnidiff_root), resize_to_long(img, SRC_LONG)))
    return bgs


def main():
    a = parse()
    rng0 = np.random.default_rng(a.seed)
    os.makedirs(os.path.join(a.out, "images"), exist_ok=True)
    prompts = sorted({q["conversations"][0]["value"] for qf in a.prompt_questions for q in json.load(open(qf))})
    bgs = load_bgs(a, rng0)
    objs, objs_color = load_objects(a)
    print(f"Ảnh nền: {len(bgs)} | vật thể: {len(objs)} (đủ màu: {len(objs_color)}) | prompt: {len(prompts)}", flush=True)

    plan = []
    if a.mode == "train":
        for k, n in TRAIN_PLAN.items():
            plan += [(k, None, i) for i in range(int(round(n * a.scale)))]
    else:
        for k, levels in CAMTEST_LEVELS.items():
            for li, lv in enumerate(levels):
                plan += [(k, (li, lv), i) for i in range(a.n_per_level)]
        for k, n in CAMTEST_OBJ.items():
            plan += [(k, None, i) for i in range(n)]

    recs, out_json = [], []
    for idx, (kind, lv, i) in enumerate(plan):
        pid = (f"{kind}_L{lv[0]+1}_{i:02d}" if lv else f"{kind}_{i:04d}")
        seed = a.seed * 100000 + idx
        rng = np.random.default_rng(seed)
        res, tries = None, 0
        while res is None and tries < 100:
            res = make_one(kind, rng, bgs, objs, objs_color, level=(lv[1] if lv else None))
            tries += 1
        if res is None:
            print("  bỏ qua", pid); continue
        A, B, cap, meta = res
        pa, pb = f"images/{pid}_A.jpg", f"images/{pid}_B.jpg"
        cv2.imwrite(os.path.join(a.out, pa), A, [cv2.IMWRITE_JPEG_QUALITY, 95])
        cv2.imwrite(os.path.join(a.out, pb), B, [cv2.IMWRITE_JPEG_QUALITY, 95])
        prompt = prompts[int(rng.integers(len(prompts)))]
        rec = {"pair_id": pid, "seed": seed, "image_A": pa, "image_B": pb, "caption": cap, "prompt": prompt,
               "level": (lv[0] + 1) if lv else 0, "level_value": (lv[1] if lv else None)} | meta
        recs.append(rec)
        img = [a.rel_prefix + pa, a.rel_prefix + pb]
        if a.mode == "train":
            out_json.append({"id": f"ftsyn_{pid}", "image": img,
                             "conversations": [{"from": "human", "value": prompt}, {"from": "gpt", "value": cap}]})
        else:
            out_json.append({"id": pid, "image": img, "conversations": [{"from": "human", "value": prompt}]})
        if (idx + 1) % 250 == 0:
            print(f"  {idx+1}/{len(plan)}", flush=True)

    with open(os.path.join(a.out, "manifest.jsonl"), "w") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    name = "train.json" if a.mode == "train" else "questions.json"
    json.dump(out_json, open(os.path.join(a.out, name), "w"), indent=1)
    df = pd.DataFrame(recs)
    print(f"\nĐã sinh {len(df)} cặp -> {a.out}/{name}")
    print(df["cond"].value_counts().to_string())
    print("\nVí dụ câu mô tả:")
    for c in df.groupby("cond").head(1)["caption"]:
        print("  -", c)


if __name__ == "__main__":
    main()
