import math
from typing import List, Any

from ..cpl._base import CompileTimeValue
from ..cpl.float import CplFloat
from ..cpl.int import CplInt
from ..cpl.nbt import CplNBT
from ..cpl.nbtfloat import CplFloatNBT
from ..cpl.nbtint import CplIntNBT
from ..cpl.score import CplScore
from ..error import raise_syntax_error
from ..transpiler import TranspilerContext, add_lib, CustomCplObject
from ..utils import FLOAT_PREC, VariableDeclaration, get_uuid


def helper_float0_check(ctx: TranspilerContext, args: List[CompileTimeValue], token, method: str):
    if len(args) != 1:
        raise_syntax_error(f"Expected 1 argument for {method}()", token)
    n = args[0]
    if n.unique_type.type not in {"int", "float"}:
        raise_syntax_error(f"Expected an int or float argument for {method}()", token)


def helper_float0(ctx: TranspilerContext, args: List[CompileTimeValue], token, method: str,
                  score_loc=None) -> float | CplScore:
    helper_float0_check(ctx, args, token, method)
    n = args[0]
    if isinstance(n, CplInt) or isinstance(n, CplFloat):
        return float(n.value)
    return n.cache(ctx, score_loc=score_loc, force="score", force_t="float")


def lib_sqrt(ctx: TranspilerContext, args: List[CompileTimeValue], token):
    tr = ctx.transpiler
    helper = helper_float0(ctx, args, token, "Math.sqrt", "__sqrt__x")
    if isinstance(helper, float):
        return CplFloat(token, math.sqrt(helper))

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
        "scoreboard players operation __sqrt__last_output __temp__ = __sqrt__output __temp__",
        "scoreboard players operation __sqrt__output __temp__ /= __sqrt__2 __temp__",
        "scoreboard players operation __sqrt__x_t __temp__ =  __sqrt__x __temp__",
        "scoreboard players operation __sqrt__x_t __temp__ /= __sqrt__output __temp__",
        "scoreboard players operation __sqrt__x_t __temp__ *= FLOAT_PREC __temp__",
        "scoreboard players operation __sqrt__output __temp__ += __sqrt__x_t __temp__",
        "execute unless score __sqrt__last_output __temp__ = __sqrt__output __temp__ run function $PACK_NAME$:__lib__/__sqrt__loop",
    ]

    return CplScore(token, "__sqrt__output __temp__", "float")


def lib_isqrt(ctx: TranspilerContext, args: List[CompileTimeValue], token):
    if len(args) != 1:
        raise_syntax_error("Expected 1 argument for Math.isqrt()", token)
    n = args[0]
    if n.unique_type.type != "int":
        raise_syntax_error("Expected an int argument for Math.isqrt()", token)
    if isinstance(n, CplInt):
        return CplInt(token, math.isqrt(n.value))
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
        "scoreboard players operation __isqrt__last_output __temp__ = __isqrt__output __temp__",
        "scoreboard players operation __isqrt__output __temp__ /= __isqrt__2 __temp__",
        "scoreboard players operation __isqrt__x_t __temp__ =  __isqrt__x_4 __temp__",
        "scoreboard players operation __isqrt__x_t __temp__ /= __isqrt__output __temp__",
        "scoreboard players operation __isqrt__output __temp__ += __isqrt__x_t __temp__",
        "execute unless score __isqrt__last_output __temp__ = __isqrt__output __temp__ run function $PACK_NAME$:__lib__/__isqrt__loop",
    ]

    return CplScore(token, "__isqrt__output __temp__", "int")


def lib_cbrt(ctx: TranspilerContext, args: List[CompileTimeValue], token):
    tr = ctx.transpiler
    helper = helper_float0(ctx, args, token, "Math.cbrt", "__cbrt__x")
    if isinstance(helper, float):
        return CplFloat(token, helper ** (1 / 3))

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
        "scoreboard players operation __cbrt__last_output __temp__ = __cbrt__output __temp__",
        "scoreboard players operation __cbrt__output __temp__ *= __cbrt__3d2 __temp__",
        "scoreboard players operation __cbrt__output __temp__ /= FLOAT_PREC __temp__",
        "scoreboard players operation __cbrt__x_t __temp__ =  __cbrt__x __temp__",
        "scoreboard players operation __cbrt__x_t __temp__ *= FLOAT_PREC __temp__",
        "scoreboard players operation __cbrt__x_t __temp__ /= __cbrt__output __temp__",
        "scoreboard players operation __cbrt__x_t __temp__ *= FLOAT_PREC __temp__",
        "scoreboard players operation __cbrt__x_t __temp__ /= __cbrt__output __temp__",
        "scoreboard players operation __cbrt__output __temp__ += __cbrt__x_t __temp__",
        "execute unless score __cbrt__last_output __temp__ = __cbrt__output __temp__ run function $PACK_NAME$:__lib__/__cbrt__loop",
    ]

    return CplScore(token, "__cbrt__output __temp__", "float")


def lib_floor(ctx: TranspilerContext, args: List[CompileTimeValue], token):
    helper = helper_float0(ctx, args, token, "Math.floor")
    if isinstance(helper, float):
        return CplFloat(token, math.floor(helper))
    return helper


def lib_ceil(ctx: TranspilerContext, args: List[CompileTimeValue], token):
    helper = helper_float0(ctx, args, token, "Math.ceil", "__ceil__x")
    if isinstance(helper, float):
        return CplFloat(token, math.ceil(helper))
    n = args[0]
    if n.unique_type.type == "int":
        return n

    ctx.file.append(f"scoreboard players add __ceil__x __temp__ {int(FLOAT_PREC - 1)}")
    ctx.file.append(f"scoreboard players operation __ceil__x __temp__ /= FLOAT_PREC __temp__")
    return helper


def lib_round(ctx: TranspilerContext, args: List[CompileTimeValue], token):
    helper = helper_float0(ctx, args, token, "Math.round", "__round__x")
    if isinstance(helper, float):
        return CplFloat(token, round(helper))
    n = args[0]
    if n.unique_type.type == "int":
        return n

    ctx.file.append(f"scoreboard players add __round__x __temp__ {int(FLOAT_PREC / 2)}")
    ctx.file.append(f"scoreboard players operation __round__x __temp__ /= FLOAT_PREC __temp__")
    return helper


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
    if tr.pack_format >= 18:
        # Just use /random command that got added in 1.20.2
        if isinstance(min_, CplInt) and isinstance(max_, CplInt):
            eid = f"int_{get_uuid()} __temp__"
            ctx.file.append(f"execute store result score {eid} run random value {min_.value}..{max_.value}")
            return CplScore(token, eid)

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


def pseudo_int(ctx, cpl):
    if isinstance(cpl, CplFloat):
        return CplInt(cpl.token, int(cpl.value * FLOAT_PREC))
    if isinstance(cpl, CplScore):
        return CplScore(cpl.token, cpl.location, "int")
    if isinstance(cpl, CplFloatNBT):
        cached = cpl.cache(ctx, force="score")
        return CplScore(cpl.token, cached.location, "int")
    raise ValueError("Unexpected input")


def lib_frandom(ctx: TranspilerContext, args: List[CompileTimeValue], token):
    if len(args) != 2:
        raise_syntax_error("Expected 2 arguments for Math.frandom()", token)
    if args[0].unique_type.type != "float" or args[1].unique_type.type != "float":
        raise_syntax_error("Expected a float argument for Math.frandom()", token)
    score = lib_random(ctx, list(map(lambda arg: pseudo_int(ctx, arg), args)), token)
    return CplScore(token, score.location, "float")


def lib_ipow(ctx: TranspilerContext, args: List[CompileTimeValue], token):
    tr = ctx.transpiler
    if len(args) != 2:
        raise_syntax_error(f"Expected 2 arguments for Math.ipow()", token)
    a0 = args[0]
    a1 = args[1]
    if a0.unique_type.type not in {"int", "float"}:
        raise_syntax_error(f"Expected an int or float for the first argument of Math.ipow()", token)
    if a1.unique_type.type != "int":
        raise_syntax_error(f"Expected an int for the second argument of Math.ipow()", token)
    if isinstance(a0, CplNBT):
        a0 = a0.cache(ctx, force="score")
    if isinstance(a1, CplIntNBT):
        a1 = a1.cache(ctx, force="score")
    if (isinstance(a0, CplInt) or isinstance(a0, CplFloat)) and isinstance(a1, CplInt):
        if isinstance(a0, CplFloat):
            return CplFloat(token, a0.value ** a1.value)
        return CplInt(token, int(a0.value ** a1.value))  # type: ignore
    output = CplScore(token, "__ipow__output __temp__", a0.unique_type.type)

    if isinstance(a1, CplInt):
        if a1.value == 0:
            return CplInt(token, 1)
        if a1.value == 1:
            return a0
        output._set(ctx, a0)
        for i in range(a1.value - 1):
            output._set_mul(ctx, a0)
    else:
        if isinstance(a0, CplInt):
            if a0.value == 0:
                return CplInt(token, 0)
            if a0.value == 1:
                return CplInt(token, 1)
        output._set(ctx, CplInt(token, 1))
        a0.cache(ctx, force="score", score_loc="__ipow__x __temp__")
        a1.cache(ctx, force="score", score_loc="__ipow__n __temp__")
        ctx.file.append(f"function {tr.pack_namespace}:__ipow__/loop{a0.unique_type.type[0]}")
        tr.files[f"__ipow__/loop{a0.unique_type.type[0]}"] = [
            f"scoreboard players remove __ipow__n __temp__ 1",
            f"scoreboard players operation __ipow__output __temp__ *= __ipow__x __temp__",
            f"scoreboard players operation __ipow__output __temp__ /= FLOAT_PREC __temp__" if a0.unique_type.type == "float" else "",
            f"execute if score __ipow__n __temp__ matches 1.. run function {tr.pack_namespace}:__ipow__/loop",
        ]

    return output


def lib_fastexp(ctx: TranspilerContext, args: List[CompileTimeValue], token):
    score = helper_float0(ctx, args, token, "Math.fastexp")
    if isinstance(score, float):
        return CplFloat(token, math.exp(score))

    exp_n = 8
    score._set_div(ctx, CplInt(token, 2 ** exp_n))
    score._set_add(ctx, CplInt(token, 1))
    for i in range(exp_n):
        score._set_mul(ctx, score)

    return score


def lib_exp(ctx: TranspilerContext, args: List[CompileTimeValue], token):
    tr = ctx.transpiler
    score = helper_float0(ctx, args, token, "Math.exp", "__exp__x __temp__")
    if isinstance(score, float):
        return CplFloat(token, math.exp(score))

    ctx.file.append(f"function {tr.pack_namespace}:__exp__/run")

    tr.files["__exp__/init"] = [
        f"scoreboard players set __exp__output __temp__ {int(FLOAT_PREC)}",
        f"scoreboard players set __exp__xn __temp__ {int(FLOAT_PREC)}",
        f"scoreboard players set __exp__nf __temp__ 1",
        f"scoreboard players set __exp__n __temp__ 0",
        f"function {tr.pack_namespace}:__exp__/loop"
    ]

    tr.files["__exp__/loop"] = [
        f"scoreboard players add __exp__n __temp__ 1",
        f"scoreboard players operation __exp__nf __temp__ *= __exp__n __temp__",
        f"scoreboard players operation __exp__xn __temp__ *= __exp__x __temp__",
        f"scoreboard players operation __exp__xn __temp__ /= FLOAT_PREC __temp__",
        f"scoreboard players operation __exp__xmn __temp__ = __exp__xn __temp__",
        f"scoreboard players operation __exp__xmn __temp__ /= __exp__nf __temp__",
        f"scoreboard players operation __exp__output __temp__ += __exp__xmn __temp__",
        f"execute unless score __exp__xmn __temp__ matches 0 run function {tr.pack_namespace}:__exp__/loop",
    ]

    return CplScore(token, "__exp__output __temp__", "float")


def lib_sin_cos(ctx: TranspilerContext, args: List[CompileTimeValue], token, cos):
    name = "cos" if cos else "sin"
    x = helper_float0(ctx, args, token, f"Math.{name}", f"__{name}__x __temp__")
    if isinstance(x, float):
        return CplFloat(token, math.cos(x) if cos else math.sin(x))

    if cos:
        # score = pi/2 - score
        x._set_sub(ctx, CplFloat(token, math.pi / 2))
        x._set_mul(ctx, CplFloat(token, -1))

    # https://en.wikipedia.org/wiki/Bh%C4%81skara_I%27s_sine_approximation_formula

    # sin(x) = 16 * x * (pi - x) / (5pi^2 - 4x(pi - x))
    # x0 = pi
    # x0 -= x
    # x1 = 16
    # x1 *= x
    # x1 *= x0
    # x2 = 5pi^2
    # x3 = 4
    # x3 *= x
    # x3 *= x0
    # x2 -= x3
    # x1 /= x2
    # return x1

    x0 = CplScore(token, f"__{name}__x0 __temp__", "float")
    x1 = CplScore(token, f"__{name}__x1 __temp__", "float")
    x2 = CplScore(token, f"__{name}__x2 __temp__", "float")
    x3 = CplScore(token, f"__{name}__x3 __temp__", "float")

    x0._set(ctx, CplFloat(token, math.pi))
    x0._set_sub(ctx, x)
    x1._set(ctx, CplFloat(token, 16))
    x1._set_mul(ctx, x)
    x1._set_mul(ctx, x0)
    x2._set(ctx, CplFloat(token, 5 * math.pi * math.pi))
    x3._set(ctx, CplFloat(token, 4))
    x3._set_mul(ctx, x)
    x3._set_mul(ctx, x0)
    x2._set_sub(ctx, x3)
    x1._set_div(ctx, x2)

    return x1


def lib_sin(ctx: TranspilerContext, args: List[CompileTimeValue], token):
    return lib_sin_cos(ctx, args, token, False)


def lib_cos(ctx: TranspilerContext, args: List[CompileTimeValue], token):
    return lib_sin_cos(ctx, args, token, True)


def lib_tan(ctx: TranspilerContext, args: List[CompileTimeValue], token):
    helper_float0_check(ctx, args, token, f"Math.tan")
    x = args[0]
    if isinstance(x, CplInt) or isinstance(x, CplFloat):
        return CplFloat(token, math.tan(x.value))
    return lib_sin(ctx, args, token)._set_div(ctx, lib_cos(ctx, args, token))


def lib_csc(ctx: TranspilerContext, args: List[CompileTimeValue], token):
    helper_float0_check(ctx, args, token, f"Math.csc")
    x = args[0]
    if isinstance(x, CplInt) or isinstance(x, CplFloat):
        return CplFloat(token, 1 / math.sin(x.value))
    return CplFloat(token, 1)._div(ctx, lib_sin(ctx, args, token))


def lib_sec(ctx: TranspilerContext, args: List[CompileTimeValue], token):
    helper_float0_check(ctx, args, token, f"Math.sec")
    x = args[0]
    if isinstance(x, CplInt) or isinstance(x, CplFloat):
        return CplFloat(token, 1 / math.cos(x.value))
    return CplFloat(token, 1)._div(ctx, lib_cos(ctx, args, token))


def lib_cot(ctx: TranspilerContext, args: List[CompileTimeValue], token):
    helper_float0_check(ctx, args, token, f"Math.cot")
    x = args[0]
    if isinstance(x, CplInt) or isinstance(x, CplFloat):
        return CplFloat(token, 1 / math.tan(x.value))
    return CplFloat(token, 1)._div(ctx, lib_tan(ctx, args, token))


def lib_fastarcsin(ctx: TranspilerContext, args: List[CompileTimeValue], token):
    x = helper_float0(ctx, args, token, f"Math.fastarcsin", f"__fastarcsin__x __temp__")
    if isinstance(x, float):
        return CplFloat(token, math.asin(x))
    x2 = CplScore(token, f"__fastarcsin__x2 __temp__", "float")
    num = CplScore(token, f"__fastarcsin__num __temp__", "float")
    denom = CplScore(token, f"__fastarcsin__denom __temp__", "float")

    # x2 = x*x
    # num = ((-0.0187293 * x2 + 0.0742610) * x2 - 0.2121144) * x2 + 1.5707288;
    # denom = ((0.0758669 * x2 + 1.0) * x2 + 1.0);
    # return x * num / denom

    # x2 = x
    # x2 *= x
    # num = -0.0187293
    # num *= x2
    # num += 0.0742610
    # num *= x2
    # num -= 0.2121144
    # num *= x2
    # num += 1.5707288
    # denom = 0.0758669
    # denom *= x2
    # denom += 1.0
    # denom *= x2
    # denom += 1.0
    # x *= num
    # x /= denom
    # return x

    x2._set(ctx, x)
    x2._set_mul(ctx, x)
    num._set(ctx, CplFloat(token, -0.0187293))
    num._set_mul(ctx, x2)
    num._set_add(ctx, CplFloat(token, 0.0742610))
    num._set_mul(ctx, x2)
    num._set_sub(ctx, CplFloat(token, 0.2121144))
    num._set_mul(ctx, x2)
    num._set_add(ctx, CplFloat(token, 1.5707288))
    denom._set(ctx, CplFloat(token, 0.0758669))
    denom._set_mul(ctx, x2)
    denom._set_add(ctx, CplFloat(token, 1.0))
    denom._set_mul(ctx, x2)
    denom._set_add(ctx, CplFloat(token, 1.0))
    x._set_mul(ctx, num)
    x._set_div(ctx, denom)

    return x


def lib_fastarccos(ctx: TranspilerContext, args: List[CompileTimeValue], token):
    helper_float0_check(ctx, args, token, f"Math.fastarccos")
    x = args[0]
    if isinstance(x, CplInt) or isinstance(x, CplFloat):
        return CplFloat(token, math.acos(x.value))
    return (lib_fastarcsin(ctx, args, token)
            ._set_sub(ctx, CplFloat(token, math.pi / 2))
            ._set_mul(ctx, CplFloat(token, -1)))


def lib_fastarctan(ctx: TranspilerContext, args: List[CompileTimeValue], token):
    helper_float0_check(ctx, args, token, f"Math.fastarctan")
    x = args[0]
    if isinstance(x, CplInt) or isinstance(x, CplFloat):
        return CplFloat(token, math.atan(x.value))
    # arctan(x) = arcsin(x / sqrt(1 + x^2))

    x0 = CplScore(token, f"__fastarcsin__x __temp__", "float")

    x0._set(ctx, x)
    x0._set_mul(ctx, x)
    x0._set_add(ctx, CplFloat(token, 1.0))
    x0 = x0._call_index(ctx, "sqrt", [x0], token)
    x._set_div(ctx, x0)

    return lib_fastarcsin(ctx, [x], token)


def lib_fastarccsc(ctx: TranspilerContext, args: List[CompileTimeValue], token):
    helper_float0_check(ctx, args, token, f"Math.fastarccsc")
    x = args[0]
    if isinstance(x, CplInt) or isinstance(x, CplFloat):
        return CplFloat(token, math.asin(1 / x.value))
    return lib_fastarcsin(ctx, [CplFloat(token, 1)._div(ctx, x)], token)


def lib_fastarcsec(ctx: TranspilerContext, args: List[CompileTimeValue], token):
    helper_float0_check(ctx, args, token, f"Math.fastarcsec")
    x = args[0]
    if isinstance(x, CplInt) or isinstance(x, CplFloat):
        return CplFloat(token, math.acos(1 / x.value))
    return lib_fastarccos(ctx, [CplFloat(token, 1)._div(ctx, x)], token)


def lib_fastarccot(ctx: TranspilerContext, args: List[CompileTimeValue], token):
    helper_float0_check(ctx, args, token, f"Math.fastarccot")
    x = args[0]
    if isinstance(x, CplInt) or isinstance(x, CplFloat):
        return CplFloat(token, math.atan(1 / x.value))
    return lib_fastarctan(ctx, [CplFloat(token, 1)._div(ctx, x)], token)


def lib_arcsin(ctx: TranspilerContext, args: List[CompileTimeValue], token):
    x = helper_float0(ctx, args, token, f"Math.arcsin", "__arcsin__x __temp__")
    if isinstance(x, float):
        return CplFloat(token, math.asin(x))

    # d/dx arcsin(x) = 1 / sqrt(1-x^2)
    # arcsin(a) = x
    # a = sin(x)
    # a - sin(x) = 0

    # iterate: y -= (sin(y) - x) / cos(y)

    y = CplScore(token, f"__arcsin__y __temp__", "float")
    z = CplScore(token, f"__arcsin__z __temp__", "float")

    # heuristic guess
    y._set(ctx, x)

    for i in range(2):
        z._set(ctx, lib_sin(ctx, [x], token))
        z._set_sub(ctx, x)
        z._set_div(ctx, lib_cos(ctx, [x], token))
        y._set_sub(ctx, z)

    return y


def lib_arccos(ctx: TranspilerContext, args: List[CompileTimeValue], token):
    helper_float0_check(ctx, args, token, f"Math.arccos")
    x = args[0]
    if isinstance(x, CplInt) or isinstance(x, CplFloat):
        return CplFloat(token, math.acos(x.value))

    return (lib_arcsin(ctx, args, token)
            ._set_sub(ctx, CplFloat(token, math.pi / 2))
            ._set_mul(ctx, CplFloat(token, -1)))


def lib_arctan(ctx: TranspilerContext, args: List[CompileTimeValue], token):
    helper_float0_check(ctx, args, token, f"Math.arctan")
    x = args[0]
    if isinstance(x, CplInt) or isinstance(x, CplFloat):
        return CplFloat(token, math.atan(x.value))

    # arctan(x) = arcsin(x / sqrt(1 + x^2))

    x0 = CplScore(token, f"__arcsin__x __temp__", "float")

    x0._set(ctx, x)
    x0._set_mul(ctx, x)
    x0._set_add(ctx, CplFloat(token, 1.0))
    x0 = x0._call_index(ctx, "sqrt", [x0], token)
    x._set_div(ctx, x0)

    return lib_arcsin(ctx, [x], token)


def lib_arccsc(ctx: TranspilerContext, args: List[CompileTimeValue], token):
    helper_float0_check(ctx, args, token, f"Math.arccsc")
    x = args[0]
    if isinstance(x, CplInt) or isinstance(x, CplFloat):
        return CplFloat(token, math.asin(1 / x.value))

    return lib_arcsin(ctx, [CplFloat(token, 1)._div(ctx, x)], token)


def lib_arcsec(ctx: TranspilerContext, args: List[CompileTimeValue], token):
    helper_float0_check(ctx, args, token, f"Math.arcsec")
    x = args[0]
    if isinstance(x, CplInt) or isinstance(x, CplFloat):
        return CplFloat(token, math.acos(1 / x.value))

    return lib_arccos(ctx, [CplFloat(token, 1)._div(ctx, x)], token)


def lib_arccot(ctx: TranspilerContext, args: List[CompileTimeValue], token):
    helper_float0_check(ctx, args, token, f"Math.arccot")
    x = args[0]
    if isinstance(x, CplInt) or isinstance(x, CplFloat):
        return CplFloat(token, math.atan(1 / x.value))

    return lib_arctan(ctx, [CplFloat(token, 1)._div(ctx, x)], token)


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
        "frandom": lib_frandom,
        "ipow": lib_ipow,
        "fastexp": lib_fastexp,
        "exp": lib_exp,
        "sin": lib_sin,
        "cos": lib_cos,
        "tan": lib_tan,
        "csc": lib_csc,
        "sec": lib_sec,
        "cot": lib_cot,
        "arcsin": lib_arcsin,
        "arccos": lib_arccos,
        "arctan": lib_arctan,
        "arccsc": lib_arccsc,
        "arcsec": lib_arcsec,
        "arccot": lib_arccot,
        "fastarcsin": lib_fastarcsin,
        "fastarccos": lib_fastarccos,
        "fastarctan": lib_fastarctan,
        "fastarccsc": lib_fastarccsc,
        "fastarcsec": lib_fastarcsec,
        "fastarccot": lib_fastarccot,
        "PI": CplFloat(None, math.pi),
        "E": CplFloat(None, math.e),
        "LN2": CplFloat(None, math.log(2)),
        "LN10": CplFloat(None, math.log(10)),
        "LOG2E": CplFloat(None, math.log(math.e, 2)),
        "LOG10E": CplFloat(None, math.log(math.e, 10)),
        "SQRT1_2": CplFloat(None, math.sqrt(0.5)),
        "SQRT2": CplFloat(None, math.sqrt(2)),
    }),
    constant=True
))
