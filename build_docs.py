from os import system, mkdir
from shutil import copytree, rmtree

system("cd docs && npx vitepress build")
rmtree("./docs")
mkdir("./docs")
copytree("docs/.vitepress/dist", "./docs", dirs_exist_ok=True)
# rmtree("./docs/.vitepress/dist")
copytree("docs/public/assets", "docs/public/assets", dirs_exist_ok=True)
copytree("docs/css", "./docs/css", dirs_exist_ok=True)

