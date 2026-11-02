"""Fixed-training-IDF CIDEr-D consensus utility; never opens val/test labels."""
import math,collections
def counts(text):
    w=text.split();return collections.Counter(tuple(w[i:i+n]) for n in range(1,5) for i in range(len(w)-n+1))
def document_frequency(documents):
    df=collections.Counter()
    for refs in documents:df.update(set(k for s in refs for k in counts(s)))
    return {'N':len(documents),'df':dict(df)}
def vector(text,cache):
    vec=[{} for _ in range(4)];norm=[0.0]*4
    for k,tf in counts(text).items():
        x=tf*(math.log(cache['N'])-math.log(max(1,cache['df'].get(k,0))));i=len(k)-1;vec[i][k]=x;norm[i]+=x*x
    return vec,[math.sqrt(x) for x in norm],len(text.split())
def pair_score(hyp,ref,cache):
    h,hn,hl=vector(hyp,cache);r,rn,rl=vector(ref,cache);score=0
    for i in range(4):
        if hn[i] and rn[i]:score+=sum(min(v,r[i].get(k,0))*r[i].get(k,0) for k,v in h[i].items())/(hn[i]*rn[i])
    return 10*score/4*math.exp(-((hl-rl)**2)/(2*6.0**2))
def select(captions,cache):
    assert len(captions)==9
    scores=[sum(pair_score(c,r,cache) for j,r in enumerate(captions) if j!=i)/8 for i,c in enumerate(captions)]
    best=max(range(9),key=lambda i:(scores[i],-i))
    return best,scores
