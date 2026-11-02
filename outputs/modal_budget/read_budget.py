"""Read-only Modal account billing summary; never reads or prints credentials."""
import asyncio,json
from datetime import datetime,timezone
from pathlib import Path
from modal.client import _Client
from modal_proto import api_pb2
from google.protobuf.timestamp_pb2 import Timestamp
from google.protobuf.json_format import MessageToDict

async def main():
    root=Path(__file__).parent
    client=await _Client.from_env()
    start=Timestamp();start.FromDatetime(datetime(2026,10,1,tzinfo=timezone.utc))
    response=await client.stub.WorkspaceBillingSummary(api_pb2.WorkspaceBillingSummaryRequest(start_timestamp=start))
    result=MessageToDict(response,preserving_proto_field_name=True)
    (root/'billing_summary.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps(result,indent=2))
    rates=await client.stub.WorkspaceBillingRates(api_pb2.WorkspaceBillingRatesRequest())
    (root/'billing_rates.json').write_text(json.dumps(MessageToDict(rates,preserving_proto_field_name=True),indent=2)+'\n',encoding='utf8')
    print(rates.formatted[:5000])

if __name__=='__main__':asyncio.run(main())
