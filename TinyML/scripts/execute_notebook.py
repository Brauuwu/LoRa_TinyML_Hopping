import os
import sys
import time
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

notebook_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../LoRa_TinyML_Pipeline.ipynb"))
run_dir = os.path.dirname(notebook_path)

print(f"[*] Loading notebook: {notebook_path}")
with open(notebook_path, "r", encoding="utf-8") as f:
    nb = nbformat.read(f, as_version=4)

ep = ExecutePreprocessor(timeout=1200, kernel_name='iot_ml')

t0 = time.time()
print(f"[*] Executing {len(nb.cells)} cells with kernel 'iot_ml' in working dir: {run_dir} ...")
try:
    ep.preprocess(nb, {'metadata': {'path': run_dir}})
    elapsed = time.time() - t0
    print(f"[OK] Successfully executed all cells in {elapsed:.1f}s ({elapsed/60:.2f} min)!")
except Exception as e:
    print(f"[ERROR] Execution error: {e}")
    raise e
finally:
    with open(notebook_path, "w", encoding="utf-8") as f:
        nbformat.write(nb, f)
    print(f"[OK] Saved executed notebook with all outputs to: {notebook_path}")

