"""Upload reviewed local artifacts; never launches compute."""
import argparse
from pathlib import Path
import modal
HERE=Path(__file__).parent
p=argparse.ArgumentParser(); p.add_argument('files',nargs='+'); args=p.parse_args()
volume=modal.Volume.from_name('m3diff')
with volume.batch_upload(force=True) as batch:
    for name in args.files:
        source=(HERE/name).resolve(); assert source.is_relative_to(HERE.resolve()) and source.is_file()
        batch.put_file(source,'/invariance_v2_20261102/'+name)
        print('Uploading',name)
