"""Read-only budget check used before every paid GPU dispatch."""
import argparse,asyncio,json,subprocess,sys
from decimal import Decimal,ROUND_CEILING
from pathlib import Path
from datetime import datetime,timezone
from google.protobuf.timestamp_pb2 import Timestamp
from google.protobuf.json_format import MessageToDict
from modal.client import _Client
from modal_proto import api_pb2

async def main(seconds,reserve_job=None,profile='a100',bind_job=None,app_id=None):
    root=Path(__file__).parent;p=json.loads((root/'budget_policy.json').read_text());client=await _Client.from_env()
    start=Timestamp();start.FromJsonString(p['billing_period_start_utc'])
    result=MessageToDict(await client.stub.WorkspaceBillingSummary(api_pb2.WorkspaceBillingSummaryRequest(start_timestamp=start)),preserving_proto_field_name=True)
    D=Decimal;adjust=result.get('adjustments',{});breakdown=result.get('metered_cost_breakdown',{})
    assert D(result.get('billed_cost','0'))==0,'Paid billing is already positive; stop credit-only jobs.'
    assert D(adjust.get('Plan Cost','0'))==0,'Plan changed; do not assume Starter allowance.'
    a=abs(D(adjust.get('Credits','0')))
    b=D(result['metered_cost'])+sum((D(v) for k,v in adjust.items() if k!='Credits'),D(0))
    c=sum((D(v) for k,v in breakdown.items() if k not in ['Volumes','Network Egress']),D(0))
    api_consumed=max(a,b,c).quantize(D('.01'),rounding=ROUND_CEILING)
    ledger_path=root/'local_ledger.json';ledger=json.loads(ledger_path.read_text()) if ledger_path.exists() else {'baseline_consumption_upper_usd':str(api_consumed),'jobs':[]}
    if bind_job:
        assert app_id,'--app-id required to bind'
        found=[j for j in ledger['jobs'] if j['label']==bind_job];assert len(found)==1;found[0]['app_id']=app_id
    apps=json.loads(subprocess.check_output([sys.executable,'-X','utf8','-m','modal','app','list','--json'],text=True,encoding='utf8'))
    by_id={app['app_id']:app for app in apps}
    for job in ledger['jobs']:
        app=by_id.get(job.get('app_id'))
        if app and app['state']=='stopped' and app.get('stopped_at'):
            t0=datetime.fromisoformat(app['created_at']);t1=datetime.fromisoformat(app['stopped_at'])
            wall=max(0,(t1-t0).total_seconds())
            bound=((D(str(wall))+D(30))*D(job['rate_upper_usd_hour'])/D(3600)).quantize(D('.01'),rounding=ROUND_CEILING)
            job['wall_time_upper_usd']=str(min(bound,D(job['reserved_upper_usd'])));job['app_wall_seconds']=wall
            job['app_created_at']=app['created_at'];job['app_stopped_at']=app['stopped_at'];job['stopped_observed_at_utc']=datetime.now(timezone.utc).isoformat()
            job['settled_upper_usd']=job.get('verified_billing_upper_usd',job['wall_time_upper_usd'])
    local_bound=D(ledger['baseline_consumption_upper_usd'])+sum((D(j.get('settled_upper_usd',j['reserved_upper_usd'])) for j in ledger['jobs']),D(0))
    consumed=max(api_consumed,local_bound)
    available=max(D(0),D(p['credit_consumption_stop_usd'])-consumed)
    rate={'a100':D('3.70'),'a10':D('1.75'),'cpu':D('0.50')}[profile]
    rate_basis=None
    if seconds and profile=='a10':
        rates=MessageToDict(await client.stub.WorkspaceBillingRates(api_pb2.WorkspaceBillingRatesRequest()),preserving_proto_field_name=True)['rates']
        exact=D(rates['gpu_hour_cost_a10g'])+4*D(rates['cpu_hour_cost'])+32*D(rates['mem_gib_hour_cost'])
        rate=(exact*D('1.035')).quantize(D('.01'),rounding=ROUND_CEILING)
        rate_basis={'profile':'A10/A10G +4CPU +32GiB only; runtime GPU class asserted by runners','exact_declared_resource_usd_hour':str(exact),'margin_multiplier':'1.035','upper_usd_hour':str(rate)}
    worst=((D(seconds)+D(p['extra_startup_allowance_seconds']))*rate/D(3600)).quantize(D('.01'),rounding=ROUND_CEILING) if seconds else D(0)
    if seconds:assert not [app for app in apps if app['state']!='stopped' and int(app.get('tasks',0))>0],'Wait for current jobs to finish before next dispatch.'
    status={'time_utc':datetime.now(timezone.utc).isoformat(),'api_consumption_upper_usd':str(api_consumed),'local_consumption_upper_usd':str(local_bound),'consumption_upper_usd':str(consumed),'remaining_guarded_usd':str(available),'job_timeout_seconds':seconds,'resource_profile':profile,'worst_job_cost_usd':str(worst),'job_fits':worst<=available,'billing':result}
    if rate_basis:status['resource_rate_basis']=rate_basis
    (root/'latest_budget.json').write_text(json.dumps(status,indent=2)+'\n',encoding='utf8')
    with (root/'budget_history.jsonl').open('a',encoding='utf8') as f:f.write(json.dumps(status)+'\n')
    print(json.dumps({k:v for k,v in status.items() if k!='billing'},indent=2))
    assert worst<=available,'Next bounded job would exceed remaining credit allowance.'
    if reserve_job:
        assert seconds>0 and not any(j['label']==reserve_job for j in ledger['jobs']),'Unique nonempty reservation required'
        ledger['jobs'].append({'label':reserve_job,'timeout_seconds':seconds,'rate_upper_usd_hour':str(rate),'reserved_upper_usd':str(worst)})
    ledger_path.write_text(json.dumps(ledger,indent=2)+'\n',encoding='utf8')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--gpu-seconds',type=int,default=0);parser.add_argument('--profile',choices=['a100','a10','cpu'],default='a100');parser.add_argument('--reserve-job');parser.add_argument('--bind-job');parser.add_argument('--app-id');args=parser.parse_args();asyncio.run(main(args.gpu_seconds,args.reserve_job,args.profile,args.bind_job,args.app_id))
