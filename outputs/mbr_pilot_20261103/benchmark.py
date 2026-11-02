"""Base-only20pair generation benchmark. No reference captions or IDF are read here."""
from pathlib import Path
import os,json,time,hashlib,copy,gc,collections
import torch
from PIL import Image
from transformers import Qwen2ForCausalLM
from llava.model.builder import load_pretrained_model
from llava.mm_utils import get_model_name_from_path,process_images,KeywordsStoppingCriteria
from llava.conversation import conv_templates,SeparatorStyle
from llava.eval.model_vqa_qwen_OmniDiff_Real import preprocess_qwen
from llava.utils import disable_torch_init
P=Path('/mnt/m3diff/mbr_pilot_20261103');cfg=json.loads((P/'PROTOCOL.json').read_text());assert (P/'CPU_READY.json').exists()
assert not (P/'BENCHMARK_ATTEMPT.json').exists(),'No automatic repeated benchmark'
start=time.time();deadline=float(os.environ['MBR_SOFT_DEADLINE_UNIX'])
(P/'BENCHMARK_ATTEMPT.json').write_text(json.dumps({'started':start,'gpu':torch.cuda.get_device_name(0),'model':'base_original','budget_cap_usd':1}))
disable_torch_init();base='/mnt/m3diff/baseline_cache/M3Diff'
tokenizer,model,processor,_=load_pretrained_model(base,None,get_model_name_from_path(base),use_flash_attn=False,torch_dtype=torch.bfloat16,device_map={'':0})
model.eval();assert not model.training
mdp=collections.Counter(str(v.dtype) for n,v in model.named_parameters() if 'vision_resampler' in n or 'mm_projector' in n);assert dict(mdp)=={'torch.bfloat16':86}
audit={'loaded_generation_config':model.generation_config.to_dict(),'model_class':type(model).__name__,'config':{k:getattr(model.config,k) for k in ['num_hidden_layers','num_attention_heads','num_key_value_heads','hidden_size']},'mdp_projector_dtype_counts':dict(mdp),'no_quantization':True,'no_flash_attention':True,'no_training':True,'sampling':{k:cfg[k] for k in ['temperature','top_p','top_k','repetition_penalty','num_beams','max_new_tokens']},'implementation':'vision/MDP embeddings computed once per pair; native Qwen2 generate called on cached embeddings. Batch expands before LLM prefill; no shared prefix KV cache.'}
(P/'GENERATION_AUDIT.json').write_text(json.dumps(audit,indent=2))
questions=json.loads((P/'questions20.json').read_text());selection={x['id']:x for x in json.loads((P/'selection20.json').read_text())};records=[];batch_size=8
def clean(seq):
    ids=seq.tolist();eos=model.generation_config.eos_token_id;eos=eos if isinstance(eos,list) else [eos]
    stop=next((i+1 for i,x in enumerate(ids) if x in eos),len(ids));ids=ids[:stop]
    text=tokenizer.decode(ids,skip_special_tokens=True).strip();assert text,'Empty caption: stop, do not resample'
    return text,len(ids),len(ids)>=cfg['max_new_tokens']
def generate(emb,n,sample):
    kw=dict(max_new_tokens=cfg['max_new_tokens'],num_beams=1,repetition_penalty=1.05,use_cache=True,num_return_sequences=n,do_sample=sample,return_dict_in_generate=True)
    if sample:kw.update(temperature=.7,top_p=.8,top_k=20)
    else:kw.update(temperature=1.,top_p=1.,top_k=50)
    out=Qwen2ForCausalLM.generate(model,inputs_embeds=emb,**kw)
    answer=[clean(x) for x in out.sequences];del out
    return answer
def measured(call):
    torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats();t=time.perf_counter();answer=call();torch.cuda.synchronize()
    return answer,{'seconds':time.perf_counter()-t,'peak_allocated_bytes':torch.cuda.max_memory_allocated(),'peak_reserved_bytes':torch.cuda.max_memory_reserved()}
for index,q in enumerate(questions):
    if time.time()>deadline-90:
        print('SOFT_BUDGET_STOP before pair',index,flush=True);break
    t=time.perf_counter();ids=preprocess_qwen([{'from':'human','value':q['conversations'][0]['value']},{'from':'gpt','value':None}],tokenizer,has_image=True).cuda()
    ims=[process_images([Image.open('/mnt/m3diff/r64_val_precheck_20261102/images/'+n).convert('RGB')],processor,model.config).to(device='cuda',dtype=torch.bfloat16) for n in q['image']];images=[torch.cat(ims,dim=0)]
    with torch.inference_mode():
        _,_,_,_,emb,_=model.prepare_inputs_labels_for_multimodal(ids,None,None,None,None,images)
        torch.cuda.synchronize();embed_seconds=time.perf_counter()-t
        greedy,gt=measured(lambda:generate(emb,1,False));greedy=greedy[0]
        if index==0:
            # Verify that bypassing the LLaVA generate wrapper preserves its greedy caption.
            conv=conv_templates['qwen_2'].copy();stop=conv.sep if conv.sep_style!=SeparatorStyle.TWO else conv.sep2
            original=model.generate(inputs=ids,images=images,do_sample=False,num_beams=1,max_new_tokens=1024,repetition_penalty=1.05,use_cache=True,stopping_criteria=[KeywordsStoppingCriteria([stop],tokenizer,ids)])
            wrapper=clean(original[0]);assert wrapper[0]==greedy[0],(wrapper,greedy)
            audit['greedy_wrapper_parity_first_pair']=True;audit['observed_prompt_embedding_tokens']=emb.shape[1];(P/'GENERATION_AUDIT.json').write_text(json.dumps(audit,indent=2));del original
        seed=cfg['seed']+int(hashlib.sha256(q['id'].encode()).hexdigest()[:8],16)%1000000
        methods={};order=['sequential8','batch8'] if index%2==0 else ['batch8','sequential8']
        for name in order:
            torch.manual_seed(seed);torch.cuda.manual_seed_all(seed)
            if name=='sequential8':
                outputs,timing=measured(lambda:[generate(emb,1,True)[0] for _ in range(8)]);effective=1
            else:
                errors=[]
                while True:
                    try:
                        outputs,timing=measured(lambda:[x for _ in range(8//batch_size) for x in generate(emb,batch_size,True)]);effective=batch_size;break
                    except torch.cuda.OutOfMemoryError:
                        errors.append({'batch_size':batch_size,'error':'CUDA OOM'});gc.collect();torch.cuda.empty_cache()
                        if batch_size==1:raise
                        batch_size//=2;torch.manual_seed(seed);torch.cuda.manual_seed_all(seed)
                timing['batch_oom_fallbacks']=errors
            assert len(outputs)==8
            methods[name]={'samples':[x[0] for x in outputs],'generated_tokens':[x[1] for x in outputs],'hit_token_cap':[x[2] for x in outputs],'effective_batch_size':effective,**timing,'seed':seed}
        r={'id':q['id'],'domain':selection[q['id']]['subset'],'prompt_embedding_tokens':emb.shape[1],'image_embedding_seconds':embed_seconds,'greedy':{'caption':greedy[0],'generated_tokens':greedy[1],'hit_token_cap':greedy[2],**gt},'methods':methods,'measurement_order':order}
        with (P/'results20.jsonl').open('a') as f:f.write(json.dumps(r)+'\n')
        records.append(r);(P/'PROGRESS.json').write_text(json.dumps({'completed_pairs':len(records),'planned':20,'last_id':q['id'],'elapsed_seconds':time.time()-start,'batch_size':batch_size}))
        print('MBR20_PROGRESS',(P/'PROGRESS.json').read_text(),flush=True)
        del emb,ims,images,ids;gc.collect();torch.cuda.empty_cache()
(P/'BENCHMARK_DONE.json').write_text(json.dumps({'complete':len(records)==20,'pairs':len(records),'wall_seconds':time.time()-start,'model':'base_original','no_training':True},indent=2));print('BENCHMARK_DONE',len(records),flush=True)
