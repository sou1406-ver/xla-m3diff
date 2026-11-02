"""Download selected experiment artifacts; no model or GPU is launched."""
import argparse
from pathlib import Path
import modal
HERE=Path(__file__).parent
p=argparse.ArgumentParser(); p.add_argument('files',nargs='+'); args=p.parse_args()
volume=modal.Volume.from_name('m3diff')
for name in args.files:
    target=HERE/name; target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('wb') as f:
        for part in volume.read_file('invariance_v2_20261102/'+name): f.write(part)
    print(name,target.stat().st_size)
