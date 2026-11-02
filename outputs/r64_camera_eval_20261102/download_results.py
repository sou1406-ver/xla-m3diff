from pathlib import Path
import modal
HERE=Path(__file__).parent
v=modal.Volume.from_name('m3diff')
for name in ['SUCCESS.json','timings.json','job_timing.json','camtest_base.jsonl','camtest_ft.jsonl','sanity_ft.jsonl','manifest.jsonl','questions.json','camtest_compare.csv','executed.ipynb']:
    data=b''.join(v.read_file('r64_camera_eval_20261102/'+name))
    (HERE/name).write_bytes(data)
    print(name,len(data),flush=True)
