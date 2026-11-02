"""Conservative CPU geometry check. No scene IDs or expected labels enter the gate."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'.deps'))
import numpy as np
from PIL import Image

def features(before,after):
    import cv2
    cv2.setRNGSeed(42);cv2.setNumThreads(2)
    a0=np.asarray(Image.open(before).convert('RGB'));b0=np.asarray(Image.open(after).convert('RGB'))
    if a0.shape==b0.shape and np.array_equal(a0,b0):return {'exact_identity':True,'registration_ok':True,'overlap':1.0}
    def resize(a):
        im=Image.fromarray(a);im.thumbnail((1024,1024),Image.Resampling.BICUBIC);return np.array(im)
    a,b=resize(a0),resize(b0)
    if a.shape!=b.shape:return {'exact_identity':False,'registration_ok':False,'reason':'different_aspect_or_size'}
    ag=cv2.cvtColor(a,cv2.COLOR_RGB2GRAY);bg=cv2.cvtColor(b,cv2.COLOR_RGB2GRAY)
    sift=cv2.SIFT_create(nfeatures=5000,contrastThreshold=0.02)
    ka,da=sift.detectAndCompute(ag,None);kb,db=sift.detectAndCompute(bg,None)
    if da is None or db is None:return {'exact_identity':False,'registration_ok':False,'reason':'no_features'}
    pairs=cv2.BFMatcher(cv2.NORM_L2).knnMatch(da,db,k=2)
    good=[m for pair in pairs if len(pair)==2 for m,n in [pair] if m.distance<0.7*n.distance]
    if len(good)<20:return {'exact_identity':False,'registration_ok':False,'reason':'few_matches','matches':len(good)}
    x=np.float32([ka[m.queryIdx].pt for m in good]);y=np.float32([kb[m.trainIdx].pt for m in good])
    mat,inliers=cv2.estimateAffinePartial2D(x,y,method=cv2.RANSAC,ransacReprojThreshold=1.0,maxIters=5000,confidence=0.999,refineIters=30)
    if mat is None:return {'exact_identity':False,'registration_ok':False,'reason':'fit_failed'}
    mask=inliers.ravel().astype(bool);w,h=a.shape[1],a.shape[0]
    cells={(min(3,int(p[0]/w*4)),min(3,int(p[1]/h*4))) for p in x[mask]}
    scale=float(np.hypot(mat[0,0],mat[1,0]));angle=float(np.degrees(np.arctan2(mat[1,0],mat[0,0])))
    info={'exact_identity':False,'matches':len(good),'inliers':int(mask.sum()),'inlier_ratio':float(mask.mean()),'grid_cells':len(cells),'scale':scale,'angle':angle,'matrix':mat.tolist()}
    if mask.sum()<40 or mask.mean()<0.65 or len(cells)<8 or not 0.65<=scale<=1.65 or abs(angle)>15:
        return {**info,'registration_ok':False,'reason':'geometric_support_insufficient'}
    aligned=cv2.warpAffine(a,mat,(w,h),flags=cv2.INTER_CUBIC,borderMode=cv2.BORDER_CONSTANT)
    valid=cv2.warpAffine(np.ones((h,w),np.uint8),mat,(w,h),flags=cv2.INTER_NEAREST,borderMode=cv2.BORDER_CONSTANT)
    valid=cv2.erode(valid,np.ones((9,9),np.uint8)).astype(bool)
    diff=np.abs(aligned.astype(np.float32)-b.astype(np.float32));maxdiff=diff.max(axis=2)
    hot=((maxdiff>30)&valid).astype(np.uint8)
    opened=cv2.morphologyEx(hot,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
    n,labels,stats,_=cv2.connectedComponentsWithStats(opened,8)
    largest=int(stats[1:,cv2.CC_STAT_AREA].max()) if n>1 else 0
    return {**info,'registration_ok':True,'overlap':float(valid.mean()),'mean_absolute_rgb_error':float(diff[valid].mean()),
       'p99_max_channel_error':float(np.percentile(maxdiff[valid],99)),
       'fraction_max_channel_above_30':float(hot.sum()/valid.sum()),'largest_opened_residual_pixels':largest,'valid_pixels':int(valid.sum())}

def decide(f,thresholds):
    if f['exact_identity']:return {'accept_no_scene_change':True,'reason':'identical_decoded_pixels','caption':'The two images show the same scene with no visible changes.'}
    ok=f.get('registration_ok',False) and all(f.get(k,float('inf'))<=v for k,v in thresholds['upper_bounds'].items()) and f.get('overlap',0)>=thresholds['minimum_overlap']
    return {'accept_no_scene_change':bool(ok),'reason':'registered_dense_match' if ok else 'fallback_to_model',
        'caption':'Only the image framing, scale, or rotation changes; no object changes are detected in the shared visible area.' if ok else None}

if __name__=='__main__':
    import argparse,json
    parser=argparse.ArgumentParser();parser.add_argument('--partition',choices=['dev','validation'],required=True);args=parser.parse_args()
    root=Path(__file__).parent;manifest=json.loads((root/'manifest.json').read_text());rows=[]
    for r in manifest:
        if r['partition']!=args.partition:continue
        f=features(*(root/'dataset'/im for im in r['image']));row={k:r[k] for k in ['id','scene','split','partition','condition']};row['features']=f;rows.append(row)
        print(r['id'],json.dumps(f),flush=True)
    (root/f'registration_{args.partition}_features.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf8')
