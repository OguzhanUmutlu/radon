import math
from math import sqrt, ceil
from typing import List, Any

from ..cpl._base import CompileTimeValue
from ..cpl.float import CplFloat
from ..cpl.int import CplInt
from ..cpl.nbt import CplNBT
from ..cpl.score import CplScore
from ..error import raise_syntax_error
from ..transpiler import TranspilerContext, add_lib, CustomCplObject
from ..utils import FLOAT_PREC, VariableDeclaration


def lib_sqrt(ctx: TranspilerContext, args: List[CompileTimeValue], token):
    tr = ctx.transpiler
    if len(args) != 1:
        raise_syntax_error("Expected 1 argument for Math.sqrt()", token)
    n = args[0]
    if n.unique_type.type not in {"int", "float"}:
        raise_syntax_error("Expected an int or float argument for Math.sqrt()", token)
    if isinstance(n, CplInt) or isinstance(n, CplFloat):
        return CplFloat(token, sqrt(float(n.value)))
    n.cache(ctx, score_loc="__sqrt__x", force="score", force_t="float")

    if "has_sqrt_init" not in tr.data:
        tr.data["has_sqrt_init"] = True
        tr.files["__load__"].append("scoreboard players set __sqrt__2 __temp__ 2")
        tr.files["__load__"].append("scoreboard players set __sqrt__4 __temp__ 4")

    ctx.file.extend(
        [
            "scoreboard players operation __sqrt__x __temp__ /= __sqrt__4 __temp__",
            "scoreboard players operation __sqrt__output __temp__ = __sqrt__x __temp__",
            f"function {tr.pack_namespace}:__lib__/__sqrt__loop",
        ]
    )

    tr.files["__lib__/sqrt_loop"] = [
        "scoreboard players operation __sqrt__output_change __temp__ = __sqrt__output __temp__",
        "scoreboard players operation __sqrt__output __temp__ /= __sqrt__2 __temp__",
        "scoreboard players operation __sqrt__x_t __temp__ =  __sqrt__x __temp__",
        "scoreboard players operation __sqrt__x_t __temp__ /= __sqrt__output __temp__",
        "scoreboard players operation __sqrt__x_t __temp__ *= FLOAT_PREC __temp__",
        "scoreboard players operation __sqrt__output __temp__ += __sqrt__x_t __temp__",
        "scoreboard players operation __sqrt__output_change __temp__ -= __sqrt__output __temp__",
        "execute unless score __sqrt__output_change matches 0..0 run function $PACK_NAME$:__lib__/__sqrt__loop",
    ]

    return CplScore(token, "__sqrt__output __temp__", "float")


def lib_isqrt(ctx: TranspilerContext, args: List[CompileTimeValue], token):
    if len(args) != 1:
        raise_syntax_error("Expected 1 argument for Math.isqrt()", token)
    n = args[0]
    if n.unique_type.type not in {"int", "float"}:
        raise_syntax_error("Expected an int or float argument for Math.isqrt()", token)
    if isinstance(n, CplInt) or isinstance(n, CplFloat):
        return CplFloat(token, sqrt(float(n.value)))
    n.cache(ctx, score_loc="__isqrt__x", force="score", force_t="int")

    tr = ctx.transpiler
    file = ctx.file
    if "has_sqrt_init" not in tr.data:
        tr.data["has_sqrt_init"] = True
        tr.files["__load__"].append("scoreboard players set __sqrt__2 __temp__ 2")
        tr.files["__load__"].append("scoreboard players set __sqrt__4 __temp__ 4")

    file.extend(
        [
            "scoreboard players operation __isqrt__x_4 __temp__ = __isqrt__x __temp__",
            "scoreboard players operation __isqrt__x_4 __temp__ /= __isqrt__4 __temp__",
            "scoreboard players operation __isqrt__output __temp__ = __isqrt__x_4 __temp__",
            f"function {tr.pack_namespace}:__lib__/__isqrt__loop",
        ]
    )

    tr.files["__lib__/isqrt_loop"] = [
        "scoreboard players operation __isqrt__output_change __temp__ = __isqrt__output __temp__",
        "scoreboard players operation __isqrt__output __temp__ /= __isqrt__2 __temp__",
        "scoreboard players operation __isqrt__x_t __temp__ =  __isqrt__x_4 __temp__",
        "scoreboard players operation __isqrt__x_t __temp__ /= __isqrt__output __temp__",
        "scoreboard players operation __isqrt__output __temp__ += __isqrt__x_t __temp__",
        "scoreboard players operation __isqrt__output_change __temp__ -= __isqrt__output __temp__",
        "execute unless score __isqrt__output_change matches 0..0 run function $PACK_NAME$:__lib__/__isqrt__loop",
    ]

    return CplScore(token, "__isqrt__output __temp__", "int")


def lib_cbrt(ctx: TranspilerContext, args: List[CompileTimeValue], token):
    tr = ctx.transpiler
    if len(args) != 1:
        raise_syntax_error("Expected 1 argument for Math.cbrt()", token)
    n = args[0]
    if n.unique_type.type not in {"int", "float"}:
        raise_syntax_error("Expected an int or float argument for Math.cbrt()", token)
    if isinstance(n, CplInt) or isinstance(n, CplFloat):
        return CplFloat(token, float(n.value) ** (1 / 3))
    n.cache(ctx, score_loc="__cbrt__x", force="score")

    if "has_cbrt_init" not in tr.data:
        tr.data["has_cbrt_init"] = True
        tr.files["__load__"].append(
            f"scoreboard players set __cbrt__3d2 __temp__ {int(FLOAT_PREC * 3 / 2)}"
        )
        tr.files["__load__"].append(
            f"scoreboard players set __cbrt__4d3 __temp__ {int(FLOAT_PREC * 4 / 3)}"
        )

    ctx.file.extend(
        [
            "scoreboard players operation __cbrt__x __temp__ *= __cbrt__4d3 __temp__",
            "scoreboard players operation __cbrt__output __temp__ = __cbrt__x __temp__",
            f"function {tr.pack_namespace}:__lib__/__cbrt__loop",
        ]
    )

    tr.files["__lib__/cbrt_loop"] = [
        "scoreboard players operation __cbrt__output_change __temp__ = __cbrt__output __temp__",
        "scoreboard players operation __cbrt__output __temp__ *= __cbrt__3d2 __temp__",
        "scoreboard players operation __cbrt__output __temp__ /= FLOAT_PREC __temp__",
        "scoreboard players operation __cbrt__x_t __temp__ =  __cbrt__x __temp__",
        "scoreboard players operation __cbrt__x_t __temp__ *= FLOAT_PREC __temp__",
        "scoreboard players operation __cbrt__x_t __temp__ /= __cbrt__output __temp__",
        "scoreboard players operation __cbrt__x_t __temp__ *= FLOAT_PREC __temp__",
        "scoreboard players operation __cbrt__x_t __temp__ /= __cbrt__output __temp__",
        "scoreboard players operation __cbrt__output __temp__ += __cbrt__x_t __temp__",
        "scoreboard players operation __cbrt__output_change __temp__ -= __cbrt__output __temp__",
        "execute unless score __cbrt__output_change matches 0..0 run function $PACK_NAME$:__lib__/__cbrt__loop",
    ]

    return CplScore(token, "__cbrt__output __temp__", "float")


def lib_floor(ctx: TranspilerContext, args: List[CompileTimeValue], token):
    if len(args) != 1:
        raise_syntax_error("Expected 1 argument for Math.floor()", token)
    n = args[0]
    if n.unique_type.type not in {"int", "float"}:
        raise_syntax_error("Expected an int or float argument for Math.floor()", token)
    if n.unique_type.type == "int":
        return n
    if isinstance(n, CplFloat):
        return CplInt(token, int(n.value))
    return n.cache(ctx, score_loc="__floor__x __temp__", force="score", force_t="int")


def lib_ceil(ctx: TranspilerContext, args: List[CompileTimeValue], token):
    if len(args) != 1:
        raise_syntax_error("Expected 1 argument for Math.ceil()", token)
    n = args[0]
    if n.unique_type.type not in {"int", "float"}:
        raise_syntax_error("Expected an int or float argument for Math.ceil()", token)
    if n.unique_type.type == "int":
        return n
    if isinstance(n, CplFloat):
        return CplInt(token, int(ceil(n.value)))
    score = n.cache(ctx, score_loc="__ceil__x", force="score")  # it's going to be a float score
    ctx.file.append(f"scoreboard players add __ceil__x __temp__ {int(FLOAT_PREC - 1)}")
    ctx.file.append(f"scoreboard players operation __ceil__x __temp__ /= FLOAT_PREC __temp__")
    return score


def lib_round(ctx: TranspilerContext, args: List[CompileTimeValue], token):
    if len(args) != 1:
        raise_syntax_error("Expected 1 argument for Math.round()", token)
    n = args[0]
    if n.unique_type.type not in {"int", "float"}:
        raise_syntax_error("Expected an int or float argument for Math.round()", token)
    if n.unique_type.type == "int":
        return n
    if isinstance(n, CplFloat):
        return CplInt(token, int(round(n.value)))
    score = n.cache(ctx, score_loc="__round__x", force="score")  # it's going to be a float score
    ctx.file.append(f"scoreboard players add __round__x __temp__ {int(FLOAT_PREC / 2)}")
    ctx.file.append(f"scoreboard players operation __round__x __temp__ /= FLOAT_PREC __temp__")
    return score


def _min_max_help(x, y, func_name):
    return x.value < y.value if func_name == "min" else x.value > y.value


def lib_min_max(
        ctx: TranspilerContext, arguments: List[CompileTimeValue], token, func_name
):
    if len(arguments) == 0:
        raise_syntax_error(f"Expected at least 1 argument for Math.{func_name}()", token)
    min_num: Any = None
    result_type = "int"
    non_literals = []
    for arg in arguments:
        if arg.unique_type.type not in {"int", "float"}:
            raise_syntax_error(f"Expected an int or float argument for Math.{func_name}()", token)
        if arg.unique_type.type == "float":
            result_type = "float"
        if isinstance(arg, CplInt) or isinstance(arg, CplFloat):
            if not min_num or _min_max_help(arg, min_num, func_name):
                min_num = arg
        else:
            non_literals.append(arg)

    result = min_num or CplInt(token, 0)
    for arg in non_literals:
        op = "<" if func_name == "min" else ">"
        if not isinstance(arg, CplScore):
            arg = arg.cache(ctx, force="score", force_t=result_type)
        if isinstance(result, CplInt) or isinstance(result, CplFloat):
            v = result.value if isinstance(result, CplInt) else int(result.value * FLOAT_PREC)
            if func_name == "min":
                cmp = f"..{v - 1}"
            else:
                cmp = f"{v + 1}.."
            ctx.file.append(f"execute if score {arg.location} matches {cmp} "
                            f"run scoreboard players set __min__output __temp__ {v}")
            result = CplScore(token, "__min__output __temp__", result_type)
        else:
            ctx.file.append(f"execute if score {arg.location} {op} {result.location} "
                            f"run scoreboard players set __min__output __temp__ {result.location}")
            result = CplScore(token, "__min__output __temp__", result_type)

    return result


def lib_min(ctx: TranspilerContext, arguments: List[CompileTimeValue], token):
    return lib_min_max(ctx, arguments, token, "min")


def lib_max(ctx: TranspilerContext, arguments: List[CompileTimeValue], token):
    return lib_min_max(ctx, arguments, token, "max")


def lib_random(ctx: TranspilerContext, args: List[CompileTimeValue], token):
    tr = ctx.transpiler
    min_ = (args and args[0]) or CplInt(token, 0)
    max_ = args[1] if len(args) > 1 else CplInt(token, 2147483647)
    if min_.unique_type.type != "int" or max_.unique_type.type != "int":
        raise_syntax_error("Expected an int argument for Math.random()", token)
    if isinstance(min_, CplNBT):
        min_ = min_.cache(ctx, force="score")
    if isinstance(max_, CplNBT):
        max_ = max_.cache(ctx, force="score")
    if "random_setup" not in tr.data:
        tr.files["__math__/random_setup"] = [
            "summon area_effect_cloud ~ ~ ~ {Tags:['__math__.random']}",
            "execute store result score __random__.seed __temp__ run data get entity @e[limit=1,type=area_effect_cloud,tag=__math__.random] UUID[0] 1",
            "kill @e[type=area_effect_cloud,tag=__math__.random]",
            "scoreboard players set __random__.rng.a __temp__ 656891",
            "scoreboard players set __random__.rng.c __temp__ 875773"
        ]
        tr.files["__math__/random"] = [
            "scoreboard players operation __random__.seed __temp__ *= __random__.rng.a __temp__",
            "scoreboard players operation __random__.seed __temp__ += __random__.rng.c __temp__",
            "scoreboard players operation __random__.rng.result __temp__ = __random__.seed __temp__",
            "scoreboard players operation __random__.tmp __temp__ = __random__.rng.result __temp__",
            "scoreboard players operation __random__.rng.result __temp__ %= __random__.rng.bound __temp__",
            "scoreboard players operation __random__.tmp __temp__ -= __random__.rng.result __temp__",
            "scoreboard players operation __random__.tmp __temp__ += __random__.rng.bound __temp__",
            f"execute if score __random__.tmp __temp__ matches ..0 run function {tr.pack_namespace}:__math__/random"
        ]

    if isinstance(min_, CplInt) and isinstance(max_, CplInt):
        ctx.file.append(f"scoreboard players set __random__.rng.bound __temp__ {max_.value - min_.value + 1}")
    elif isinstance(min_, CplScore) and isinstance(max_, CplInt):
        ctx.file.append(f"scoreboard players set __random__.rng.bound __temp__ {max_.value + 1}")
        ctx.file.append(f"scoreboard players operation __random__.rng.bound __temp__ -= {min_.location}")
    elif isinstance(min_, CplInt) and isinstance(max_, CplScore):
        ctx.file.append(f"scoreboard players set __random__.rng.bound __temp__ {-min_.value + 1}")
        ctx.file.append(f"scoreboard players operation __random__.rng.bound __temp__ += {max_.location}")
    else:
        ctx.file.append(f"scoreboard players operation __random__.rng.bound __temp__ = {max_.location}")
        ctx.file.append(f"scoreboard players operation __random__.rng.bound __temp__ -= {min_.location}")
        ctx.file.append(f"scoreboard players add __random__.rng.bound __temp__ 1")
    ctx.file.append(f"function {tr.pack_namespace}:__math__/random")

    return CplScore(token, "__random__.rng.result __temp__", "int")._set_add(ctx, min_)


add_lib(VariableDeclaration(
    name="Math",
    type=CustomCplObject({
        "sqrt": lib_sqrt,
        "cbrt": lib_cbrt,
        "isqrt": lib_isqrt,
        "floor": lib_floor,
        "ceil": lib_ceil,
        "round": lib_round,
        "min": lib_min,
        "max": lib_max,
        "random": lib_random,
        "PI": CplFloat(None, math.pi),
    }),
    constant=True
))
