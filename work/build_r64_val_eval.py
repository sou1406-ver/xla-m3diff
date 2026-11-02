from pathlib import Path
import json
root=Path(__file__).resolve().parents[1];out=root/'outputs/r64_val_precheck_20261102';cam=root/'outputs/r64_camera_eval_20261102'
nb=json.loads((cam/'r64-camera-only.ipynb').read_text(encoding='utf-8'));nb['cells']=nb['cells'][:8]
def code(s):nb['cells'].append({'cell_type':'code','metadata':{},'execution_count':None,'outputs':[],'source':s.splitlines(True)})
code('''RUN='/mnt/m3diff/r64_val_precheck_20261102'
import hashlib
lock=json.load(open(f'{RUN}/SELECTION_LOCK.json'))
assert hashlib.sha256(open(f'{RUN}/questions.json','rb').read()).hexdigest()==lock['hashes']['questions.json']
assert len(json.load(open(f'{RUN}/questions.json')))==200
path=f'{REPO}/llava/eval/model_vqa_qwen_OmniDiff_Real.py'
src=open(path).read()
assert '    # Load and shard the evaluation data.' in src
audit_code="""    model.eval()
    from collections import Counter
    gen_audit={'loaded_generation_config':model.generation_config.to_dict(),
       'effective_explicit_overrides':{'do_sample':False,'temperature':0,'top_p':None,'num_beams':1,'max_new_tokens':1024,'repetition_penalty':1.05},
       'model_name':model_name,'dtype_arg':args.torch_dtype,
       'mdp_projector_dtype_counts':dict(Counter(str(p.dtype) for n,p in model.named_parameters() if 'vision_resampler' in n or 'mm_projector' in n))}
    json.dump(gen_audit,open(args.answers_file+'.generation_audit.json','w'),indent=2)
    print('GENERATION_AUDIT',gen_audit,flush=True)
"""
src=src.replace('    # Load and shard the evaluation data.',audit_code+'    # Load and shard the evaluation data.')
assert 'max_new_tokens=args.max_new_tokens,' in src
src=src.replace('max_new_tokens=args.max_new_tokens,','max_new_tokens=args.max_new_tokens,\\n                repetition_penalty=1.05,')
open(path,'w').write(src)
json.dump({'runner_sha256':hashlib.sha256(src.encode()).hexdigest(),'repo_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd='/mnt/m3diff/baseline_reproduction_v1/repo',text=True).strip(),'gpu':gpu},open(f'{RUN}/runtime.json','w'),indent=2)
timings={'gpu':gpu,'evals':[]}
for arm,lora in [('base',False),('r64',True)]:
    answers=f'{RUN}/{arm}.jsonl'
    assert not os.path.exists(answers), 'Do not mix preexisting captions into matched session'
    t0=time.time()
    run_eval(f'{RUN}/questions.json',answers,f'{RUN}/images',lora=lora)
    qs=json.load(open(f'{RUN}/questions.json'));rs=[json.loads(l) for l in open(answers) if l.strip()]
    assert [r['id'] for r in rs]==[q['id'] for q in qs] and all(r['caption'].strip() for r in rs)
    timings['evals'].append({'arm':arm,'n':len(rs),'wall_seconds':time.time()-t0})
    json.dump(timings,open(f'{RUN}/timings.json','w'),indent=2)
''')
scoring='''from pathlib import Path
import json
from pycocotools.coco import COCO
from pycocoevalcap.tokenizer.ptbtokenizer import PTBTokenizer
from pycocoevalcap.cider.cider import Cider
p=Path('/mnt/m3diff/r64_val_precheck_20261102');result={};per=[]
for domain in ['real','render']:
    coco=COCO(str(p/f'{domain}_reference.json'));ids=coco.getImgIds();result[domain]={}
    for arm in ['base','r64']:
        rows=[json.loads(l) for l in (p/f'{arm}.jsonl').read_text().splitlines() if l.strip()]
        rows=[{'image_id':r['id'],'caption':r['caption']} for r in rows if r['id'] in ids]
        assert len(rows)==100
        res=coco.loadRes(rows);tok=PTBTokenizer()
        gts=tok.tokenize({i:coco.imgToAnns[i] for i in ids});pred=tok.tokenize({i:res.imgToAnns[i] for i in ids})
        score,scores=Cider().compute_score(gts,pred);result[domain][arm]={'n':100,'CIDEr_x100':float(score)*100}
        per += [{'domain':domain,'arm':arm,'id':i,'CIDEr_x100':float(s)*100} for i,s in zip(ids,scores)]
    result[domain]['delta_r64_minus_base']=result[domain]['r64']['CIDEr_x100']-result[domain]['base']['CIDEr_x100']
(p/'metrics.json').write_text(json.dumps(result,indent=2));(p/'per_pair_cider.json').write_text(json.dumps(per,indent=2))
print(json.dumps(result,indent=2))
'''
code('subprocess.run([PY,"-c",'+repr(scoring)+'],check=True)\n'+"json.dump({'complete':True,'pairs':200,'arms':['base','r64'],'same_container':True,'v2_trained':False,'full_test_run':False},open(f'{RUN}/SUCCESS.json','w'),indent=2)\nprint('DONE matched val200, stop GPU.')\n")
for i,c in enumerate(nb['cells']):c['id']='cell'+str(i)
(out/'r64-val200-only.ipynb').write_text(json.dumps(nb,ensure_ascii=False,indent=1),encoding='utf-8')
s=(cam/'run_modal.py').read_text().replace('r64_camera_eval_20261102','r64_val_precheck_20261102').replace('r64-camera-only','r64-val200-only').replace('m3diff-r64-camera-eval','m3diff-r64-val-precheck').replace('timeout=2400','timeout=3000').replace('timeout=1800','timeout=2700')
(out/'run_modal.py').write_text(s,encoding='utf-8')
# New round-local budget snapshot, no mutation of the November2 invariance ledger.
b=(root/'outputs/invariance_v2_20261102/budget.py').read_text().replace('bounded invariance experiment','bounded matched val200 precheck')
(out/'budget.py').write_text(b,encoding='utf-8')
print('Prepared matched val notebook')
