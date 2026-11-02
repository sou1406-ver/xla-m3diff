import time
import argparse
import json
import os
import re
from typing import Dict

import torch
import transformers
from PIL import Image
from tqdm import tqdm

from llava.constants import DEFAULT_IMAGE_TOKEN, IGNORE_INDEX, IMAGE_TOKEN_INDEX
from llava.conversation import SeparatorStyle, conv_templates
from llava.mm_utils import KeywordsStoppingCriteria, get_model_name_from_path, process_images
from llava.model.builder import load_pretrained_model
from llava.utils import disable_torch_init


def split_list(lst, n):
    """Split a list into exactly n approximately equal chunks."""
    if n <= 0:
        raise ValueError("n must be a positive integer")
    chunk_size, remainder = divmod(len(lst), n)
    return [
        lst[i * chunk_size + min(i, remainder) : (i + 1) * chunk_size + min(i + 1, remainder)]
        for i in range(n)
    ]


def get_chunk(lst, n, k):
    chunks = split_list(lst, n)
    if not 0 <= k < len(chunks):
        raise IndexError(f"chunk index {k} is out of range for {len(chunks)} chunks")
    return chunks[k]


def preprocess_qwen(
    sources,
    tokenizer: transformers.PreTrainedTokenizer,
    has_image: bool = False,
    system_message: str = "You are a helpful assistant.",
) -> Dict:
    roles = {"human": "<|im_start|>user", "gpt": "<|im_start|>assistant"}

    im_start, im_end = tokenizer.additional_special_tokens_ids[:2]

    nl_tokens = tokenizer("\n").input_ids
    _system = tokenizer("system").input_ids + nl_tokens

    # Apply the Qwen chat template.
    input_ids, targets = [], []

    source = sources
    if roles[source[0]["from"]] != roles["human"]:
        source = source[1:]

    input_id, target = [], []
    system = [im_start] + _system + tokenizer(system_message).input_ids + [im_end] + nl_tokens
    input_id += system
    target += [im_start] + [IGNORE_INDEX] * (len(system) - 3) + [im_end] + nl_tokens
    assert len(input_id) == len(target)
    for j, sentence in enumerate(source):
        role = roles[sentence["from"]]
        if has_image and sentence["value"] is not None and "<image>" in sentence["value"]:
            num_image = len(re.findall(DEFAULT_IMAGE_TOKEN, sentence["value"]))
            texts = sentence["value"].split("<image>")
            _input_id = tokenizer(role).input_ids + nl_tokens
            for i, text in enumerate(texts):
                _input_id += tokenizer(text).input_ids
                if i < len(texts) - 1:
                    _input_id += [IMAGE_TOKEN_INDEX]
            _input_id += [im_end] + nl_tokens
            assert sum([i == IMAGE_TOKEN_INDEX for i in _input_id]) == num_image
        else:
            if sentence["value"] is None:
                _input_id = tokenizer(role).input_ids + nl_tokens
            else:
                _input_id = (
                    tokenizer(role).input_ids
                    + nl_tokens
                    + tokenizer(sentence["value"]).input_ids
                    + [im_end]
                    + nl_tokens
                )
        input_id += _input_id
        if role == "<|im_start|>user":
            _target = [im_start] + [IGNORE_INDEX] * (len(_input_id) - 3) + [im_end] + nl_tokens
        elif role == "<|im_start|>assistant":
            _target = (
                [im_start]
                + [IGNORE_INDEX] * len(tokenizer(role).input_ids)
                + _input_id[len(tokenizer(role).input_ids) + 1 : -2]
                + [im_end]
                + nl_tokens
            )
        else:
            raise NotImplementedError
        target += _target

    input_ids.append(input_id)
    targets.append(target)
    input_ids = torch.tensor(input_ids, dtype=torch.long)
    targets = torch.tensor(targets, dtype=torch.long)
    return input_ids


def eval_model(args):

    # Load the model and its image processor.
    import random
    import numpy as np
    random.seed(42)
    np.random.seed(42)
    torch.manual_seed(42)
    torch.cuda.manual_seed_all(42)
    disable_torch_init()
    model_path = os.path.expanduser(args.model_path)
    model_name = get_model_name_from_path(model_path)
    print(model_path)
    torch_dtype = getattr(torch, args.torch_dtype)
    quant_mode = os.environ.get("M3DIFF_QUANT", "none")
    skip = ["vision_tower", "vision_resampler", "mm_projector", "lm_head"]
    extra = {}
    if quant_mode == "8bit":
        extra["quantization_config"] = transformers.BitsAndBytesConfig(
            load_in_8bit=True, llm_int8_skip_modules=skip)
    elif quant_mode == "4bit":
        extra["quantization_config"] = transformers.BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4", bnb_4bit_use_double_quant=True,
            llm_int8_skip_modules=skip)
    print(f"[patch] quant_mode={quant_mode}", flush=True)
    tokenizer, model, image_processor, _ = load_pretrained_model(
        model_path,
        args.model_base,
        model_name,
        use_flash_attn=args.flash_attention,
        torch_dtype=torch_dtype,
        device_map={"": 0},
        **extra,
    )
    # Load and shard the evaluation data.
    with open(os.path.expanduser(args.question_file)) as f:
        questions = json.load(f)
    questions = get_chunk(questions, args.num_chunks, args.chunk_idx)
    answers_file = os.path.expanduser(args.answers_file)
    answers_dir = os.path.dirname(answers_file)
    if answers_dir:
        os.makedirs(answers_dir, exist_ok=True)
    expected_ids = {q["id"] for q in questions}
    saved = {}
    if os.path.exists(answers_file):
        with open(answers_file) as f:
            lines = f.readlines()
        for i, line in enumerate(lines):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                if i == len(lines) - 1:
                    print("[resume] Bỏ dòng cuối bị ngắt khi ghi", flush=True)
                    continue
                raise
            if row.get("id") not in expected_ids or row.get("image_id") != row["id"]:
                raise RuntimeError("File kết quả chứa ID ngoài tập câu hỏi hoặc sai schema")
            if not isinstance(row.get("caption"), str) or not row["caption"].strip():
                raise RuntimeError("File kết quả chứa caption rỗng")
            if row["id"] in saved:
                raise RuntimeError("File kết quả chứa ID trùng")
            saved[row["id"]] = row
    tmp = answers_file + ".repair.tmp"
    with open(tmp, "w") as f:
        for row in saved.values():
            f.write(json.dumps(row) + "\n")
    os.replace(tmp, answers_file)
    questions = [q for q in questions if q["id"] not in saved]
    print(f"[resume] {len(saved)} xong, còn {len(questions)}", flush=True)
    model.eval()
    ans_file = open(answers_file, "a")

    for line in tqdm(questions):
        image_files = line["image"]
        qs = args.extra_prompt + line["conversations"][0]["value"]
        conv = conv_templates[args.conv_mode].copy()
        conv.append_message(conv.roles[0], qs)
        conv.append_message(conv.roles[1], None)
        input_ids = preprocess_qwen(
            [{"from": "human", "value": qs}, {"from": "gpt", "value": None}],
            tokenizer,
            has_image=True,
        ).cuda()
        image_tensors = []
        for image_file in image_files:
            image = Image.open(os.path.join(args.image_folder, image_file)).convert("RGB")
            image_tensors.append(
                process_images([image], image_processor, model.config).to(torch_dtype)
            )

        image_tensors = torch.cat(image_tensors, dim=0)
        image_tensors = [image_tensors]
        stop_str = conv.sep if conv.sep_style != SeparatorStyle.TWO else conv.sep2
        keywords = [stop_str]
        stopping_criteria = KeywordsStoppingCriteria(keywords, tokenizer, input_ids)
        torch.cuda.synchronize()
        gen_started = time.monotonic()
        with torch.inference_mode():
            output_ids = model.generate(
                inputs=input_ids,
                images=image_tensors,
                do_sample=True if args.temperature > 0 else False,
                temperature=args.temperature,
                top_p=args.top_p,
                num_beams=args.num_beams,
                max_new_tokens=args.max_new_tokens,
                use_cache=args.use_cache,
                stopping_criteria=[stopping_criteria],
            )

        torch.cuda.synchronize()
        gen_seconds = time.monotonic() - gen_started
        outputs = tokenizer.batch_decode(output_ids, skip_special_tokens=True)[0]
        outputs = outputs.strip()
        if outputs.endswith(stop_str):
            outputs = outputs[: -len(stop_str)]
        outputs = outputs.strip()
        ans_file.write(
            json.dumps(
                {
                    "id": line["id"],
                    "image_id": line["id"],
                    "caption": outputs,
                    "generated_token_slots": int(output_ids.shape[-1]),
                    "last_token_id": int(output_ids[0, -1]),
                    "tokenizer_eos_token_id": tokenizer.eos_token_id,
                    "generation_seconds": gen_seconds,
                    "max_new_tokens": args.max_new_tokens,
                }
            )
            + "\n"
        )
        ans_file.flush()
        os.fsync(ans_file.fileno())

    ans_file.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", type=str, required=True)
    parser.add_argument("--model-base", type=str, default=None)
    parser.add_argument("--image-folder", type=str, required=True)
    parser.add_argument("--extra-prompt", type=str, default="")
    parser.add_argument("--question-file", type=str, required=True)
    parser.add_argument("--answers-file", type=str, default="./results/OmniDiff_Real/result.jsonl")
    parser.add_argument("--conv-mode", type=str, default="qwen_2")
    parser.add_argument("--num-chunks", type=int, default=1)
    parser.add_argument("--chunk-idx", type=int, default=0)
    parser.add_argument("--temperature", type=float, default=0)
    parser.add_argument("--top_p", type=float, default=None)
    parser.add_argument("--num_beams", type=int, default=1)
    parser.add_argument("--max-new-tokens", type=int, default=1024)
    parser.add_argument(
        "--torch-dtype", choices=("float16", "bfloat16", "float32"), default="bfloat16"
    )
    parser.add_argument("--flash-attention", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--use-cache", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args()

    eval_model(args)
