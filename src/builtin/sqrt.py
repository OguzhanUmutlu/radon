from utils import FunctionArgument, FunctionDeclaration, TranspilerContext


def lib_isqrt(ctx: TranspilerContext, _):
    tr = ctx.transpiler
    file = ctx.file
    if "has_sqrt_init" not in tr.data:
        tr.data["has_sqrt_init"] = True
    tr.files["__load__"].append("scoreboard players set __sqrt__4 --temp-- 4")

    file.extend(
        [
            "scoreboard players operation __isqrt__x_4 --temp-- = __isqrt__x --temp--",
            "scoreboard players operation __isqrt__x_4 --temp-- /= __isqrt__4 --temp--",
            "scoreboard players operation __isqrt__output --temp-- = __isqrt__x_4 --temp--",
            f"function {tr.pack_name}:__lib__/__isqrt__loop",
        ]
    )

    tr.files["__lib__/isqrt_loop"] = [
        "scoreboard players operation __isqrt__output_change --temp-- = __isqrt__output --temp--",
        "scoreboard players operation __isqrt__output --temp-- /= __isqrt__2 --temp--",
        "scoreboard players operation __isqrt__x_t --temp-- =  __isqrt__x_4 --temp--",
        "scoreboard players operation __isqrt__x_t --temp-- /= __isqrt__output --temp--",
        "scoreboard players operation __isqrt__output --temp-- += __isqrt__x_t --temp--",
        "scoreboard players operation __isqrt__output_change --temp-- -= __isqrt__output --temp--",
        "execute unless score __isqrt__output_change matches 0..0 run function $PACK_NAME$:__lib__/__isqrt__loop",
    ]


def lib_fsqrt(ctx: TranspilerContext, _):
    tr = ctx.transpiler
    file = ctx.file
    if "has_sqrt_init" not in tr.data:
        tr.data["has_sqrt_init"] = True
    tr.files["__load__"].append("scoreboard players set __sqrt__4 --temp-- 4")

    file.extend(
        [
            "scoreboard players operation __fsqrt__x_4 --temp-- = __fsqrt__x --temp--",
            "scoreboard players operation __fsqrt__x_4 --temp-- /= __fsqrt__4 --temp--",
            "scoreboard players operation __fsqrt__output --temp-- = __fsqrt__x_4 --temp--",
            f"function {tr.pack_name}:__lib__/__fsqrt__loop",
        ]
    )

    tr.files["__lib__/fsqrt_loop"] = [
        "scoreboard players operation __fsqrt__output_change --temp-- = __fsqrt__output --temp--",
        "scoreboard players operation __fsqrt__output --temp-- /= __fsqrt__2 --temp--",
        "scoreboard players operation __fsqrt__x_t --temp-- =  __fsqrt__x_4 --temp--",
        "scoreboard players operation __fsqrt__x_t --temp-- /= __fsqrt__output --temp--",
        "scoreboard players operation __fsqrt__x_t --temp-- *= FLOAT_PREC --temp--",
        "scoreboard players operation __fsqrt__output --temp-- += __fsqrt__x_t --temp--",
        "scoreboard players operation __fsqrt__output_change --temp-- -= __fsqrt__output --temp--",
        "execute unless score __fsqrt__output_change matches 0..0 run function $PACK_NAME$:__lib__/__fsqrt__loop",
    ]


LIB = [
    FunctionDeclaration(
        type="python",
        name="sqrt",
        returns="int",
        returnId="__isqrt__output",
        arguments=[FunctionArgument("int", "x", "__isqrt__x")],
        direct=True,
        function=lib_isqrt,
    ),
    FunctionDeclaration(
        type="python",
        name="sqrt",
        returns="float",
        returnId="__fsqrt__output",
        arguments=[FunctionArgument("float", "x", "__fsqrt__x")],
        direct=True,
        function=lib_fsqrt,
    ),
]
