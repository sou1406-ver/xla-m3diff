"""Remove exact repeated sentences, preserving quoted contents and distinct claims.

Fixed before viewing the curated-SFT evaluation scores. No semantic rewriting.
"""
import re

def sentence_spans(text):
    result=[];start=0;quote=None;i=0
    while i<len(text):
        ch=text[i]
        apostrophe=(ch=="'" and i>0 and i+1<len(text) and text[i-1].isalnum() and text[i+1].isalnum())
        closed=False
        if ch in ['"',"'"] and not apostrophe:
            if quote==ch:quote=None;closed=True
            elif quote is None:quote=ch
        boundary=(quote is None and (ch in '.!?' or (closed and i>0 and text[i-1] in '.!?'))
                  and (i+1==len(text) or text[i+1].isspace()))
        if boundary:
            part=text[start:i+1].strip()
            if part:result.append(part)
            start=i+1
        i+=1
    tail=text[start:].strip()
    if tail:result.append(tail)
    return result

def deduplicate_caption(caption):
    parts=sentence_spans(caption);seen=set();kept=[];removed=0;repeated=[]
    for part in parts:
        key=re.sub(r'\s+',' ',part).strip()
        if key in seen:
            removed+=1;repeated.append(key)
        else:seen.add(key);kept.append(part)
    trimmed=False
    if removed>=2 and kept and kept[-1][-1:] not in '.!?\"\'':
        tail=re.sub(r'\s+',' ',kept[-1]).strip()
        if len(tail)<=80 and any(s.startswith(tail) and len(s)>len(tail) for s in repeated):
            kept.pop();trimmed=True
    result=' '.join(kept) if removed or trimmed else caption
    return result,{'removed_exact_sentences':removed,'trimmed_repetition_fragment':trimmed,'changed':result!=caption}

if __name__=='__main__':
    # Repeated model output is removed; distinct object locations remain distinct.
    cap='The chair disappears. The cup turns red. The chair disappears. The chair disappears. The'
    assert deduplicate_caption(cap)[0]=='The chair disappears. The cup turns red.'
    cap='The left chair disappears. The right chair disappears.'
    assert deduplicate_caption(cap)[0]==cap
    cap='The sign reads "Go. Go." The person\'s hat changes to blue.'
    assert deduplicate_caption(cap)[0]==cap
    cap="The text changes to 'YES'. The text changes to 'yes'."
    assert deduplicate_caption(cap)[0]==cap
    cap='The size changes to 1.5 meters. The blue box remains.'
    assert deduplicate_caption(cap)[0]==cap
    cap='The chair disappears. The cup appears. The cup'
    assert deduplicate_caption(cap)[0]==cap
    print('Passed preservation, quotation, decimal, location and loop-fragment checks.')
