"""Read-only per-object cost audit for the user's spending question."""
from pathlib import Path
from datetime import datetime,timezone
from decimal import Decimal
import modal,dataclasses,json
ROOT=Path(__file__).parent
start=datetime(2026,10,1,tzinfo=timezone.utc);end=datetime.now(timezone.utc)
rows=modal.Workspace.from_context().billing.report(start=start,end=end,resolution='h')
body={'start_utc':start.isoformat(),'end_utc':end.isoformat(),'resolution':'h','items':[dataclasses.asdict(r) for r in rows]}
(ROOT/'full_billing_snapshot.json').write_text(json.dumps(body,default=str,ensure_ascii=False,indent=2),encoding='utf8')
groups={}
for r in rows:
 key=r.object_id
 if key not in groups:groups[key]={'object_id':key,'description':r.description,'cost':Decimal(0),'resources':{}}
 g=groups[key];g['cost']+=r.cost
 for resource,value in r.cost_by_resource.items():g['resources'][resource]=g['resources'].get(resource,Decimal(0))+value
result=sorted(groups.values(),key=lambda g:-g['cost'])
(ROOT/'full_object_costs.json').write_text(json.dumps(result,default=str,ensure_ascii=False,indent=2),encoding='utf8')
for g in result:print(json.dumps(g,default=str,ensure_ascii=False))
print('TOTAL',sum((g['cost'] for g in result),Decimal(0)))
