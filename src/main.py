from transpiler import transpile_str
from argparse import ArgumentParser
from os import path, makedirs

parser = ArgumentParser(description="CLI")
parser.add_argument(
    "file",
    help="Path of the file to transpile",
)

parser.add_argument(
    "-o",
    type=str,
    help="Folder path of the build",
)

parser.add_argument(
    "-n",
    type=str,
    help="Name of the datapack",
)

parser.add_argument(
    "-d",
    type=str,
    help="Description of the datapack",
)

parser.add_argument(
    "-f",
    type=str,
    help="Format of the datapack",
)

args = parser.parse_args()

build_dir = path.realpath(args.o or (args.file + "/../build"))

file = open(args.file, "r")
code = file.read()
file.close()

transpiler = transpile_str(code)

if args.n:
    transpiler.pack_name = args.n
if args.d:
    transpiler.pack_desc = args.d
if args.f:
    transpiler.pack_format = args.f

pack_name = transpiler.pack_name
pack_desc = transpiler.pack_desc
pack_format = transpiler.pack_format

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

# f"/data/{pack_name}/functions"
makedirs(build_dir + f"/", exist_ok=True)

for filename in transpiler.files:
    # f"/data/{pack_name}/functions"
    pt = build_dir + f"/" + filename + ".mcfunction"
    makedirs(path.realpath(pt + "/../"), exist_ok=True)
    with open(pt, "w") as file:
        file.write(
            "\n".join(transpiler.files[filename]).replace("$PACK_NAME$", pack_name)
        )
