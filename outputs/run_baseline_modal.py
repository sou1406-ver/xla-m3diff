"""Run the adjacent baseline notebook on one Modal A10 GPU.

Start: modal run --detach run_baseline_modal.py
Download: modal volume get m3diff baseline_reproduction_v1/m3diff_baseline_results.zip .
"""
from pathlib import Path
import modal

NOTEBOOK = Path(__file__).with_name('m3diff-baseline-full.ipynb')
if not NOTEBOOK.is_file():
    raise FileNotFoundError(f'Keep the notebook beside this script: {NOTEBOOK}')

app = modal.App('m3diff-baseline-reproduction')
volume = modal.Volume.from_name('m3diff', create_if_missing=True)
image = (
    modal.Image.debian_slim(python_version='3.12')
    .apt_install('git', 'default-jre-headless')
    .pip_install('uv', 'nbformat', 'nbclient', 'ipykernel')
    .add_local_file(str(NOTEBOOK), '/root/m3diff-baseline-full.ipynb', copy=True)
)


@app.function(image=image, gpu='A10', cpu=4, memory=32768,
              timeout=24 * 60 * 60, volumes={'/mnt/m3diff': volume})
def baseline():
    import nbformat
    from nbclient import NotebookClient

    out = Path('/mnt/m3diff/baseline_reproduction_v1')
    out.mkdir(parents=True, exist_ok=True)
    nb = nbformat.read('/root/m3diff-baseline-full.ipynb', as_version=4)

    def cell_done(cell, cell_index, **kwargs):
        # Persist the executed notebook after every cell, including saved outputs.
        nbformat.write(nb, out / 'baseline_executed.ipynb')
        volume.commit()
        print(f'Completed cell {cell_index + 1}/{len(nb.cells)}', flush=True)

    client = NotebookClient(nb, timeout=None, kernel_name='python3',
                            allow_errors=False, on_cell_executed=cell_done,
                            resources={'metadata': {'path': '/root'}})
    try:
        client.execute()
    finally:
        nbformat.write(nb, out / 'baseline_executed.ipynb')
        volume.commit()
    print('DONE. Results: Volume m3diff / baseline_reproduction_v1', flush=True)


@app.local_entrypoint()
def main():
    baseline.remote()
