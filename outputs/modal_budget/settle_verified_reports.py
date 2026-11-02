"""Replace only closed-job estimates with official closed-hour app costs plus buffer."""
from pathlib import Path
from decimal import Decimal,ROUND_CEILING
import json,hashlib,shutil
ROOT=Path(__file__).parent;D=Decimal;path=ROOT/'local_ledger.json';ledger=json.loads(path.read_text());audit=json.loads((ROOT/'closed_app_cost_audit.json').read_text());by_label={r['label']:r for r in audit['jobs']};changes=[]
backup=ROOT/'local_ledger.before_closed_bill_settlement.json'
if not backup.exists():shutil.copy2(path,backup)
for job in ledger['jobs']:
 row=by_label[job['label']]
 if not row['eligible_complete_hourly_intervals'] or not row['n_report_rows'] or not row['resource_total_matches_cost'] or D(row['actual_reported_cost_usd'])<=0:continue
 is_gpu=D(job['rate_upper_usd_hour'])>D('.50')
 if is_gpu and not any(k.startswith(('A10','A100','H100','L4','T4')) and D(v)>0 for k,v in row['reported_resources'].items()):continue
 reported=max(D(row['actual_reported_cost_usd']),D(job.get('max_closed_report_cost_usd','0')));buffer=D('.02') if is_gpu else D('.01');upper=(reported+buffer).quantize(D('.01'),rounding=ROUND_CEILING)
 prior=job.get('settled_upper_usd',job['reserved_upper_usd']);job['max_closed_report_cost_usd']=str(reported);job['verified_billing_upper_usd']=str(upper);job['settled_upper_usd']=str(upper);job['verified_report_cutoff_utc']=audit['report_cutoff_UTC'];job['verified_report_source_file']=audit.get('source_report','closed_interval_billing_report.json');job['verified_report_source_sha256']=hashlib.sha256((ROOT/job['verified_report_source_file']).read_bytes()).hexdigest();job['settlement_source']='official per-app report, completed hourly intervals, stopped job, rounded cost +buffer';job['app_stopped_at']=row['app_stopped_at']
 changes.append({'label':job['label'],'old_upper_usd':prior,'official_closed_cost_usd':str(reported),'buffer_usd':str(buffer),'new_upper_usd':str(upper)})
path.write_text(json.dumps(ledger,indent=2)+'\n',encoding='utf8');(ROOT/'verified_settlement_changes.json').write_text(json.dumps({'report_cutoff':audit['report_cutoff_UTC'],'changes':changes,'global_stop_29p90_and_billed_zero_checks_unchanged':True},indent=2),encoding='utf8');print(json.dumps(changes,indent=2))
