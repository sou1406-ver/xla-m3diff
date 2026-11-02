from pathlib import Path
import argparse,json
p=argparse.ArgumentParser();p.add_argument('--before',type=Path,required=True);p.add_argument('--after',type=Path,required=True);p.add_argument('--output',type=Path,default=Path('questions.json'));args=p.parse_args()
images=[args.before.resolve(),args.after.resolve()]
assert all(p.is_file() for p in images),'Image file missing'
args.output.write_text(json.dumps([{'id':'my_pair_001','image':[str(p) for p in images],'conversations':[{'from':'human','value':"What's the difference between 2 images?  <image><image>Difference:"}]}],ensure_ascii=False,indent=2),encoding='utf8')
print('Wrote',args.output.resolve())
