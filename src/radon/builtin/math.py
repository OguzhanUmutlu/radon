from typing import List

from math import sqrt
from ..cpl.base import CompileTimeValue
from ..cpl.float import CplFloat
from ..cpl.int import CplInt
from ..cpl.score import CplScore
from ..error import raise_syntax_error
from ..transpiler import TranspilerContext, add_lib, FunctionDeclaration

_ = 0


def lib_sqrt(ctx: TranspilerContext, args: List[CompileTimeValue], token):
    tr = ctx.transpiler
    if len(args) != 1:
        raise_syntax_error("Expected 1 argument for sqrt()", token)
    n = args[0]
    if n.unique_type.type not in {"int", "float"}:
        raise_syntax_error("Expected an int or float argument for sqrt()", token)
    if isinstance(n, CplInt) or isinstance(n, CplFloat):
        return CplFloat(token, sqrt(float(n.value)))
    n.cache(ctx, score_loc="__sqrt__x", force="score")

    if "has_sqrt_init" not in tr.data:
        tr.data["has_sqrt_init"] = True
        tr.files["__load__"].append("scoreboard players set __sqrt__2 --temp-- 2")
        tr.files["__load__"].append("scoreboard players set __sqrt__4 --temp-- 4")

    ctx.file.extend(
        [
            "scoreboard players operation __sqrt__x --temp-- /= __sqrt__4 --temp--",
            "scoreboard players operation __sqrt__output --temp-- = __sqrt__x --temp--",
            f"function {tr.pack_namespace}:__lib__/__sqrt__loop",
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

    return CplScore(token, "__sqrt__output --temp--", "float")


def lib_cbrt(ctx: TranspilerContext, args: List[CompileTimeValue], token):
    tr = ctx.transpiler
    if len(args) != 1:
        raise_syntax_error("Expected 1 argument for cbrt()", token)
    n = args[0]
    if n.unique_type.type not in {"int", "float"}:
        raise_syntax_error("Expected an int or float argument for cbrt()", token)
    if isinstance(n, CplInt) or isinstance(n, CplFloat):
        return CplFloat(token, sqrt(float(n.value)))
    n.cache(ctx, score_loc="__cbrt__x", force="score")

    if "has_cbrt_init" not in tr.data:
        tr.data["has_cbrt_init"] = True
        tr.files["__load__"].append(
            f"scoreboard players set __cbrt__3d2 --temp-- {int(FLOAT_PREC * 3 / 2)}"
        )
        tr.files["__load__"].append(
            f"scoreboard players set __cbrt__4d3 --temp-- {int(FLOAT_PREC * 4 / 3)}"
        )

    ctx.file.extend(
        [
            "scoreboard players operation __cbrt__x --temp-- *= __cbrt__4d3 --temp--",
            "scoreboard players operation __cbrt__output --temp-- = __cbrt__x --temp--",
            f"function {tr.pack_namespace}:__lib__/__cbrt__loop",
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

    return CplScore(token, "__cbrt__output --temp--", "float")


add_lib(FunctionDeclaration(
    type="python-cpl",
    name="sqrt",
    function=lib_sqrt
))

add_lib(FunctionDeclaration(
    type="python-cpl",
    name="cbrt",
    function=lib_cbrt
))

'''def lib_isqrt(ctx: TranspilerContext, _, __):
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
            f"function {tr.pack_namespace}:__lib__/__isqrt__loop",
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


def lib_cbrt(ctx: TranspilerContext, _, __):
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
            f"function {tr.pack_namespace}:__lib__/__cbrt__loop",
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


def lib_sqrt(ctx: TranspilerContext, _, __):
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
            f"function {tr.pack_namespace}:__lib__/__sqrt__loop",
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


def lib_float(ctx: TranspilerContext, _, __):
    ctx.file.append(
        f"scoreboard players operation float_float --temp-- *= FLOAT_PREC --temp--"
    )


def lib_int(ctx: TranspilerContext, _, __):
    ctx.file.append(
        f"scoreboard players operation int_int --temp-- /= FLOAT_PREC --temp--"
    )


def lib_floor(ctx: TranspilerContext, _, __):
    ctx.file.append(
        f"scoreboard players operation int_floor --temp-- /= FLOAT_PREC --temp--"
    )


def lib_ceil(ctx: TranspilerContext, _, __):
    ctx.file.append(f"scoreboard players add int_ceil --temp-- {int(FLOAT_PREC - 1)}")
    ctx.file.append(
        f"scoreboard players operation int_ceil --temp-- /= FLOAT_PREC --temp--"
    )


def lib_round(ctx: TranspilerContext, _, __):
    ctx.file.append(f"scoreboard players add int_round --temp-- {int(FLOAT_PREC / 2)}")
    ctx.file.append(
        f"scoreboard players operation int_round --temp-- /= FLOAT_PREC --temp--"
    )


def _min_max_help(x, y, func_name):
    return x.value < y.value if func_name == "min" else x.value > y.value


def lib_min_max(
        ctx: TranspilerContext, arguments: List[CompileTimeValue], token: GroupToken
):
    if not token.func:
        return "null"
    func_name = token.func.value
    op = "<" if func_name == "min" else ">"
    file = ctx.file
    min_num = None
    scores = [
        arg if (isinstance(arg, CplScore)
                or isinstance(arg, CplInt)
                or isinstance(arg, CplFloat))
        else arg.cache(ctx, force="score")
        for arg in arguments]

    if len(scores) == 0:
        return "null"

    new_scores = []
    score_t = "int"
    for score in scores:
        if isinstance(score, CplScore):
            if score.unique_type.type == "float":
                score_t = "float"
            new_scores.append(score)
        elif min_num is None or _min_max_help(score, min_num, func_name):
            if score.unique_type.type == "float":
                score_t = "float"
            min_num = score.value
    last_id = get_expr_id()
    last_score = f"{score_t}_{last_id}"
    if min_num is not None:
        if score_t == "float":
            min_num = int(FLOAT_PREC * min_num)
        file.append(f"scoreboard players set {last_score} --temp-- {min_num}")
        if len(new_scores) == 0:
            return last_score
    else:
        score = new_scores.pop(0)
        file.append(
            f"scoreboard players operation {last_score} --temp-- = {score.location} --temp--"
        )
        if score.unique_type.type == "int" and score_t == "float":
            file.append(
                f"scoreboard players operation {last_score} --temp-- *= FLOAT_PREC --temp--"
            )

    for score in new_scores:
        if score.unique_type.type == "int" and score_t == "float":
            file.append(
                f"scoreboard players operation {score.location} --temp-- *= FLOAT_PREC --temp--"
            )
        file.append(
            f"execute if score {score.location} --temp-- {op} {last_score} --temp-- "
            f"run scoreboard players operation {last_score} --temp-- = {score.location} --temp--"
        )

    return last_score


def math_dec(name, args, returns, func, return_loc=None):
    if returns is None:
        return_loc = NULL_VALUE
    elif returns == "int":
        return_loc = CplScore(None, return_loc or f"int_{name}")
    else:
        return_loc = CplScore(None, return_loc or f"float_{name}")
    add_lib(
        FunctionDeclaration(
            type="python" if args else "python-cpl",
            name=name,
            returns=return_loc,
            arguments=(
                [
                    FunctionArgument(
                        "x" + str(index),
                        CplScore(
                            None,
                            (arg[1] if isinstance(arg, tuple) else f"{name}_{index}")
                            + " --temp--",
                            arg[0] if isinstance(arg, tuple) else arg,
                        ),
                        False
                    )
                    for index, arg in enumerate(args)
                ]
                if args
                else []
            ),
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
math_dec(name="max", args=None, returns=None, func=lib_min_max)'''
