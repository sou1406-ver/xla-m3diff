"""Read official per-app billing for completed hourly intervals; no billing changes."""
from pathlib import Path
from datetime import datetime,timezone
from decimal import Decimal
import json,subprocess,sys,dataclasses
import modal
ROOT=Path(__file__).parent
ledger=json.loads((ROOT/'local_ledger.json').read_text());apps=json.loads(subprocess.check_output([sys.executable,'-X','utf8','-m','modal','app','list','--json'],text=True,encoding='utf8'));by_id={r['app_id']:r for r in apps}
created=[datetime.fromisoformat(by_id[j['app_id']]['created_at']) for j in ledger['jobs'] if j.get('app_id') in by_id]
start=min(created).astimezone(timezone.utc).replace(minute=0,second=0,microsecond=0);cutoff=datetime.now(timezone.utc).replace(minute=0,second=0,microsecond=0)
rows=modal.Workspace.from_context().billing.report(start=start,end=cutoff,resolution='h')
data=[dataclasses.asdict(r) for r in rows];body=json.dumps({'start':start,'end':cutoff,'resolution':'h','items':data},default=str,indent=2);(ROOT/'closed_interval_billing_report.json').write_text(body,encoding='utf8')
archive=ROOT/'billing_reports';archive.mkdir(exist_ok=True);source=archive/('report_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'.json');source.write_text(body,encoding='utf8')
audit=[]
for job in ledger['jobs']:
 app=by_id.get(job.get('app_id'));selected=[r for r in rows if r.object_id==job.get('app_id')];resources={}
 for row in selected:
  for name,value in row.cost_by_resource.items():resources[name]=resources.get(name,Decimal(0))+value
 cost=sum((r.cost for r in selected),Decimal(0));stopped=app.get('stopped_at') if app else job.get('app_stopped_at');proof='Modal app stopped timestamp'
 if not stopped and job['label']=='precision_comparison' and 'app_wall_seconds' in job:
  success=json.loads((ROOT.parent/'precision_audit/comparison_results/SUCCESS.json').read_text());assert success['same_checkpoint'] and success['n_generations']==216
  stopped=datetime.fromtimestamp(success['time'],timezone.utc).isoformat();proof='Saved completion metadata plus previously observed stopped ledger; app no longer retained in recent app list'
 eligible=bool(stopped and datetime.fromisoformat(stopped)<=cutoff and (not app or app['state']=='stopped'))
 audit.append({'label':job['label'],'app_id':job.get('app_id'),'eligible_complete_hourly_intervals':eligible,'n_report_rows':len(selected),'actual_reported_cost_usd':str(cost),'reported_resources':{k:str(v) for k,v in resources.items()},'resource_total_matches_cost':abs(sum(resources.values(),Decimal(0))-cost)<Decimal('.000001'),'app_stopped_at':stopped,'completion_evidence':proof})
result={'report_cutoff_UTC':cutoff.isoformat(),'resolution':'h','source_report':str(source.relative_to(ROOT)),'jobs':audit,'no_ledger_modified':True};(ROOT/'closed_app_cost_audit.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result,indent=2))
