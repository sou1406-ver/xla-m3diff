"""Frozen pre-v2 camera-motion proxy. Do not add result-dependent exceptions."""
import re

CAM = re.compile(
    r"\b(perspective|viewpoint|point of view|viewing angle|shooting angle|camera angle|field of view|"
    r"zoom(ed|s|ing)?|panned|"
    r"camera (has |had )?(been )?(moved|shifted|panned|rotated|tilted|turned|zoomed)|"
    r"(the )?view (has )?(shifted|moved|panned|rotated|tilted))\b", re.I)
DEVICE_ADJECTIVES = (
    'black','white','red','blue','green','yellow','gray','grey','brown','pink',
    'silver','golden','digital','security','surveillance','video','web','DSLR','CCTV')
DEVICE_PREPOSITIONS = ('on','in','under','above','beside','behind','near','next to','in front of')
DEVICE_ADJ = re.compile(r'\b(?:'+'|'.join(map(re.escape, DEVICE_ADJECTIVES))+r')\s+(camera)\b',re.I)
DEVICE_LOCATION = re.compile(r'\b(camera)\s+(?:'+'|'.join(map(re.escape, DEVICE_PREPOSITIONS))+r')\b',re.I)

def camera_motion_claim(caption):
    # Mask only camera head spans: never suppress a mixed device/motion sentence.
    spans=[m.span(1) for rx in [DEVICE_ADJ,DEVICE_LOCATION] for m in rx.finditer(caption)]
    masked=list(caption)
    for start,end in spans:
        masked[start:end]='_'*(end-start)
    return bool(CAM.search(''.join(masked)))
