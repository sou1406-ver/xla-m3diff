from pathlib import Path
import json,hashlib,dataclasses
from datetime import datetime,timezone
from decimal import Decimal as D
import modal
H=Path(__file__).parent;P=H/'camera240'
assert not (P/'ADMISSION.json').exists()
s=modal.Workspace.from_context().billing.summary(cycle='2026-11')
cost=max(abs(s.adjustments['Credits']),s.metered_cost+sum(v for k,v in s.adjustments.items() if k!='Credits'))
assert s.billed_cost==0 and s.adjustments.get('Plan Cost',D(0))==0
assert D(30)-cost>=D('2.50'),'Insufficient credit including buffer'
body={'authorized':True,'cap_usd':2,'reservation_upper_usd':'1.95','credit_consumed':str(cost),'credit_remaining_estimate':str(D(30)-cost),'billing':dataclasses.asdict(s),'utc':datetime.now(timezone.utc).isoformat(),'no_retry':True,'synthetic600_authorized_now':False,'synthetic600_condition':'Only after settlement camera, remaining actual>=2.5 USD and measured worst-case cost fits credit with buffer; no borrowing.'}
body['code_sha256']={n:hashlib.sha256((H/n).read_bytes()).hexdigest() for n in ['camera_modal.py','camera240_score.py']}
(P/'ADMISSION.json').write_text(json.dumps(body,default=str,indent=2))
v=modal.Volume.from_name('m3diff')
with v.batch_upload() as batch:
 for f in P.iterdir():
  if f.is_file():batch.put_file(f,'/mbr_pilot_20261103/camera240/'+f.name)
print(json.dumps(body,default=str,indent=2))
