"""Inspect saved LoRA updates and BF16 merge rounding without loading a full model."""
import collections,json,math,re,hashlib
from pathlib import Path
import torch
from safetensors import safe_open

root=Path('/mnt/m3diff');out=root/'precision_audit_v1';out.mkdir(exist_ok=True)
model=root/'invariance_sft_v1/m3diff-invariance-lora';base=root/'baseline_cache/M3Diff'
torch.set_num_threads(8);torch.manual_seed(42)
cfg=json.loads((model/'adapter_config.json').read_text());index=json.loads((base/'model.safetensors.index.json').read_text())['weight_map']
state=torch.load(model/'adapter_model.bin',map_location='cpu',weights_only=True)
records=[]
for name,a in state.items():
    match=re.match(r'(.+)\.lora_A(?:\.default)?\.weight$',name)
    if not match:continue
    b=state[name.replace('.lora_A','.lora_B')]
    stem=match.group(1);base_name=stem.removeprefix('base_model.model.')+'.weight'
    assert base_name in index,base_name
    records.append({'adapter_name':name,'base_name':base_name,'layer':int(re.search(r'\.layers\.(\d+)\.',stem).group(1)),
      'module':stem.rsplit('.',1)[-1],'A_dtype':str(a.dtype),'B_dtype':str(b.dtype),'A_shape':list(a.shape),'B_shape':list(b.shape),
      'B_nonzero_fraction':float(torch.count_nonzero(b)/b.numel()),'B_rms':float(b.float().square().mean().sqrt()),'B_abs_max':float(b.abs().max())})
assert records and any(r['B_nonzero_fraction']>0 for r in records),'Saved adapters contain no learned B updates.'
layers=sorted({r['layer'] for r in records});sample_layers={layers[0],layers[len(layers)//2],layers[-1]}
sample=[r for r in records if r['layer'] in sample_layers];metrics=[]
scale=cfg['lora_alpha']/cfg['r']
for r in sample:
    a=state[r['adapter_name']].float();b=state[r['adapter_name'].replace('.lora_A','.lora_B')].float()
    delta=b@a*scale
    with safe_open(str(base/index[r['base_name']]),framework='pt',device='cpu') as handle:w=handle.get_tensor(r['base_name']).to(torch.bfloat16)
    assert tuple(w.shape)==tuple(delta.shape)
    old=w.float();merged=(old+delta).to(torch.bfloat16).float();rounded=merged-old
    norm=float(torch.linalg.vector_norm(delta));err=float(torch.linalg.vector_norm(rounded-delta))
    item={**r,'n_weights':delta.numel(),'delta_rms':float(delta.square().mean().sqrt()),'delta_abs_max':float(delta.abs().max()),
     'fraction_base_weights_changed_after_bf16_merge':float(torch.count_nonzero(rounded)/rounded.numel()),
     'relative_l2_rounding_error':err/norm if norm else None,'rounded_delta_norm_ratio':float(torch.linalg.vector_norm(rounded))/norm if norm else None}
    metrics.append(item);print('AUDITED',r['base_name'],item['fraction_base_weights_changed_after_bf16_merge'],item['relative_l2_rounding_error'],flush=True)
    del w,old,merged,rounded,delta
summary={'n_adapter_pairs':len(records),'all_adapter_dtypes':sorted({r['A_dtype'] for r in records}|{r['B_dtype'] for r in records}),
 'all_B_nonzero':all(r['B_nonzero_fraction']>0 for r in records),'sample_layers':sorted(sample_layers),'n_sampled_matrices':len(metrics),
 'weighted_changed_base_fraction':sum(r['n_weights']*r['fraction_base_weights_changed_after_bf16_merge'] for r in metrics)/sum(r['n_weights'] for r in metrics),
 'mean_relative_l2_rounding_error':sum(r['relative_l2_rounding_error'] for r in metrics)/len(metrics),
 'interpretation':'Numerical audit only. Rounding can alter small learned deltas; this does not establish an effect on caption quality. Compare merged versus unmerged inference on the same checkpoint before further training.'}
(out/'adapter_parameters.json').write_text(json.dumps(records,indent=2));(out/'sampled_merge_math.json').write_text(json.dumps(metrics,indent=2));(out/'summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(summary,indent=2),flush=True)
