from pathlib import Path
here=Path(__file__).parent
s=(here.parent/'invariance_sft/run_modal.py').read_text()
start=s.index('cpu_image=');end=s.index('@app.function(image=gpu_image')
s=s[:start]+'''gpu_image=(modal.Image.debian_slim(python_version='3.10').apt_install('git').pip_install('uv')
 .add_local_file(str(DIAG/'deduplicate_caption.py'),'/root/deduplicate_caption.py',copy=True))
for name in ['protocol.json','train_weighted.py','train.json','eval_questions.json','eval_manifest.json','data_audit.json']:
 gpu_image=gpu_image.add_local_file(str(HERE/name),'/root/ablation/'+name,copy=True)
gpu_image=gpu_image.add_local_file(str(HERE.parent/'precision_audit/load_wrapper.py'),'/root/ablation/load_wrapper.py',copy=True)
RUN='invariance_ablation_v1'

'''+s[end:]
s=s.replace('m3diff-invariance-sft-v1','m3diff-invariance-ablation-v1').replace('timeout=3600','timeout=1800')
s=s.replace("assert (out/'PREPARED.json').exists();", "out.mkdir(exist_ok=True);\n for p in Path('/root/ablation').iterdir():(out/p.name).write_bytes(p.read_bytes())\n ")
s=s.replace("if lora:args+=['--model-base',ckpt]", "if lora:args=[py,out/'load_wrapper.py','--adapter-mode','unmerged_fp32','--load-audit',out/(arm+'_load_audit.json'),'--model-path',path,'--model-base',ckpt]")
start=s.index(" if not (out/'TRAIN_DONE.json').exists():")
end=s.index('\n raw={}',start)
train=s[start:s.index(" evaluate('invariance',model,True)",start)]
train=train.replace(" if not (out/'TRAIN_DONE.json').exists():", " if not (out/(arm+'_TRAIN_DONE.json')).exists():")
train=train.replace("out/'train_seeded.py'", "out/'train_weighted.py'").replace("'--num_train_epochs','1'", "'--num_train_epochs','2'").replace("'--learning_rate','5e-6'", "'--learning_rate','2e-5'")
train=train.replace("run(args,'train',env)","run(args,arm+'_train',train_env)").replace("==32","==64").replace("'steps':32","'steps':64").replace("save('TRAIN_DONE.json'", "save(arm+'_TRAIN_DONE.json'")
train=train.replace("'verify_frozen',env", "arm+'_verify_frozen',env")
train='\n'.join(' '+line if line else line for line in train.splitlines())
s=s[:start]+" for arm,weight in [('positive_control',0),('mixed_objective',1)]:\n  model=out/('m3diff-'+arm.replace('_','-')+'-lora')\n  train_env=dict(env,M3DIFF_NEGATIVE_WEIGHT=str(weight))\n"+train+"\n  evaluate(arm,model,True)\n models=[out/('m3diff-'+a.replace('_','-')+'-lora') for a in ['positive_control','mixed_objective']]\n audits=[json.loads((p/'initialization_audit.json').read_text()) for p in models]\n for k in ['lora_init_sha256','MDP_init_sha256']:assert audits[0][k]==audits[1][k]\n orders=[json.loads((p/'sample_orders.json').read_text()) for p in models]\n assert orders[0]==orders[1] and len(orders[0])==2\n assert all(sorted(order)==list(range(256)) for order in orders[0])\n save('matched_training_audit.json',{'initialization_matches':True,'both_epoch_orders_match':True,'epochs':2,'steps_per_arm':64})\n"+s[end:]
s=s.replace("['baseline','invariance']", "['baseline','positive_control','mixed_objective']").replace('==108','==72')
s=s.replace("'candidate_1':deduplicate_caption(raw[arms[0]][r['id']]['caption'])[0],'candidate_2':deduplicate_caption(raw[arms[1]][r['id']]['caption'])[0]", "**{f'candidate_{i+1}':deduplicate_caption(raw[a][r['id']]['caption'])[0] for i,a in enumerate(arms)}")
s=s.replace("'n_eval':108,'generations':216", "'n_eval':72,'generations':216").replace('random.Random(2026102724)','random.Random(2026102801)')
s=s[:s.index('@app.local_entrypoint()')]+'''@app.local_entrypoint()
def main():
 experiment.remote()
'''
(here/'run_modal.py').write_text(s)
compile(s,'run_modal.py','exec')
print('Runner generated and syntax checked')
