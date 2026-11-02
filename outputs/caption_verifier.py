"""Conservative caption-claim checker. No reference captions are consumed here.

Rule-based development prototype, not an identity model or calibrated fact verifier.
Box + image alignment + visual similarity can still confuse similar objects.
"""
import re

REMOVE = re.compile(r'\b(?:(?:has|have)\s+disappeared|(?:is|are)\s+no\s+longer\s+(?:visible|present)|(?:has|have)\s+been\s+removed)\b', re.I)
ADD = re.compile(r'\b(?:(?:has|have)\s+(?:newly\s+)?appeared|appears?|(?:is|are)\s+now\s+(?:visible|present))\b', re.I)
NOUNS = [('storage box',r'storage boxes?|storage box'),('toy car',r'toy cars?'),
 ('toy truck',r'toy trucks?'),('train toy',r'train toys?'),('stuffed toy',r'(?:stuffed|plush) toys?'),
 ('fire extinguisher',r'fire extinguishers?'),('potted plant',r'potted plants?'),
 ('pickup truck',r'pickup trucks?'),('ladder',r'ladders?'),('speaker',r'speakers?'),
 ('cushion',r'cushions?'),('blanket',r'blankets?'),('stool',r'stools?'),
 ('mattress',r'mattress(?:es)?'),('pillow',r'pillows?'),('chair',r'chairs?'),
 ('table',r'tables?'),('cabinet',r'cabinets?|cupboards?'),('bed',r'beds?'),
 ('person',r'person|people|man|men|woman|women|boy|girl|child|children'),
 ('bicycle',r'bicycles?|bikes?'),('motorcycle',r'motorcycles?'),('car',r'cars?|suvs?'),
 ('truck',r'trucks?'),('dog',r'dogs?'),('cat',r'cats?'),('bottle',r'bottles?'),
 ('cup',r'cups?|mugs?'),('bowl',r'bowls?'),('vase',r'vases?'),('book',r'books?'),
 ('clock',r'clocks?'),('bag',r'bags?|backpacks?'),('ball',r'balls?'),('box',r'boxes|box')]


def extract_claims(caption):
    sentences = re.split(r'(?<=[.!?])\s+',caption.strip())
    claims=[]
    for si,sentence in enumerate(sentences):
        events=[('removed',m) for m in REMOVE.finditer(sentence)]+[('added',m) for m in ADD.finditer(sentence)]
        if len(events)!=1:continue  # never edit a sentence with mixed event claims
        event,m=events[0]
        if re.search(r'\b(replaced|not|never|whether|might|may|could)\b',sentence,re.I):continue
        subject=sentence[:m.start()]
        head=re.split(r'\b(?:on|in|at|near|beside|above|below|behind|with|wearing|that|which|to|of)\b',subject,1,flags=re.I)[0]
        matches=[]
        for label,pattern in NOUNS:
            for hit in re.finditer(r'\b(?:'+pattern+r')\b',head,re.I):
                matches.append((hit.start(),-len(hit.group()),label,hit.end()))
        if not matches:continue
        matches.sort()
        first=matches[0]
        # Reject multiple different subject nouns; nested compound/generic hits are fine.
        if any(x[0]>=first[3] and x[2]!=first[2] for x in matches):continue
        claims.append({'sentence_index':si,'sentence':sentence,'event':event,'label':first[2]})
    return sentences,claims


def box_iou(a,b):
    inter=max(0,min(a[2],b[2])-max(a[0],b[0]))*max(0,min(a[3],b[3])-max(a[1],b[1]))
    aa=max(0,a[2]-a[0])*max(0,a[3]-a[1]);bb=max(0,b[2]-b[0])*max(0,b[3]-b[1])
    return inter/max(1e-9,aa+bb-inter)


def align_pair(a,b):
    import cv2
    import numpy as np
    gray_a=cv2.cvtColor(a,cv2.COLOR_RGB2GRAY);gray_b=cv2.cvtColor(b,cv2.COLOR_RGB2GRAY)
    sift=cv2.SIFT_create(nfeatures=3000)
    ka,da=sift.detectAndCompute(gray_a,None);kb,db=sift.detectAndCompute(gray_b,None)
    info={'ok':False,'reason':'not enough reliable keypoints'}
    if da is None or db is None or len(da)<2 or len(db)<2:return info,None
    pairs=cv2.BFMatcher().knnMatch(db,da,k=2)
    good=[p[0] for p in pairs if len(p)==2 and p[0].distance<.70*p[1].distance]
    info['matches']=len(good)
    if len(good)<25:return info,None
    src=np.float32([kb[m.queryIdx].pt for m in good]);dst=np.float32([ka[m.trainIdx].pt for m in good])
    h,mask=cv2.findHomography(src,dst,cv2.RANSAC,3.)
    if h is None or mask is None:return info,None
    inliers=mask.ravel().astype(bool);info['inliers']=int(inliers.sum());info['inlier_ratio']=float(inliers.mean())
    if inliers.sum()<25 or inliers.mean()<.45:return info,None
    area=cv2.contourArea(cv2.convexHull(dst[inliers]))/(a.shape[0]*a.shape[1])
    info['inlier_coverage']=float(area)
    corners=np.float32([[0,0],[b.shape[1],0],[b.shape[1],b.shape[0]],[0,b.shape[0]]])
    projected=cv2.perspectiveTransform(corners[None],h)[0]
    scale=abs(cv2.contourArea(projected))/(a.shape[0]*a.shape[1])
    if area<.10 or not .4<=scale<=2.5 or not np.isfinite(projected).all():
        info['reason']='insufficient geometric coverage or extreme transform';return info,None
    info.update(ok=True,reason='reliable global 2D alignment',H=h.tolist())
    return info,h


def stable_region(a,b,h,boxes_a,boxes_b,allow_structure=False):
    """Abstain unless strong geometric and visual evidence agrees. No absent->present logic."""
    import cv2
    import numpy as np
    info={'stable':False,'reason':'no unambiguous corresponding boxes'}
    if not boxes_a or not boxes_b or max(len(boxes_a),len(boxes_b))>5:return info
    aa=[[x1*a.shape[1]/1000,y1*a.shape[0]/1000,x2*a.shape[1]/1000,y2*a.shape[0]/1000] for x1,y1,x2,y2 in boxes_a]
    bb=[]
    for x1,y1,x2,y2 in boxes_b:
        p=np.float32([[x1*b.shape[1]/1000,y1*b.shape[0]/1000],[x2*b.shape[1]/1000,y1*b.shape[0]/1000],
                      [x2*b.shape[1]/1000,y2*b.shape[0]/1000],[x1*b.shape[1]/1000,y2*b.shape[0]/1000]])
        q=cv2.perspectiveTransform(p[None],h)[0]
        bb.append([float(q[:,0].min()),float(q[:,1].min()),float(q[:,0].max()),float(q[:,1].max())])
    matrix=np.array([[box_iou(x,y) for y in bb] for x in aa])
    ia,ib=np.unravel_index(matrix.argmax(),matrix.shape)
    best=float(matrix[ia,ib]);info['aligned_box_iou']=best
    if best<.60:return info
    alternatives=[matrix[ia,j] for j in range(len(bb)) if j!=ib]+[matrix[i,ib] for i in range(len(aa)) if i!=ia]
    if alternatives and best-max(alternatives)<.20:
        info['reason']='ambiguous object association';return info
    # Category has multiple instances: removing a whole added/removed claim may target another instance.
    if len(aa)!=1 or len(bb)!=1:
        info['reason']='multiple instances: sentence identity not established';return info
    x1,y1,x2,y2=aa[ia]
    x1,y1=max(0,int(x1)),max(0,int(y1));x2,y2=min(a.shape[1],int(x2)),min(a.shape[0],int(y2))
    if min(x2-x1,y2-y1)<16:return info
    warp=cv2.warpPerspective(b,h,(a.shape[1],a.shape[0]))
    valid=cv2.warpPerspective(np.ones(b.shape[:2],np.uint8),h,(a.shape[1],a.shape[0]),flags=cv2.INTER_NEAREST)
    if valid[y1:y2,x1:x2].mean()<.98:
        info['reason']='object region partly outside overlap';return info
    ga=cv2.cvtColor(a[y1:y2,x1:x2],cv2.COLOR_RGB2GRAY).astype(np.float32)
    gb=cv2.cvtColor(warp[y1:y2,x1:x2],cv2.COLOR_RGB2GRAY).astype(np.float32)
    ma=cv2.GaussianBlur(ga,(11,11),1.5);mb=cv2.GaussianBlur(gb,(11,11),1.5)
    va=cv2.GaussianBlur(ga*ga,(11,11),1.5)-ma*ma
    vb=cv2.GaussianBlur(gb*gb,(11,11),1.5)-mb*mb
    cov=cv2.GaussianBlur(ga*gb,(11,11),1.5)-ma*mb
    ssim=float((((2*ma*mb+6.5025)*(2*cov+58.5225))/((ma*ma+mb*mb+6.5025)*(va+vb+58.5225))).mean())
    def edges(g):
        g=cv2.GaussianBlur(g,(3,3),.8)
        return cv2.magnitude(cv2.Sobel(g,cv2.CV_32F,1,0),cv2.Sobel(g,cv2.CV_32F,0,1)).ravel()
    ea,eb=edges(ga),edges(gb)
    corr=float(np.corrcoef(ea,eb)[0,1]) if min(ea.std(),eb.std())>1.0 else 0.
    info.update(ssim=ssim,edge_correlation=corr,box_a=aa[ia],box_b_aligned=bb[ib])
    info['stable']=ssim>=.80 and corr>=.85
    if allow_structure and not info['stable']:
        # Color changes can alter intensity correlation while retaining the same ladder/shape.
        # Require tighter geometric agreement and bidirectional edge persistence instead.
        def canny(g):
            g=cv2.GaussianBlur(g,(3,3),.7)
            mag=cv2.magnitude(cv2.Sobel(g,cv2.CV_32F,1,0),cv2.Sobel(g,cv2.CV_32F,0,1))
            hi=max(20.,float(np.percentile(mag,85)))
            return cv2.Canny(np.clip(g,0,255).astype(np.uint8),hi*.4,hi)>0
        ca,cb=canny(ga),canny(gb)
        density_a,density_b=float(ca.mean()),float(cb.mean())
        info.update(edge_density_a=density_a,edge_density_b=density_b)
        if min(ca.sum(),cb.sum())>=30 and .02<=density_a<=.40 and .02<=density_b<=.40:
            da=cv2.distanceTransform((~ca).astype(np.uint8),cv2.DIST_L2,3)
            db=cv2.distanceTransform((~cb).astype(np.uint8),cv2.DIST_L2,3)
            p=float((db[ca]<=2.).mean());r=float((da[cb]<=2.).mean())
            f1=2*p*r/max(1e-9,p+r)
            info.update(edge_persistence_precision=p,edge_persistence_recall=r,edge_persistence_f1=f1)
            if best>=.80 and ssim>=.50 and f1>=.85 and min(p,r)>=.80:
                info['stable']=True
                info['verification_path']='color-tolerant structural persistence'
    info['reason']='strong same-region evidence' if info['stable'] else 'visual agreement insufficient; keep caption'
    return info


def minimally_filter(sentences,decisions):
    drop={d['claim']['sentence_index'] for d in decisions if d.get('action')=='drop'}
    kept=[s for i,s in enumerate(sentences) if i not in drop]
    if not kept:
        for d in decisions:
            if d.get('action')=='drop':d.update(action='keep',reason='would remove entire caption; abstain')
        return ' '.join(sentences)
    return ' '.join(kept)


def verify_color_transition(a,b,h,box_a,box_b,source_color):
    """Color evidence at corresponding interior pixels; requires external object/geometry guards.

    Only chromatic source colors are supported. Dark/white source objects are ambiguous
    with shadow/background, so this method abstains rather than inventing a transition.
    """
    import numpy as np
    import cv2
    names=['black','white','gray','red','orange','yellow','green','blue','purple','pink','brown','other']
    def classify(rgb):
        hsv=cv2.cvtColor(np.clip(rgb,0,255).astype(np.uint8),cv2.COLOR_RGB2HSV)
        hh,ss,vv=hsv[...,0],hsv[...,1],hsv[...,2]
        lab=np.full(hh.shape,11,np.uint8)
        for idx,cond in [(3,(hh<10)|(hh>=170)),(4,(hh>=10)&(hh<22)),(5,(hh>=22)&(hh<36)),
                         (6,(hh>=36)&(hh<85)),(7,(hh>=100)&(hh<135)),(8,(hh>=135)&(hh<160)),
                         (9,(hh>=160)&(hh<170))]:lab[cond]=idx
        lab[(lab==4)&(vv<150)]=10
        lab[ss<50]=2;lab[(ss<35)&(vv>200)]=1;lab[vv<80]=0
        return lab
    info={'supported':False,'reason':'insufficient unambiguous color evidence'}
    if source_color not in ['red','orange','yellow','green','blue','purple','pink','brown']:return info
    # Warp and correct only a robust global illumination offset estimated outside target boxes.
    warped=cv2.warpPerspective(b,h,(a.shape[1],a.shape[0]))
    valid=cv2.warpPerspective(np.ones(b.shape[:2],np.uint8),h,(a.shape[1],a.shape[0]),flags=cv2.INTER_NEAREST)>0
    x1,y1,x2,y2=box_a
    x1,y1=max(0,int(x1)),max(0,int(y1));x2,y2=min(a.shape[1],int(x2)),min(a.shape[0],int(y2))
    if min(x2-x1,y2-y1)<16:return info
    background=valid.copy();background[max(0,y1-8):y2+8,max(0,x1-8):x2+8]=False
    if background.sum()<1000:return info
    offset=np.median(warped[background].astype(np.float32)-a[background].astype(np.float32),axis=0)
    corrected=np.clip(warped.astype(np.float32)-offset,0,255).astype(np.uint8)
    la=classify(a[y1:y2,x1:x2]);lb=classify(corrected[y1:y2,x1:x2])
    mask=(la==names.index(source_color)).astype(np.uint8)
    mask=cv2.erode(mask,np.ones((3,3),np.uint8))>0
    mask &= valid[y1:y2,x1:x2]
    info.update(source_interior_pixels=int(mask.sum()),global_offset_rgb=offset.tolist())
    if mask.sum()<30 or mask.mean()<.01:return info
    counts=np.bincount(lb[mask],minlength=len(names));dominant=int(counts.argmax())
    fraction=float(counts[dominant]/counts.sum())
    info.update(source_color=source_color,target_color=names[dominant],target_fraction=fraction,
                color_fractions={name:float(counts[i]/counts.sum()) for i,name in enumerate(names) if counts[i]})
    if names[dominant] not in [source_color,'other'] and fraction>=.80:
        info.update(supported=True,reason='dominant color changed at matched object-interior pixels')
    return info
