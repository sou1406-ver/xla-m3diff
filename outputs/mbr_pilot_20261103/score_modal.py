from pathlib import Path
import modal
HERE=Path(__file__).parent;v=modal.Volume.from_name('m3diff');app=modal.App('m3diff-mbr20-offline-score')
image=modal.Image.debian_slim(python_version='3.10').apt_install('default-jre-headless').pip_install('numpy<2','pycocoevalcap')
for n in ['score20_cpu.py','utility.py']:image=image.add_local_file(str(HERE/n),'/root/'+n,copy=True)
@app.function(image=image,cpu=(4,4),memory=(8192,8192),timeout=120,retries=0,scaledown_window=2,volumes={'/mnt/m3diff':v})
def score():
 import runpy
 try:runpy.run_path('/root/score20_cpu.py',run_name='__main__')
 finally:v.commit()
@app.local_entrypoint()
def main():score.remote()
