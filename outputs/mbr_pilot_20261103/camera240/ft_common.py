"""Hàm chung cho phần đánh giá fine-tune."""
import re

from scipy.stats import binomtest

CAM = re.compile(
    r"\b(perspective|viewpoint|point of view|viewing angle|shooting angle|camera angle|field of view|"
    r"zoom(ed|s|ing)?|panned|"
    r"camera (has |had )?(been )?(moved|shifted|panned|rotated|tilted|turned|zoomed)|"
    r"(the )?view (has )?(shifted|moved|panned|rotated|tilted))\b", re.I)   # không dùng 'tilted'/'frame' đứng riêng: hay là tư thế vật / khung tranh
ZOOM_IN = re.compile(r"\bzoom(ed|s|ing)? in\b|\bcloser\b", re.I)
ZOOM_OUT = re.compile(r"\bzoom(ed|s|ing)? out\b|\bfarther\b|\bmore of the scene\b", re.I)
CW = re.compile(r"\bclockwise\b", re.I)
CCW = re.compile(r"\b(counter-?clockwise|anti-?clockwise)\b", re.I)


def camera_sents(caption):
    return [s for s in re.split(r"(?<=[.!?;])\s+", caption) if CAM.search(s)]


def camera_dir_ok(caption, cond, direction):
    ss = " ".join(camera_sents(caption))
    if not ss:
        return False
    if cond == "zoom_in" or (direction == "in"):
        return bool(ZOOM_IN.search(ss)) and not ZOOM_OUT.search(ss)
    if cond == "zoom_out" or (direction == "out"):
        return bool(ZOOM_OUT.search(ss)) and not ZOOM_IN.search(ss)
    if direction in ("clockwise", "counterclockwise"):
        ccw = bool(CCW.search(ss))
        cw = bool(CW.search(ss)) and not ccw
        return ccw if direction == "counterclockwise" else cw
    if direction in ("left", "right"):
        other = "right" if direction == "left" else "left"
        return bool(re.search(rf"\b{direction}\b", ss, re.I)) and not re.search(rf"\b{other}\b", ss, re.I)
    return False


def mcnemar(a, b):
    """a, b: list bool ghép cặp (model gốc, model fine-tune). p-value McNemar chính xác."""
    n01 = sum(1 for x, y in zip(a, b) if not x and y)
    n10 = sum(1 for x, y in zip(a, b) if x and not y)
    if n01 + n10 == 0:
        return 1.0, n01, n10
    return binomtest(n01, n01 + n10, 0.5).pvalue, n01, n10
