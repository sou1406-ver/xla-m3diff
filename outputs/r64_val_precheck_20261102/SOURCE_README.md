---
pretty_name: OmniDiff
license: cc-by-4.0
language:
  - en
task_categories:
  - image-to-text
tags:
  - image-difference-captioning
  - change-captioning
  - computer-vision
  - multimodal
size_categories:
  - 10K<n<100K
---

# OmniDiff

OmniDiff is a benchmark for fine-grained Image Difference Captioning (IDC):
given two similar images, a model must describe their subtle visual differences
in natural language. The dataset combines complex real-world environments with
near-realistic 3D-rendered scenes and emphasizes precise change localization and
detailed semantic descriptions.

The dataset is introduced in **“OmniDiff: A Comprehensive Benchmark for
Fine-grained Image Difference Captioning”** by Yuan Liu, Saihui Hou, Saijie Hou,
Jiabao Du, Shibei Meng, and Yongzhen Huang (ICCV 2025).

## Highlights

- **15,598 image pairs and captions** from **324 scenes**.
- **8,609 real-world pairs** and **6,989 rendered pairs**.
- **12 change types** spanning semantic changes and visual distractors.
- Human-written, fine-grained captions averaging **60 words**.
- Indoor and outdoor scenes split into train, validation, and test sets at an
  approximately 8:1:1 ratio.
- One centralized JSON Lines file, `annotation.jsonl`, for every subset and
  split.

## Dataset construction

The paper describes a two-stage construction pipeline.

### 1. Change-pair collection

The Real subset covers 224 scenes collected through on-site photography and
carefully selected online videos. Cameras were placed in varied indoor and
outdoor environments, and similar frames with subtle changes were selected.

The Render subset covers 100 scenes: 50 indoor and 50 outdoor environments.
High-quality 3D assets were rendered with Blender, and scene objects were
manually modified to create realistic changes beyond simple tabletop settings.

### 2. Difference-caption collection

Captions were written by human annotators rather than generated automatically.
The annotation guidelines in the paper ask annotators to:

1. Describe meaningful semantic changes while ignoring irrelevant visual
   variation when it is only a distractor.
2. Identify the changed entity with sufficient attributes and spatial context.
3. State how that entity changed, including its before and after state when
   applicable.

The captions were subsequently reviewed for spelling and grammar. A pair may
contain one or more of the following change types:

`viewpoint`, `illumination`, `addition`, `disappearance`, `removal`,
`substitution`, `size`, `color`, `orientation`, `pose`, `ocr`, and `counting`.

## Statistics

### Release files

| Subset | Split | Unique images | Image pairs |
| --- | --- | ---: | ---: |
| Real | train | 1,674 | 7,007 |
| Real | val | 189 | 799 |
| Real | test | 191 | 803 |
| Render | train | 975 | 5,445 |
| Render | val | 135 | 777 |
| Render | test | 128 | 767 |
| **Total** |  | **3,292** | **15,598** |

### Caption statistics reported in the paper

| Statistic | Value |
| --- | ---: |
| Captions | 15,598 |
| Average words per caption | 60.0 |
| Total sentences | 38,653 |
| Average sentences per caption | 2.5 |
| Vocabulary size | 3,793 |
| Captions longer than 20 words | 37% |

## Directory layout

```text
OmniDiff/
├── annotation.jsonl
├── README.md
├── Real/
│   ├── train/images/
│   ├── val/images/
│   └── test/images/
└── Render/
    ├── train/images/
    ├── val/images/
    └── test/images/
```

All paths in `annotation.jsonl` are relative to the OmniDiff root. Image names
are ASCII-only and zero-padded. Rendered filenames additionally indicate
whether the source scene is indoor or outdoor. Extensions match the actual JPEG
or PNG encoding.

## Unified annotation format

`annotation.jsonl` is the sole source of ground-truth annotations. It uses
[JSON Lines](https://jsonlines.org/): each non-empty line is one independent
JSON object, allowing streaming reads and direct ingestion by dataset tools.
Each line has the following form:

```json
{
  "id": "real_train_pair_000001",
  "subset": "real",
  "split": "train",
  "image": [
    "Real/train/images/real_train_000019.jpg",
    "Real/train/images/real_train_000009.jpg"
  ],
  "caption": "A fine-grained description of the observed differences."
}
```

Field definitions:

| Field | Type | Description |
| --- | --- | --- |
| `id` | string | Globally unique, zero-padded annotation identifier. |
| `subset` | string | `real` or `render`. |
| `split` | string | `train`, `val`, or `test`. |
| `image` | array[string] | Ordered pair: first image followed by second image. |
| `caption` | string | Human-written ground-truth difference description. |

IDs follow `<subset>_<split>_pair_<six-digit index>`, for example
`render_test_pair_000001`.

### Loading annotations

```python
import json
from pathlib import Path

root = Path("/path/to/OmniDiff")
with (root / "annotation.jsonl").open(encoding="utf-8") as handle:
    annotations = [json.loads(line) for line in handle if line.strip()]

train = [item for item in annotations if item["split"] == "train"]

first_image = root / train[0]["image"][0]
second_image = root / train[0]["image"][1]
caption = train[0]["caption"]
```

## Evaluation

The paper evaluates change captioning with BLEU-4, METEOR, ROUGE-L, CIDEr-D,
and SPICE using the Microsoft COCO caption-evaluation protocol. OmniDiff-Real
and OmniDiff-Render are evaluated separately in a multi-change captioning
setting.

## Citation

```bibtex
@inproceedings{liu2025omnidiff,
  title     = {OmniDiff: A Comprehensive Benchmark for Fine-grained Image Difference Captioning},
  author    = {Liu, Yuan and Hou, Saihui and Hou, Saijie and Du, Jiabao and Meng, Shibei and Huang, Yongzhen},
  booktitle = {Proceedings of the IEEE/CVF International Conference on Computer Vision (ICCV)},
  pages     = {21440--21449},
  year      = {2025}
}
```

## License

OmniDiff is licensed under the
[Creative Commons Attribution 4.0 International License](https://creativecommons.org/licenses/by/4.0/)
(CC BY 4.0). You may share and adapt the dataset for any purpose, including
commercial use, provided that you give appropriate credit, link to the license,
and indicate whether changes were made. See [LICENSE](LICENSE) for the license
notice and the official
[legal code](https://creativecommons.org/licenses/by/4.0/legalcode.en).
