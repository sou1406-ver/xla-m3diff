"""Local read-only owner-SDK poll; writes proof only after old app has0tasks.

No GPU calls, cancellation, scoring, credential export or cap changes.
"""
import json,time,subprocess,sys
from pathlib import Path
from datetime import datetime,timezone
import modal

P=Path(__file__).parent/'resume1020_v1'
REMOTE='mbr_pilot_20261103/resume1020_v1/'
APP='ap-2LLzTT9FpCW7OGxuFpawMc'

def main():
 v=modal.Volume.from_name('m3diff');ad=json.loads((P/'ADMISSION_PHASE2.json').read_text());end=ad['absolute_gpu_deadline_unix']
 while time.time()<end-120:
  try:
   try:
    proof=json.loads(b''.join(v.read_file(REMOTE+'PHASE1_RELEASE_APPROVED.json')))
    assert proof['old_app_id']==APP and proof['old_app_tasks']==[]
    print('ALREADY_RELEASED',json.dumps(proof),flush=True);return
   except (FileNotFoundError,modal.exception.NotFoundError):pass
   try:
    data=b''.join(v.read_file(REMOTE+'PIPELINE_DONE.json'));done=json.loads(data)
   except (FileNotFoundError,modal.exception.NotFoundError):done=None
   if done:
    cli=subprocess.run([sys.executable,'-m','modal','container','list','--app-id',APP,'--json'],capture_output=True,text=True,timeout=30,check=True)
    tasks=json.loads(cli.stdout)
    if not tasks:
     proof={'checked_utc':datetime.now(timezone.utc).isoformat(),'old_app_id':APP,'old_app_tasks':[],'phase1_terminal_status':done.get('status'),'provider_source':'OwnerSDK modal container list --app-id exactID --json','no_GPU_started_by_watcher':True}
     (P/'PHASE1_RELEASE_APPROVED.json').write_text(json.dumps(proof,indent=2))
     with v.batch_upload(force=False) as batch:batch.put_file(P/'PHASE1_RELEASE_APPROVED.json',REMOTE+'PHASE1_RELEASE_APPROVED.json')
     print(json.dumps(proof),flush=True);return
   (P/'LOCAL_RELEASE_WATCH.json').write_text(json.dumps({'checked_utc':datetime.now(timezone.utc).isoformat(),'status':'WAITING_PHASE1_END_AND_PROVIDER_ZERO_TASKS','GPU_calls':0}))
  except Exception as exc:print('READ_ONLY_POLL_ERROR',type(exc).__name__,flush=True)
  time.sleep(30)
 print('STOP_NO_RELEASE_BEFORE_COMBINED_DEADLINE',flush=True)

if __name__=='__main__':main()
