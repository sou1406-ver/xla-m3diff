"""November credit-only guard; keeps October experiment accounting untouched."""
import argparse, asyncio, json, math
from datetime import datetime, timezone
from decimal import Decimal, ROUND_CEILING
from pathlib import Path
from modal.client import _Client
from modal_proto import api_pb2
from google.protobuf.timestamp_pb2 import Timestamp
from google.protobuf.json_format import MessageToDict

HERE = Path(__file__).parent

async def main(args):
    client = await _Client.from_env()
    start = Timestamp(); start.FromDatetime(datetime(2026, 11, 1, tzinfo=timezone.utc))
    result = MessageToDict(await client.stub.WorkspaceBillingSummary(
        api_pb2.WorkspaceBillingSummaryRequest(start_timestamp=start)), preserving_proto_field_name=True)
    rates = MessageToDict(await client.stub.WorkspaceBillingRates(api_pb2.WorkspaceBillingRatesRequest()),
                          preserving_proto_field_name=True)
    D = Decimal; adjust = result.get('adjustments', {}); breakdown = result.get('metered_cost_breakdown', {})
    assert D(result.get('billed_cost', '0')) == 0, 'Positive billed cost: stop credit-only dispatch.'
    assert D(adjust.get('Plan Cost', '0')) == 0, 'Plan changed: stop.'
    consumed = max(abs(D(adjust.get('Credits', '0'))), D(result.get('metered_cost', '0')) +
                   sum((D(v) for k, v in adjust.items() if k != 'Credits'), D(0)),
                   sum((D(v) for k, v in breakdown.items() if k not in ('Volumes', 'Network Egress')), D(0)))
    ledger_path = HERE / 'budget_ledger.json'
    ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else {
        'period_start': '2026-11-01', 'authorization': 'User renewed $30 credit; one final v2 round,7USD maximum, no purchases.',
        'initial_consumption': str(consumed), 'jobs': []}
    local = D(ledger['initial_consumption']) + sum((D(j.get('settled', j['reservation'])) for j in ledger['jobs']), D(0))
    available = D('29.50') - max(consumed, local)
    r = rates['rates']; cpu, gib = (8, 64) if args.profile == 'a100' else ((4, 32) if args.profile == 'a10' else (4, 8))
    # Modal can supply an80GB physical A100 for a40GB request. Reserve the higher
    # listed rate regardless of whether an automatic upgrade is actually billed.
    gpu = max(D(r['gpu_hour_cost_a100_40gb']),D(r['gpu_hour_cost_a100_80gb'])) if args.profile == 'a100' else D(r['gpu_hour_cost_a10g']) if args.profile == 'a10' else D(0)
    rate = ((gpu + cpu * D(r['cpu_hour_cost']) + gib * D(r['mem_gib_hour_cost'])) * D('1.10')).quantize(D('.01'), rounding=ROUND_CEILING)
    worst = ((D(args.seconds + 180) * rate / 3600).quantize(D('.01'), rounding=ROUND_CEILING)) if args.seconds else D(0)
    report = {'time_utc': datetime.now(timezone.utc).isoformat(), 'billing': result,
              'api_consumption': str(consumed), 'local_upper': str(local), 'remaining_guarded': str(available),
              'profile': args.profile, 'rate_upper_hour': str(rate), 'reservation': str(worst), 'fits': worst <= available}
    (HERE / 'latest_budget.json').write_text(json.dumps(report, indent=2))
    (HERE / 'rates.json').write_text(json.dumps(rates, indent=2))
    print(json.dumps(report, indent=2))
    assert worst <= available, 'Job exceeds remaining credit.'
    if args.reserve:
        assert args.seconds and not any(j['label'] == args.reserve for j in ledger['jobs'])
        ledger['jobs'].append({'label': args.reserve, 'reservation': str(worst), 'rate': str(rate),
                               'seconds': args.seconds, 'profile': args.profile})
    ledger_path.write_text(json.dumps(ledger, indent=2))

if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--seconds', type=int, default=0)
    p.add_argument('--profile', choices=['cpu', 'a10', 'a100'], default='cpu'); p.add_argument('--reserve')
    asyncio.run(main(p.parse_args()))
