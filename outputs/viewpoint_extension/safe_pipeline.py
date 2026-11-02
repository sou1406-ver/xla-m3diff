"""Only exact decoded-pixel identity can automatically replace a caption.

Approximate registration is an optional review aid after the v1 stress failures.
"""
import argparse,json
from pathlib import Path
import numpy as np
from PIL import Image

def route_features(f,thresholds):
    from registration_gate_frozen import decide
    v1=decide(f,thresholds)
    if f['exact_identity']:
        return {'replace_caption':True,'caption':'The two images show the same scene with no visible changes.',
                'needs_review':False,'reason':'exact_decoded_pixels','v1_would_replace':True}
    alignment=bool(f.get('registration_ok',False))
    return {'replace_caption':False,'caption':None,'needs_review':alignment,'reason':'approximate_registration_advisory_only',
            'v1_would_replace':v1['accept_no_scene_change'],'alignment_found':alignment,
            'target_overlap':f.get('overlap'),'scale':f.get('scale'),'angle':f.get('angle'),
            'review_hint':'Inspect residuals and unmatched regions; geometric similarity does not establish absence of small appearance changes.' if alignment else None}

def assess(before,after,thresholds,registration_advice=False):
    a=np.array(Image.open(before).convert('RGB'));b=np.array(Image.open(after).convert('RGB'))
    exact=a.shape==b.shape and np.array_equal(a,b)
    if exact:return route_features({'exact_identity':True,'registration_ok':True,'overlap':1.0},thresholds)
    if not registration_advice:return {'replace_caption':False,'caption':None,'needs_review':False,'reason':'nonidentical_keep_model_caption'}
    from registration_gate_frozen import features
    f=features(before,after)
    return {**route_features(f,thresholds),'features':f}

def main():
    p=argparse.ArgumentParser();p.add_argument('--manifest',type=Path,required=True);p.add_argument('--image-root',type=Path,required=True)
    p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--audit',type=Path,required=True)
    p.add_argument('--protocol',type=Path,default=Path(__file__).with_name('registration_protocol_frozen.json'))
    p.add_argument('--registration-advice',action='store_true');a=p.parse_args()
    if len({x.resolve() for x in [a.manifest,a.input,a.output,a.audit]})!=4:p.error('All input/output paths must be distinct')
    manifest=json.loads(a.manifest.read_text(encoding='utf-8-sig'));lookup={r['id']:r for r in manifest}
    if len(lookup)!=len(manifest):raise ValueError('Duplicate manifest IDs')
    protocol=json.loads(a.protocol.read_text(encoding='utf-8-sig'))
    rows=[json.loads(l) for l in a.input.read_text(encoding='utf-8-sig').splitlines() if l.strip()]
    if len(rows)!=len({r['id'] for r in rows}):raise ValueError('Duplicate predictions')
    output=[];audits=[]
    for r in rows:
        m=lookup[r['id']]
        if not isinstance(r.get('caption'),str) or len(m['image'])!=2:raise ValueError('Invalid paired prediction')
        d=assess(*(a.image_root/s for s in m['image']),protocol['thresholds'],a.registration_advice)
        output.append({**r,'caption':d['caption'] if d['replace_caption'] else r['caption']});audits.append({'id':r['id'],**d})
    for path in [a.output,a.audit]:path.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in output),encoding='utf8')
    a.audit.write_text(json.dumps(audits,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'n':len(output),'replaced_exact_identity':sum(r['replace_caption'] for r in audits),'approximate_automatic_replacements':0,'review_flags':sum(r.get('needs_review',False) for r in audits)}))

if __name__=='__main__':main()
