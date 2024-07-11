import os
import shutil

cwd = os.path.dirname(os.path.abspath(__file__))

shutil.rmtree(cwd + "/src/__pycache__", ignore_errors=True)
shutil.rmtree(cwd + "/src/builtin/__pycache__", ignore_errors=True)
shutil.make_archive(cwd + "/web/radon", 'zip', cwd + "/src")
