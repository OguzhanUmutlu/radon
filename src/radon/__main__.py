import json
import os
import platform
import shutil
import sys
from os import path
from time import sleep, time
from typing import Any

from .dp_ast import parse_str
from .transpiler import Transpiler
from .utils import VERSION_RADON, get_pack_format

# get the path that the file is running from
cwd = os.getcwd()

arg = sys.argv[1] if len(sys.argv) > 1 else "build"

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
    with open("./radon.json", "r") as file:
        res = json.loads(file.read())
        if "useLock" not in res:
            res["useLock"] = False
        return res


def listdir_recursive(pt):
    for root, _, files in os.walk(pt):
        for file in files:
            yield path.join(root, file)


def empty_dir_recursive(pt):
    if path.exists(pt) and path.isdir(pt):
        for f in os.listdir(pt):
            empty_dir_recursive(pathr(pt + "/" + f))
        if len(os.listdir(pt)) == 0:
            os.rmdir(pt)
            empty_dir_recursive(pathr(pt + "/../"))


def build():
    init()

    config = read_config()

    if not path.exists(config["main"]):
        return "The main file does not exist!"

    with open(config["main"], "r") as file:
        code = file.read()

    try:
        (statements, macros) = parse_str(code)
        transpiler = Transpiler(statements, macros, config["namespace"], config["format"], config["main"] + "/../")
    except SyntaxError as e:
        return str(e)
    except Exception as e:
        raise e

    out_folders = (
        config["outFolder"]
        if isinstance(config["outFolder"], list)
        else [config["outFolder"]]
    )

    lock = ""

    if config["useLock"] and path.exists(f"{cwd}/radon.lock"):
        with open(f"{cwd}/radon.lock", "r") as file:
            lock = file.read().strip("\n")

    rm_files = lock.split("\n") if lock else []

    for outFolder in out_folders:
        os.makedirs(outFolder, exist_ok=True)
        if config["useLock"]:
            for f in rm_files:
                f = f"{outFolder}/{f}"
                if path.exists(f) and path.isfile(f):
                    os.remove(f)
                dr = path.dirname(f)
                empty_dir_recursive(dr)
        else:
            shutil.rmtree(
                f"{outFolder}/data/{config['namespace']}/functions", ignore_errors=True
            )

        with open(outFolder + f"/pack.mcmeta", "w") as file:
            file.write(
                json.dumps(
                    {
                        "pack": {
                            "pack_format": config["format"],
                            "description": config["description"],
                        }
                    },
                    indent=4,
                )
            )

        os.makedirs(outFolder + "/data/minecraft/tags/functions", exist_ok=True)

        with open(outFolder + "/data/minecraft/tags/functions/load.json", "w") as file:
            file.write(
                json.dumps({"values": [f"{config['namespace']}:__load__"]}, indent=4)
            )

        if "tick" in transpiler.files:
            with open(
                    f"{outFolder}/data/minecraft/tags/functions/tick.json", "w"
            ) as file:
                file.write(
                    json.dumps(
                        {"values": [f"{config['namespace']}:__tick__"]}, indent=4
                    )
                )

    new_files = dict()
    for filename in transpiler.files:
        new_files[f"data/{config['namespace']}/functions/{filename}.mcfunction"] = (
            transpiler.files[filename]
        )

    for outFolder in out_folders:
        for pt in new_files:
            fname = pt
            pt = f"{outFolder}/{pt}"
            os.makedirs(pathr(pt + "/../"), exist_ok=True)
            with open(pt, "w") as file:
                file.write("\n".join(new_files[fname]))

    if config["useLock"]:
        with open(f"{cwd}/radon.lock", "w") as file:
            file.write("\n".join(new_files.keys()))


def init():
    if path.exists("./radon.json"):
        return
    print(f"{BLUE}No config file found, generating radon.json")

    main_file = "main.rn"

    for file in os.listdir("."):
        if file.endswith(".rn") and path.isfile("./" + file):
            main_file = file
            break

    pack_name = get_input(f"{CYAN}Name(Leave blank to cancel): {RESET}")

    if not pack_name:
        print(f"{RED}Cancelling...{RESET}")
        sys.exit(0)

    pack_namespace = get_input(f"{CYAN}Namespace(Leave blank to cancel): {RESET}")

    if not pack_namespace:
        print(f"{RED}Cancelling...{RESET}")
        sys.exit(0)

    pack_desc = get_input(f"{CYAN}Description: {RESET}")

    while True:
        pack_format = get_pack_format(
            get_input(f"{CYAN}Pack format or Minecraft version: {RESET}")
        )
        if pack_format is None:
            print(
                f"{RED}Invalid pack format or Minecraft version please try again.{RESET}"
            )
            continue
        break

    pack_main = get_input(f"{CYAN}Main file({main_file}): {RESET}")

    if not pack_main:
        pack_main = main_file

    pack_output_folder = get_input(f"{CYAN}Output folder(.): {RESET}")

    if not pack_output_folder:
        pack_output_folder = "."

    with open("./radon.json", "w") as file:
        file.write(
            json.dumps(
                {
                    "name": pack_name,
                    "namespace": pack_namespace,
                    "description": pack_desc,
                    "format": pack_format,
                    "main": pack_main,
                    "outFolder": pack_output_folder,
                    "useLock": False,
                },
                indent=4,
            )
        )

    if not path.exists(main_file):
        with open(main_file, "w") as file:
            file.write("print('Hello, world!')")

    print(f"{GREEN}Datapack's workplace is ready!{RESET}")
    build_for_watch()
    sys.exit(0)


def watch_snapshot():
    lock = ""
    if path.exists(f"{cwd}/radon.lock"):
        with open(f"{cwd}/radon.lock", "r") as file:
            lock = file.read().strip("\n")

    lock = lock.split("\n") if lock else []
    files = []
    files += map(
        lambda x: path.join("./", x),
        filter(
            lambda x: x.endswith(".rn") or x == path.join(".", "radon.json"),
            listdir_recursive("."),
        ),
    )
    return {f: path.getmtime(f) for f in files}


def build_for_watch():
    start = time()
    built = build()
    if isinstance(built, str):
        print(built)
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
    c = """a = [1, 2, 3, 4]

a[0] = 10

"""
    global files_snapshot
    print(f"{YELLOW}Radon v{VERSION_RADON}{RESET}")
    print("")
    print(f"{CYAN}Current Directory | {cwd}{RESET}")
    print("")

    init()

    if arg == "build":
        start = time()
        built = build()
        if isinstance(built, str):
            print(built)
            sys.exit(1)

        took = time() - start

        print(f"{GREEN}Datapack has been built!{GRAY} ({took:.5f}s){RESET}")
        sys.exit(0)

    if arg != "watch":
        print(
            f"{RED}Invalid argument! Usage: {CYAN}radon [build|watch]{RED} or just {CYAN}radon{RESET} to build"
        )
        sys.exit(1)

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
