# Config

The Radon config can let you customize the behavior of the compiler. The config is stored in `radon.json` in the root of
the project directory.

The default config is:

```json
{
  "namespace": "my_namespace",
  "description": "",
  "format": "1.21",
  "main": "src/main.rn",
  "data": "src/data",
  "outFolder": ".",
  "useLock": false
}
```

## Namespace

Namespace will determine the name of the folder inside data/ folder and will be used to run functions. For example if
your function's name is `my_function` you can run it in game by using `function my_namespace:my_function`
where `my_namespace` is the namespace.

## Description

Description is a short description of the function. It will only be used in the `pack.mcmeta` file.

## Pack format

Pack format is the format of the pack. It can be either a pack format version as an integer or a Minecraft version. It
will be used in the `pack.mcmeta` file. It will also affect the name of the `data/my_namespace/functions` folder, for >
=1.21 it will be `data/minecraft/function`.

## Main file

Main file will be the root of the code and parsing will start from here. Its content will also be included in the load
file.

## Data folder

The contents of this folder will be copied to the output folder's `/data/` folder

## Out folder

Out folder section can either be a string or a string array. The datapack will be built into these folders.

## Use-lock

Lock will make it so that when building, it won't be deleting every file that is a part of the datapack. It will only
delete the files that were used to build the datapack last time it built. (This is disabled by default)