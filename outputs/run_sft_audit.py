import json
from pathlib import Path
import modal

app = modal.App('m3diff-real-sft-audit')
volume = modal.Volume.from_name('m3diff')

@app.function(image=modal.Image.debian_slim(python_version='3.10'),
              volumes={'/mnt/m3diff': volume}, timeout=600, scaledown_window=2)
def audit():
    root = Path('/mnt/m3diff')
    repo = root/'baseline_reproduction_v1/repo'
    report = {'checkpoint': {}, 'files': {}, 'data': {}}
    ckpt = root/'ft/m3diff-ft-lora'
    report['checkpoint']['files'] = {str(p.relative_to(ckpt)):p.stat().st_size for p in ckpt.rglob('*') if p.is_file()}
    for name in ['adapter_config.json','trainer_state.json']:
        if (ckpt/name).exists(): report['checkpoint'][name] = json.loads((ckpt/name).read_text())
    tests = set()
    for split in ['Real','Render']:
        qs=json.loads((repo/f'data/evaluation/prompt/OmniDiff_{split}_test.json').read_text())
        tests.update(im for q in qs for im in q['image'])
    for rel in ['ft/train_mix.json','ft/orig/training_m3diff.json']:
        p=root/rel
        if not p.exists(): continue
        rows=json.loads(p.read_text())
        original_count=len(rows)
        if 'orig' in rel:
            rows=[r for r in rows if isinstance(r.get('image'),list) and any('OmniDiff/' in im for im in r['image'])]
        stats={'count':len(rows),'sample':rows[:2],'test_image_overlap_rows':0,'test_path_rows':0,'existing_images':0,'total_images':0}
        stats['all_dataset_count']=original_count
        print('AUDIT',rel,len(rows),flush=True)
        for r in rows:
            ims=r.get('image',[]);ims=[ims] if isinstance(ims,str) else ims
            if any(im.removeprefix('OmniDiff/') in tests for im in ims):stats['test_image_overlap_rows']+=1
            if any('/test/' in im for im in ims):stats['test_path_rows']+=1
            for im in ims:
                stats['total_images']+=1
                candidates=[root/'baseline_cache/OmniDiff'/im.removeprefix('OmniDiff/'),repo/'datasets'/im,root/im,root/'ft'/im]
                if any(c.exists() for c in candidates):stats['existing_images']+=1
        report['data'][rel]=stats
        if 'orig' in rel:
            (root/'ft/orig/omnidiff_only.json').write_text(json.dumps(rows))
    for rel in ['llava/model/builder.py','llava/train/train.py','pyproject.toml']:
        report['files'][rel]=(repo/rel).read_text()
    report['directories']={str(p.relative_to(root)): [x.name for x in p.iterdir()][:20]
      for p in [root/'ft/orig',root/'baseline_cache/OmniDiff',repo/'datasets'] if p.is_dir()}
    out=root/'real_sft_v1';out.mkdir(exist_ok=True)
    (out/'audit.json').write_text(json.dumps(report,indent=2))
    volume.commit()
    print(json.dumps({k:v for k,v in report.items() if k!='files'},indent=2))

@app.local_entrypoint()
def main():
    audit.remote()
