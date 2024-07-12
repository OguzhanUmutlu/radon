import os
import shutil
from src.utils import VERSION_RADON

cwd = os.path.dirname(os.path.abspath(__file__))

shutil.rmtree(cwd + "/src/__pycache__", ignore_errors=True)
shutil.rmtree(cwd + "/src/builtin/__pycache__", ignore_errors=True)
shutil.make_archive(cwd + "/web/radon", "zip", cwd + "/src")
with open("./web/radon_version.js", "w") as f:
    f.write(f"const RADON_VERSION = '{VERSION_RADON}';")
