"""Apply an explicit optional CPU guard to existing paired-image captions.

Default is exact decoded-pixel identity only. Approximate registration requires opt-in.
"""
import argparse,json
from pathlib import Path
import numpy as np
from PIL import Image
from registration_gate import features,decide

def try_no_change(before,after,mode='identity-only',thresholds=None):
    if mode=='identity-only':
        a=np.asarray(Image.open(before).convert('RGB'));b=np.asarray(Image.open(after).convert('RGB'))
        exact=a.shape==b.shape and np.array_equal(a,b)
        return {'accept_no_scene_change':bool(exact),'reason':'identical_decoded_pixels' if exact else 'fallback_to_model',
                'caption':'The two images show the same scene with no visible changes.' if exact else None}
    if mode!='registration' or thresholds is None:raise ValueError('Registration requires explicit mode and locked thresholds.')
    f=features(before,after)
    return {**decide(f,thresholds),'features':f}

def main():
    p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,required=True);p.add_argument('--image-root',type=Path,required=True)
    p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--audit',type=Path,required=True)
    p.add_argument('--mode',choices=['identity-only','registration'],default='identity-only');p.add_argument('--protocol',type=Path)
    a=p.parse_args()
    if len({x.resolve() for x in [a.manifest,a.input,a.output,a.audit]})!=4:p.error('Manifest, input, output and audit must be distinct files.')
    protocol=json.loads(a.protocol.read_text(encoding='utf-8-sig')) if a.protocol else None
    if a.mode=='registration' and protocol is None:p.error('Registration requires --protocol registration_protocol.json')
    manifest=json.loads(a.manifest.read_text(encoding='utf-8-sig'));lookup={r['id']:r for r in manifest}
    if len(lookup)!=len(manifest):raise ValueError('Duplicate manifest IDs')
    rows=[json.loads(l) for l in a.input.read_text(encoding='utf-8-sig').splitlines() if l.strip()]
    if len(rows)!=len({r['id'] for r in rows}):raise ValueError('Duplicate prediction IDs')
    out=[];audits=[]
    for r in rows:
        m=lookup[r['id']]
        if not isinstance(r.get('caption'),str) or len(m['image'])!=2:raise ValueError('Invalid caption or image pair')
        d=try_no_change(*(a.image_root/x for x in m['image']),a.mode,protocol['thresholds'] if protocol else None)
        out.append({**r,'caption':d['caption'] if d['accept_no_scene_change'] else r['caption']})
        audits.append({'id':r['id'],'mode':a.mode,**d,'changed':out[-1]['caption']!=r['caption']})
    for path in [a.output,a.audit]:path.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in out),encoding='utf8')
    a.audit.write_text(json.dumps(audits,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'n':len(rows),'mode':a.mode,'routed':sum(d['accept_no_scene_change'] for d in audits),'changed':sum(d['changed'] for d in audits)}))

if __name__=='__main__':main()
