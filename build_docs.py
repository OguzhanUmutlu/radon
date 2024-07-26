from os import system, mkdir
from shutil import copytree, rmtree

system("cd docs-src && npx vitepress build")
rmtree("./docs")
mkdir("./docs")
copytree("./docs-src/.vitepress/dist", "./docs", dirs_exist_ok=True)
# rmtree("./docs-src/.vitepress/dist")
copytree("./docs-src/assets", "./docs/assets", dirs_exist_ok=True)
copytree("./docs-src/css", "./docs/css", dirs_exist_ok=True)

