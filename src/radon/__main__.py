import json
import os
import platform
import shutil
import sys
from argparse import ArgumentParser
from os import path
from time import sleep, time
from typing import Any

from .dp_ast import parse_str
from .transpiler import Transpiler
from .utils import VERSION_RADON, get_pack_format

BLACK = "\x1b[30m"
RED = "\x1b[31m"
GREEN = "\x1b[32m"
YELLOW = "\x1b[33m"
BLUE = "\x1b[34m"
MAGENTA = "\x1b[35m"
CYAN = "\x1b[36m"
WHITE = "\x1b[37m"
RESET = "\x1b[0m"
GRAY = "\x1b[90m"


# Usage: radon [build|watch] (-d="cwd")

class RadonArgumentParser(ArgumentParser):
    def __init__(self):
        super().__init__()
        self.add_argument("command", nargs="?", default="build", choices=["build", "watch"],
                          help="The command to run (build or watch)")
        self.add_argument("-d", default=os.getcwd(), type=str, help="sets the working directory")
        self.add_argument("-b", action="store_true", help="toggles debug mode")
        self.prog = "radon"

    def error(self, message):
        sys.stderr.write(RED)
        self.print_help(sys.stderr)
        sys.stderr.write(f"\nError: {message}\n")
        sys.stderr.write(RESET)
        sys.exit(2)


parser = RadonArgumentParser()
args = parser.parse_args()
cwd_list = args.d.split("|")
original_cwd = os.getcwd()


# real path
def pathr(pt):
    return path.realpath(pt)


def get_input(inp):
    try:
        return input(inp).strip()
    except KeyboardInterrupt:
        print(f"\n{RED}Cancelling...{RESET}")
        sys.exit(0)


def clear():
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")


def read_config():
    with open(f"./radon.json", "r") as file:
        res = json.loads(file.read())
        if "useLock" not in res:
            res["useLock"] = False
        return res


def listdir_recursive(pt):
    for root, _, files in os.walk(pt):
        for file in files:
            yield pathr(root + "/" + file)


def empty_dir_recursive(pt):
    if path.exists(pt) and path.isdir(pt):
        for f in os.listdir(pt):
            empty_dir_recursive(pathr(pt + "/" + f))
        if len(os.listdir(pt)) == 0:
            os.rmdir(pt)
            empty_dir_recursive(pathr(pt + "/../"))


def build_dir():
    init_dir()

    config = read_config()

    if not path.exists(config["main"]):
        return "The main file does not exist: " + config["main"] + ", cwd: " + os.getcwd()

    with open(pathr(config["main"]), "r") as file:
        code = file.read()

    try:
        (statements, macros) = parse_str(code)
        transpiler = Transpiler(
            statements=statements,
            macros=macros,
            pack_namespace=config["namespace"],
            pack_description=config["description"],
            pack_format=get_pack_format(config["format"]),
            main_dir=config["main"] + "/../",
            main_file_path=config["main"],
            debug_mode=args.b)
    except SyntaxError as e:
        return str(e)
    except Exception as e:
        raise e

    dp_files = transpiler.get_datapack_files()

    out_folders = (
        config["outFolder"]
        if isinstance(config["outFolder"], list)
        else [config["outFolder"]]
    )

    lock = ""

    if config["useLock"] and path.exists(f"./radon.lock"):
        with open(f"./radon.lock", "r") as file:
            lock = file.read().strip("\n")

    rm_files = lock.split("\n") if lock else []

    for out_folder in out_folders:
        if config["useLock"]:
            for f in rm_files:
                f = f"{out_folder}/{f}"
                if not path.exists(f):
                    continue
                if path.isfile(f):
                    os.remove(f)
                dr = path.dirname(f)
                empty_dir_recursive(dr)
        else:
            shutil.rmtree(out_folder + "/data", ignore_errors=True)
            if path.exists(out_folder + "/pack.mcmeta"):
                os.remove(out_folder + "/pack.mcmeta")
            os.makedirs(out_folder + "/data", exist_ok=True)

    for out_folder in out_folders:
        if "data" in config and path.exists(config["data"]) and path.isdir(config["data"]):
            shutil.copytree(config["data"], out_folder + "/data", dirs_exist_ok=True)
        for pt in dp_files:
            file_name = pt
            pt = f"{out_folder}/{pt}"
            os.makedirs(pathr(pt + "/../"), exist_ok=True)
            with open(pt, "w") as file:
                file.write(dp_files[file_name])

    if config["useLock"]:
        with open(f"./radon.lock", "w") as file:
            file.write("\n".join(dp_files.keys()))


def build():
    res = []
    for cwd in cwd_list:
        os.chdir(original_cwd)
        if not path.exists(cwd):
            print(f"{RED}Directory {cwd} does not exist!{RESET}")
            exit(1)
        os.chdir(cwd)
        s = build_dir()
        if isinstance(s, str):
            res.append(s)
    return "\n".join(res) if len(res) > 0 else None


def init_dir():
    if path.exists(f"./radon.json"):
        return
    print(f"{BLUE}No config file found, generating radon.json")

    pack_namespace = None
    while not pack_namespace:
        pack_namespace = get_input(f"{CYAN}*Namespace: {RESET}")

    if not pack_namespace:
        print(f"{RED}Cancelling...{RESET}")
        sys.exit(0)

    pack_desc = get_input(f"{CYAN}Description: {RESET}")

    pack_format = None

    while not get_pack_format(pack_format):
        pack_format = get_input(f"{CYAN}*Pack format or Minecraft version: {RESET}")

    pack_main = get_input(f"{CYAN}Main file(src/main.rn): {RESET}") or "src/main.rn"
    pack_data = get_input(f"{CYAN}Data folder(src/data): {RESET}") or "src/data"
    pack_output_folder = get_input(f"{CYAN}Output folder(.): {RESET}") or "."

    with open("./radon.json", "w") as file:
        file.write(
            json.dumps(
                {
                    "namespace": pack_namespace,
                    "description": pack_desc,
                    "format": pack_format,
                    "main": pack_main,
                    "data": pack_data,
                    "outFolder": pack_output_folder,
                    "useLock": False,
                },
                indent=2,
            )
        )

    if not path.exists(pack_main):
        os.makedirs(path.dirname(pack_main), exist_ok=True)
        with open(pack_main, "w") as file:
            file.write("print('Hello, world!')")
    if not path.exists(pack_data):
        os.makedirs(pack_data, exist_ok=True)

    print(f"{GREEN}Datapack's workplace is ready!{RESET}")
    build_for_watch()
    sys.exit(0)


def init():
    for cwd in cwd_list:
        os.chdir(original_cwd)
        if not path.exists(cwd):
            print(f"{RED}Directory {cwd} does not exist!{RESET}")
            exit(1)
        os.chdir(cwd)
        init_dir()


def watch_snapshot():
    files = []
    files += map(
        lambda x: path.join("./", x),
        list(listdir_recursive("./src")) + ["radon.json"]
    )
    return {f: path.getmtime(f) for f in files}


def build_for_watch():
    start = time()
    built = build()
    if isinstance(built, str):
        print(RED + built + RESET)
    else:
        took = time() - start
        print(f"{GREEN}Datapack has been built!{GRAY} ({took:.5f}s){RESET}")


files_snapshot: Any = None


def check_for_changes():
    global files_snapshot
    new_snapshot = watch_snapshot()
    old_snapshot = files_snapshot

    if new_snapshot == old_snapshot:
        return

    for file in new_snapshot:
        if file not in old_snapshot:
            print(f"{GRAY}File created: {path.realpath(file)}{RESET}")
        elif new_snapshot[file] != old_snapshot[file]:
            print(f"{GRAY}File modified: {path.realpath(file)}{RESET}")

    for file in old_snapshot:
        if file not in new_snapshot:
            print(f"{GRAY}File deleted: {path.realpath(file)}{RESET}")

    build_for_watch()

    files_snapshot = new_snapshot


def main():
    global files_snapshot
    print(f"{YELLOW}Radon v{VERSION_RADON}{RESET}")
    print("")
    print(f"{CYAN}Current Directory | {" | ".join(cwd_list)}{RESET}")
    print("")

    init()

    if args.command == "build":
        start = time()
        built = build()
        if isinstance(built, str):
            print(RED + built + RESET)
            sys.exit(1)

        took = time() - start

        print(f"{GREEN}Datapack has been built!{GRAY} ({took:.5f}s){RESET}")
        sys.exit(0)

    files_snapshot = watch_snapshot()

    print(f"{GREEN}Watching files...{RESET}")
    print(f"{CYAN}Press CTRL + C to stop watching{RESET}")
    build_for_watch()
    try:
        while True:
            sleep(0.3)
            check_for_changes()
    except KeyboardInterrupt:
        print(f"{RED}Stopped watching{RESET}")

    sys.exit(0)


if __name__ == "__main__":
    main()
