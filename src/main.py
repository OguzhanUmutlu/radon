import shutil
from transpiler import Transpiler
from dp_ast import parse_str
from os import path, makedirs, listdir, system
import sys
import json
from time import sleep
import platform

if len(sys.argv) != 2:
    print(f"Usage: python3 {sys.argv[0]} init/build/watch")
    sys.exit(1)


arg = sys.argv[1]


def clear():
    if platform.system() == "Windows":
        system("cls")
    else:
        system("clear")


def read_config():
    with open("./radon.json", "r") as file:
        return json.loads(file.read())


def build():
    if not path.exists("./radon.json"):
        return "The radon.json file does not exist!"

    config = read_config()

    if not path.exists(config["main"]):
        return "The main file does not exist!"

    with open(config["main"], "r") as file:
        code = file.read()

    transpiler = Transpiler()
    transpiler.pack_name = config["name"]
    transpiler.pack_desc = config["description"]
    transpiler.pack_format = config["format"]
    transpiler.main_dir = config["main"] + "/../"

    try:
        (statements, macros) = parse_str(code)

        transpiler.transpile(statements, macros)
    except SyntaxError as e:
        return str(e)

    outFolders = (
        config["outFolder"]
        if isinstance(config["outFolder"], list)
        else [config["outFolder"]]
    )

    if config["cleanFilesInBuilds"]:
        for outFolder in outFolders:
            shutil.rmtree(outFolder)

    for outFolder in outFolders:
        makedirs(outFolder, exist_ok=True)

    for filename in transpiler.files:
        # f"/data/{pack_name}/functions"
        for outFolder in outFolders:
            pt = outFolder + f"/" + filename + ".mcfunction"
            makedirs(path.realpath(pt + "/../"), exist_ok=True)
            with open(pt, "w") as file:
                file.write("\n".join(transpiler.files[filename]))


def init():
    if path.exists("./radon.json"):
        print("The radon.json file already exists!")
        sys.exit(1)

    if not path.exists("./src"):
        makedirs("./src")

    main_file = "main.rn"

    for file in listdir("./src"):
        if file.endswith(".rn") and path.isfile("./src/" + file):
            main_file = file
            break

    with open("./radon.json", "w") as file:
        file.write(
            json.dumps(
                {
                    "name": "mypack",
                    "description": "This is a datapack!",
                    "main": "./src/" + main_file,
                    "outFolder": "./build",
                    "cleanFilesInBuilds": False,
                    "format": 10,
                },
                indent=4,
            )
        )

    if not path.exists("./src/" + main_file):
        with open("./src/" + main_file, "w") as file:
            file.write("say Hello, world!")

    print("Your project has been initialized!")
    sys.exit(0)


class FileWatcher:
    def __init__(self, directory_to_watch):
        self.directory_to_watch = directory_to_watch
        self.files_snapshot = self.snapshot_directory()

    def snapshot_directory(self):
        files = []
        for dir in self.directory_to_watch:
            files += map(lambda x: path.join(dir, x), listdir(dir))
        return {f: path.getmtime(f) for f in files}

    def run(self):
        joined = ", ".join(self.directory_to_watch)
        print(f"Watching directories: {joined}")
        print(f"Press CTRL + C to stop watching")
        self.build()
        try:
            while True:
                sleep(0.3)
                self.check_for_changes()
        except KeyboardInterrupt:
            print("Stopped watching")

    def build(self):
        built = build()
        if isinstance(built, str):
            print(built)
        else:
            print("Datapack has been built")

    def check_for_changes(self):
        new_snapshot = self.snapshot_directory()
        old_snapshot = self.files_snapshot

        if new_snapshot == old_snapshot:
            return

        for file in new_snapshot:
            if file not in old_snapshot:
                print(f"File created: {path.realpath(file)}")
            elif new_snapshot[file] != old_snapshot[file]:
                print(f"File modified: {path.realpath(file)}")

        for file in old_snapshot:
            if file not in new_snapshot:
                print(f"File deleted: {path.realpath(file)}")

        self.build()

        self.files_snapshot = new_snapshot


if arg == "init":
    init()
    sys.exit(0)

if arg == "build":
    built = build()
    if isinstance(built, str):
        print(built)
        sys.exit(1)

    print("The datapack has been successfully built!")
    sys.exit(0)

if arg == "watch":
    watcher = FileWatcher(["./src", "./"])
    watcher.run()
    sys.exit(0)


'''shutil.rmtree(build_dir, ignore_errors=True)
makedirs(build_dir, exist_ok=True)

with open(build_dir + f"/pack.mcmeta", "w") as file:
    file.write(
        """{
    "pack": {
        "pack_format": %pack_format,
        "description": "%pack_desc"
    }
}""".replace(
            "%pack_format", str(pack_format)
        ).replace(
            "%pack_desc", pack_desc
        )
    )

makedirs(build_dir + "/data/minecraft/tags/functions", exist_ok=True)

with open(build_dir + "/data/minecraft/tags/functions/load.json", "w") as file:
    file.write(
        """{
    "values": [
        "%pack_name:__load__"
    ]
}""".replace(
            "%pack_name", pack_name
        )
    )

if "tick" in transpiler.functions:
    with open(build_dir + "/data/minecraft/tags/functions/tick.json", "w") as file:
        file.write(
            """{
        "values": [
            "%pack_name:tick"
        ]
    }""".replace(
                "%pack_name", pack_name
            )
        )'''
