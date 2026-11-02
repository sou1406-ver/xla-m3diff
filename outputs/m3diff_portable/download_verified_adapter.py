"""Sequential export download; replace target only after SHA256 and ZIP CRC pass."""
import asyncio,hashlib,json,zipfile
from pathlib import Path
import modal
ROOT=Path(__file__).parent;target=ROOT/'model/m3diff-mixed-lora/adapter_model.bin';temp=target.with_name(target.name+'.verified-download.tmp')
expected='6b8d81729b03f83e9c03de9a78fb1aa895a47088c32c4435115ac39b77a1fb5f'
async def main():
 volume=modal.Volume.from_name('m3diff');h=hashlib.sha256();size=0
 with temp.open('wb') as f:
  async for chunk in volume.read_file.aio('invariance_ablation_v1/m3diff-mixed-objective-lora/adapter_model.bin'):
   f.write(chunk);h.update(chunk);size+=len(chunk)
 got=h.hexdigest();assert got==expected,(got,expected,size)
 with zipfile.ZipFile(temp) as z:assert z.testzip() is None,'Torch archive CRC failed'
 temp.replace(target)
 result={'bytes':size,'sha256':got,'matches_GPU_checkpoint':True,'torch_zip_CRC_all_members_pass':True,'sequential_download':True}
 (ROOT/'ADAPTER_FILE_CHECK.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result))
if __name__=='__main__':asyncio.run(main())
