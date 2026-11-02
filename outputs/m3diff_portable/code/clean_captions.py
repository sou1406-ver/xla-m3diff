from pathlib import Path
import argparse,json
from deduplicate_caption import deduplicate_caption
p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--version',choices=['v1','v2'],default='v2');args=p.parse_args()
if args.version=='v2':
 from deduplicate_caption_v2 import deduplicate_caption
assert args.input.resolve()!=args.output.resolve(),'Choose another output file'
rows=[json.loads(l) for l in args.input.read_text(encoding='utf8').splitlines() if l.strip()];changed=0
for r in rows:
 value,_=deduplicate_caption(r['caption']);changed+=value!=r['caption'];r['caption']=value
args.output.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf8');print({'rows':len(rows),'changed':changed})
