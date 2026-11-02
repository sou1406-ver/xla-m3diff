"""Apply locked exact-sentence deduplication to saved M3Diff predictions."""
import argparse
import json
from pathlib import Path
from deduplicate_caption import deduplicate_caption

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--audit',type=Path,required=True)
    args=parser.parse_args()
    paths=[p.resolve() for p in [args.input,args.output,args.audit]]
    if len(set(paths))!=3:parser.error('Input, output and audit must be different files.')
    rows=[];audits=[];ids=set()
    for line_number,line in enumerate(args.input.read_text(encoding='utf-8-sig').splitlines(),1):
        if not line.strip():continue
        row=json.loads(line)
        key=row.get('id',row.get('image_id'))
        if key is None or key in ids:raise ValueError(f'Missing/duplicate id at line {line_number}')
        if not isinstance(row.get('caption'),str):raise ValueError(f'Invalid caption at line {line_number}')
        ids.add(key);caption,audit=deduplicate_caption(row['caption'])
        rows.append({**row,'caption':caption});audits.append({'id':key,**audit})
    for path in [args.output,args.audit]:path.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf8')
    args.audit.write_text(json.dumps(audits,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'n':len(rows),'changed':sum(r['changed'] for r in audits),'output':str(args.output)}))

if __name__=='__main__':main()
