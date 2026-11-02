"""So điểm OmniDiff (BLEU-4, METEOR, ROUGE-L, CIDEr) giữa model gốc và model fine-tune + kiểm tra các cặp zoom thật."""
import argparse, json, os, re, sys
from pathlib import Path

import numpy as np
from scipy.stats import wilcoxon

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ft_common import CAM  # noqa: E402

p = argparse.ArgumentParser()
p.add_argument("--repo", required=True)
p.add_argument("--split", required=True)
p.add_argument("--base", required=True)
p.add_argument("--ft", required=True)
a = p.parse_args()
sys.path.insert(0, a.repo)
from metrics import load_predictions  # noqa: E402
from pycocotools.coco import COCO  # noqa: E402
from pycocoevalcap.tokenizer.ptbtokenizer import PTBTokenizer  # noqa: E402
from pycocoevalcap.bleu.bleu import Bleu  # noqa: E402
from pycocoevalcap.meteor.meteor import Meteor  # noqa: E402
from pycocoevalcap.rouge.rouge import Rouge  # noqa: E402
from pycocoevalcap.cider.cider import Cider  # noqa: E402

ref = os.path.join(a.repo, f"data/evaluation/reference/OmniDiff_{a.split}.json")
coco = COCO(ref)


def score(pred):
    res = coco.loadRes(load_predictions(Path(pred)))
    ids = res.getImgIds()
    tok = PTBTokenizer()
    gts = tok.tokenize({i: coco.imgToAnns[i] for i in ids})
    rs = tok.tokenize({i: res.imgToAnns[i] for i in ids})
    out, per = {}, {}
    for sc, names in [(Bleu(4), ["B1", "B2", "B3", "Bleu_4"]), (Meteor(), ["METEOR"]), (Rouge(), ["ROUGE_L"]), (Cider(), ["CIDEr"])]:
        s, ps = sc.compute_score(gts, rs)
        s = s if isinstance(s, list) else [s]
        for n, v in zip(names, s):
            out[n] = float(v)
        if names[-1] == "CIDEr":
            per = dict(zip(list(gts.keys()), np.asarray(ps, float)))
    return out, per


cb, pb = score(a.base)
cf, pf = score(a.ft)
print(f"\n== OmniDiff-{a.split} ==")
print(f"{'Chỉ số':<9}{'Gốc':>8}{'Fine-tune':>11}{'Chênh':>8}")
for k in ["Bleu_4", "METEOR", "ROUGE_L", "CIDEr"]:
    print(f"{k:<9}{cb[k]*100:>8.1f}{cf[k]*100:>11.1f}{(cf[k]-cb[k])*100:>+8.1f}")
ids = sorted(set(pb) & set(pf))
x, y = np.array([pb[i] for i in ids]), np.array([pf[i] for i in ids])
print(f"CIDEr từng câu: tăng {int((y > x).sum())}, giảm {int((y < x).sum())}, Wilcoxon p = {wilcoxon(y, x).pvalue:.3g}")

load = lambda fp: {json.loads(l)["image_id"]: json.loads(l)["caption"] for l in open(fp) if l.strip()}
B, F = load(a.base), load(a.ft)
lens = lambda d: np.median([len(v.split()) for v in d.values()])
print(f"Độ dài câu trung vị: gốc {lens(B):.0f} từ, fine-tune {lens(F):.0f} từ")
refs = {r["image_id"]: r["caption"] for r in json.load(open(ref))["annotations"]}
zoom = [k for k, v in refs.items() if re.search(r"\b(perspective|zoom|viewpoint|camera angle|shooting angle)\b", v, re.I)]
print(f"Cặp có câu tham chiếu nói về camera/góc chụp: {len(zoom)} | model nhắc camera: gốc {sum(bool(CAM.search(B.get(k, ''))) for k in zoom)}, "
      f"fine-tune {sum(bool(CAM.search(F.get(k, ''))) for k in zoom)}")
others = [k for k in refs if k not in zoom]
print(f"Cặp KHÔNG có camera trong tham chiếu: model nhắc camera (bịa): gốc {sum(bool(CAM.search(B.get(k, ''))) for k in others)}/{len(others)}, "
      f"fine-tune {sum(bool(CAM.search(F.get(k, ''))) for k in others)}/{len(others)}")
