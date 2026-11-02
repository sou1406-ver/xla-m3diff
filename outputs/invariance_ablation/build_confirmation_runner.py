from pathlib import Path
here=Path(__file__).parent
s=(here/'run_modal.py').read_text()
start=s.index('for name in ');end=s.index('@app.function',start)
s=s[:start]+"gpu_image=gpu_image.add_local_file(str(HERE.parent/'precision_audit/load_wrapper.py'),'/root/load_wrapper.py',copy=True)\nRUN='invariance_confirmation_v1'\n\n"+s[end:]
s=s.replace('m3diff-invariance-ablation-v1','m3diff-fresh-confirmation-v1').replace("gpu='A100-40GB',cpu=8,memory=65536", "gpu='A10',cpu=4,memory=32768")
s=s.replace("for p in Path('/root/ablation').iterdir():(out/p.name).write_bytes(p.read_bytes())", "assert (out/'PREPARED.json').exists();(out/'load_wrapper.py').write_bytes(Path('/root/load_wrapper.py').read_bytes())")
s=s.replace("save('gpu.json',{'actual_gpu':gpu,'all_generations_same_container':True})", "save('gpu.json',{'actual_gpu':gpu,'all_generations_same_container':True});\n import re\n assert re.search(r'\\bA10(?:G)?\\b',gpu),'Unexpected GPU class; stop before inference'")
start=s.index(" for arm,weight in ");end=s.index('\n raw={}',start)
s=s[:start]+" for arm in ['positive_control','mixed_objective']:\n  evaluate(arm,root/'invariance_ablation_v1'/('m3diff-'+arm.replace('_','-')+'-lora'),True)\n"+s[end:]
s=s.replace('==72','==80').replace("'n_eval':72,'generations':216", "'n_eval':80,'generations':240").replace('random.Random(2026102801)','random.Random(2026102803)')
(here/'run_confirmation.py').write_text(s)
compile(s,'run_confirmation.py','exec')
print('Confirmation runner generated and syntax checked')
