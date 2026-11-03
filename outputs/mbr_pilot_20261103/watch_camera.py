"""Read-only local result collector. Never allocates GPU or retries inference."""
from pathlib import Path
import json,time,dataclasses
from datetime import datetime,timezone
from decimal import Decimal as D
import modal
H=Path(__file__).parent;P=H/'camera240';v=modal.Volume.from_name('m3diff');remote='/mbr_pilot_20261103/camera240/'
def download(n):
 try:data=b''.join(v.read_file(remote+n))
 except FileNotFoundError:return None
 (P/n).write_bytes(data);return json.loads(data) if n.endswith('.json') else data
start=time.time();last=0
while time.time()-start<4800:
 done=download('PIPELINE_DONE.json')
 if done:break
 progress=download('PROGRESS.json')
 if progress and progress['completed_pairs']!=last:
  last=progress['completed_pairs'];print(json.dumps(progress),flush=True)
 (P/'LOCAL_WATCH.json').write_text(json.dumps({'utc':datetime.now(timezone.utc).isoformat(),'last_completed':last,'read_only':True}))
 time.sleep(30)
else:raise RuntimeError('Watch expired; no job retried or new GPU allocated')
for n in ['GPU_ATTEMPT.json','ATTEMPT.json','GPU_DONE.json','GEN_DONE.json','GENERATION_AUDIT.json','PROGRESS.json','results.jsonl','SELECTION.json','base.jsonl','mbr.jsonl','REVIEW_240.csv','METRICS.json','generation.log']:download(n)
s=modal.Workspace.from_context().billing.summary(cycle='2026-11');cost=max(abs(s.adjustments['Credits']),s.metered_cost+sum(v for k,v in s.adjustments.items() if k!='Credits'))
snapshot={'utc':datetime.now(timezone.utc).isoformat(),'billing':dataclasses.asdict(s),'api_consumption':str(cost),'credit_remaining_estimate':str(D(30)-cost),'not_final_invoice':True}
(P/'FINAL_BILLING.json').write_text(json.dumps(snapshot,default=str,indent=2))
print('PIPELINE_DONE',json.dumps(done),flush=True);print('BILLING',json.dumps(snapshot,default=str),flush=True)
