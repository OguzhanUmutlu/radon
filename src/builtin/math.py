from typing import List
from tokenizer import GroupToken, Token
from utils import get_expr_id
from utils import FLOAT_PREC, FunctionArgument, FunctionDeclaration, TranspilerContext


def lib_isqrt(ctx: TranspilerContext, _):
    tr = ctx.transpiler
    file = ctx.file
    if "has_sqrt_init" not in tr.data:
        tr.data["has_sqrt_init"] = True
        tr.files["__load__"].append("scoreboard players set __sqrt__2 --temp-- 2")
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


# x^3 - a = 0
# (2x^3 + a) / (3x^2)
# (2x + a / x^2) / 3
# Set: x = 3/2 x
# x + a / ((2x / 3)^2 * 3)
# x + 3/4 * a / x^2
# Set: a = 4/3 a

# Iteration: x = x + a / x^2
# Therefore, iteration: x += a / x^2

# x_t = a / x^2
# x += x_t


def lib_cbrt(ctx: TranspilerContext, _):
    tr = ctx.transpiler
    file = ctx.file
    if "has_cbrt_init" not in tr.data:
        tr.data["has_cbrt_init"] = True
        tr.files["__load__"].append(
            f"scoreboard players set __cbrt__3d2 --temp-- {int(FLOAT_PREC * 3 / 2)}"
        )
        tr.files["__load__"].append(
            f"scoreboard players set __cbrt__4d3 --temp-- {int(FLOAT_PREC * 4 / 3)}"
        )

    file.extend(
        [
            "scoreboard players operation __cbrt__x --temp-- *= __cbrt__4d3 --temp--",
            "scoreboard players operation __cbrt__output --temp-- = __cbrt__x --temp--",
            f"function {tr.pack_name}:__lib__/__cbrt__loop",
        ]
    )

    tr.files["__lib__/cbrt_loop"] = [
        "scoreboard players operation __cbrt__output_change --temp-- = __cbrt__output --temp--",
        "scoreboard players operation __cbrt__output --temp-- *= __cbrt__3d2 --temp--",
        "scoreboard players operation __cbrt__output --temp-- /= FLOAT_PREC --temp--",
        "scoreboard players operation __cbrt__x_t --temp-- =  __cbrt__x --temp--",
        "scoreboard players operation __cbrt__x_t --temp-- *= FLOAT_PREC --temp--",
        "scoreboard players operation __cbrt__x_t --temp-- /= __cbrt__output --temp--",
        "scoreboard players operation __cbrt__x_t --temp-- *= FLOAT_PREC --temp--",
        "scoreboard players operation __cbrt__x_t --temp-- /= __cbrt__output --temp--",
        "scoreboard players operation __cbrt__output --temp-- += __cbrt__x_t --temp--",
        "scoreboard players operation __cbrt__output_change --temp-- -= __cbrt__output --temp--",
        "execute unless score __cbrt__output_change matches 0..0 run function $PACK_NAME$:__lib__/__cbrt__loop",
    ]


# x^2 - a = 0
# (x^2 + a) / (2x)
# (x + a / x) / 2
# Set: x = x / 2
# x + a / (4x)
# Set: a = a / 4
# x + a / x


def lib_sqrt(ctx: TranspilerContext, _):
    tr = ctx.transpiler
    file = ctx.file
    if "has_sqrt_init" not in tr.data:
        tr.data["has_sqrt_init"] = True
        tr.files["__load__"].append("scoreboard players set __sqrt__2 --temp-- 2")
        tr.files["__load__"].append("scoreboard players set __sqrt__4 --temp-- 4")

    # x = x / 4
    # output = x

    # iterate:
    # output_change = output
    # output /= 2
    # x_t = x / output
    # output += x_t
    # output_change -= output

    file.extend(
        [
            "scoreboard players operation __sqrt__x --temp-- /= __sqrt__4 --temp--",
            "scoreboard players operation __sqrt__output --temp-- = __sqrt__x --temp--",
            f"function {tr.pack_name}:__lib__/__sqrt__loop",
        ]
    )

    tr.files["__lib__/sqrt_loop"] = [
        "scoreboard players operation __sqrt__output_change --temp-- = __sqrt__output --temp--",
        "scoreboard players operation __sqrt__output --temp-- /= __sqrt__2 --temp--",
        "scoreboard players operation __sqrt__x_t --temp-- =  __sqrt__x --temp--",
        "scoreboard players operation __sqrt__x_t --temp-- /= __sqrt__output --temp--",
        "scoreboard players operation __sqrt__x_t --temp-- *= FLOAT_PREC --temp--",
        "scoreboard players operation __sqrt__output --temp-- += __sqrt__x_t --temp--",
        "scoreboard players operation __sqrt__output_change --temp-- -= __sqrt__output --temp--",
        "execute unless score __sqrt__output_change matches 0..0 run function $PACK_NAME$:__lib__/__sqrt__loop",
    ]


def lib_float(ctx: TranspilerContext, _):
    ctx.file.append(
        f"scoreboard players operation float_float --temp-- *= FLOAT_PREC --temp--"
    )


def lib_int(ctx: TranspilerContext, _):
    ctx.file.append(
        f"scoreboard players operation int_int --temp-- /= FLOAT_PREC --temp--"
    )


def lib_floor(ctx: TranspilerContext, _):
    ctx.file.append(
        f"scoreboard players operation int_floor --temp-- /= FLOAT_PREC --temp--"
    )


def lib_ceil(ctx: TranspilerContext, _):
    ctx.file.append(f"scoreboard players add int_ceil --temp-- {int(FLOAT_PREC - 1)}")
    ctx.file.append(
        f"scoreboard players operation int_ceil --temp-- /= FLOAT_PREC --temp--"
    )


def lib_round(ctx: TranspilerContext, _):
    ctx.file.append(f"scoreboard players add int_round --temp-- {int(FLOAT_PREC / 2)}")
    ctx.file.append(
        f"scoreboard players operation int_round --temp-- /= FLOAT_PREC --temp--"
    )


def lib_min_max(
    ctx: TranspilerContext, arguments: List[List[Token]], token: GroupToken
):
    if not token.func:
        return "null"
    func_name = token.func.value
    op = "<" if func_name == "min" else ">"
    op_func = lambda x, y: x < y if func_name == "min" else x > y
    file = ctx.file
    minNum = None
    scores = [ctx.transpiler.transpile_expr(arg, ctx) for arg in arguments]

    if len(scores) == 0:
        return "null"

    newScores = []
    scoreT = "int"
    for score in scores:
        if not isinstance(score, str):
            if minNum is None or op_func(score, minNum):
                if isinstance(score, float):
                    scoreT = "float"
                minNum = score
        else:
            if score.startswith("float_"):
                scoreT = "float"
            newScores.append(score)
    lastId = get_expr_id()
    lastScore = f"{scoreT}_{lastId}"
    if minNum is not None:
        if scoreT == "float":
            minNum = int(FLOAT_PREC * minNum)
        file.append(f"scoreboard players set {lastScore} --temp-- {minNum}")
        if len(newScores) == 0:
            return lastScore
    else:
        score = newScores.pop(0)
        file.append(
            f"scoreboard players operation {lastScore} --temp-- = {score} --temp--"
        )
        if score.startswith("int_") and scoreT == "float":
            file.append(
                f"scoreboard players operation {lastScore} --temp-- *= FLOAT_PREC --temp--"
            )

    for score in newScores:
        if score.startswith("int_") and scoreT == "float":
            file.append(
                f"scoreboard players operation {score} --temp-- *= FLOAT_PREC --temp--"
            )
        file.append(
            f"execute if score {score} --temp-- {op} {lastScore} --temp-- run scoreboard players operation {lastScore} --temp-- = {score} --temp--"
        )

    return lastScore


LIB = []


def math_dec(name, args, returns, func, returnId=None):
    if returnId is None:
        returnId = f"{returns}_{name}"
    LIB.append(
        FunctionDeclaration(
            type="python" if args else "python-raw",
            name=name,
            returns=returns,
            returnId=returnId,
            arguments=(
                [
                    FunctionArgument(
                        arg[0] if isinstance(arg, tuple) else arg,
                        "x" + str(index),
                        arg[1] if isinstance(arg, tuple) else f"{name}_{index}",
                    )
                    for index, arg in enumerate(args)
                ]
                if args
                else []
            ),
            direct=True,
            function=func,
        )
    )


math_dec(name="isqrt", args=["int"], returns="int", func=lib_isqrt)
math_dec(name="sqrt", args=["float"], returns="float", func=lib_sqrt)
math_dec(name="cbrt", args=["float"], returns="float", func=lib_cbrt)
math_dec(name="int", args=[("float", "int_int")], returns="int", func=lib_int)
math_dec(name="float", args=[("int", "float_float")], returns="float", func=lib_float)
math_dec(name="floor", args=[("float", "int_floor")], returns="int", func=lib_floor)
math_dec(name="ceil", args=[("float", "int_ceil")], returns="int", func=lib_ceil)
math_dec(name="round", args=[("float", "int_round")], returns="int", func=lib_round)
math_dec(name="min", args=None, returns=None, func=lib_min_max)
math_dec(name="max", args=None, returns=None, func=lib_min_max)
