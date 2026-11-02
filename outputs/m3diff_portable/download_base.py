from pathlib import Path
import argparse,json
from huggingface_hub import snapshot_download
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args()
repo='IVC-liuyuan/M3Diff';revision='d6a8880dc789b0816660278c087ac9ebdfe18dd0'
snapshot_download(repo_id=repo,revision=revision,local_dir=str(args.output),max_workers=2)
(args.output/'download_revision.json').write_text(json.dumps({'repo':repo,'revision':revision},indent=2))
print('Base downloaded. This is inference setup; no training performed.')
