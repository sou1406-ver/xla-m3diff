from pathlib import Path
HERE=Path(__file__).parent
s=(HERE.parent/'invariance_ablation/run_confirmation.py').read_text()
start=s.index('gpu_image=');end=s.index('@app.function',start)
image="""gpu_image=(modal.Image.debian_slim(python_version='3.10').apt_install('git','default-jre-headless')
 .pip_install_from_requirements(str(HERE.parent/'mixed_full_benchmark/requirements.txt'))
 .add_local_file(str(HERE.parent/'curated_sft/deduplicate_caption.py'),'/root/deduplicate_caption.py',copy=True)
 .add_local_file(str(HERE.parent/'precision_audit/load_wrapper.py'),'/root/load_wrapper.py',copy=True))
for name in ['eval_questions.json','eval_manifest.json','protocol.json']:
 gpu_image=gpu_image.add_local_file(str(HERE/name),'/root/probe/'+name,copy=True)
RUN='invariance_prompt_probe_v1'

"""
s=s[:start]+image+s[end:]
s=s.replace('m3diff-fresh-confirmation-v1','m3diff-ten-prompt-probe-v1').replace('timeout=1800','timeout=1200')
s=s.replace("assert (out/'PREPARED.json').exists();(out/'load_wrapper.py').write_bytes(Path('/root/load_wrapper.py').read_bytes())", "for p in Path('/root/probe').iterdir():(out/p.name).write_bytes(p.read_bytes())\n (out/'load_wrapper.py').write_bytes(Path('/root/load_wrapper.py').read_bytes())")
s=s.replace(" (out/'eval_rubric.json').write_bytes(Path('/root/eval_rubric.json').read_bytes())\n",'')
s=s.replace("py='/root/invariance-venv/bin/python';uv='/usr/local/bin/uv'","py=sys.executable")
start=s.index(" run([uv,'venv'");end=s.index(" (out/'repo_commit.txt')",start)
s=s[:start]+" (out/'environment_freeze.txt').write_text(subprocess.check_output([py,'-m','pip','freeze'],text=True))\n"+s[end:]
start=s.index(" for arm in ['positive_control'");end=s.index('\n raw={}',start)
s=s[:start]+" for arm,path in [('old_mixed',root/'invariance_ablation_v1/m3diff-mixed-objective-lora'),('balanced',root/'invariance_prompt_balanced_v1/m3diff-balanced-lora')]:\n  evaluate(arm,path,True)\n"+s[end:]
s=s.replace("['baseline','positive_control','mixed_objective']","['baseline','old_mixed','balanced']").replace('==80','==40').replace("'n_eval':80,'generations':240","'n_eval':40,'generations':120").replace('random.Random(2026102803)','random.Random(2026102806)')
s=s.replace("**{k:r[k] for k in ['id','cohort','scene','split','condition']}","**r")
(HERE/'run_modal.py').write_text(s);compile(s,'run_modal.py','exec');print('Prompt probe runner prepared')
