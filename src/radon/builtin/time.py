from typing import List

from ..cpl import Cpl, CplScore
from ..error import raise_syntax_error
from ..transpiler import FunctionDeclaration, TranspilerContext, add_lib
from ..utils import FLOAT_PREC


def lib_time(ctx: TranspilerContext, args: List[Cpl], token):
    if len(args) != 0:
        raise_syntax_error("time() takes no arguments", token)
    tr = ctx.transpiler
    tr.files["__load__"].append("scoreboard players set __time__time__ __temp__ 0")
    tr.tick_file.append("scoreboard players add __time__time__ __temp__ 1")
    return CplScore(token, "__time__time__ __temp__", "int")


def lib_ftime(ctx: TranspilerContext, args: List[Cpl], token):
    if len(args) != 0:
        raise_syntax_error("ftime() takes no arguments", token)
    tr = ctx.transpiler
    tr.files["__load__"].append("scoreboard players set __ftime__time__ __temp__ 0")
    tr.tick_file.append(f"scoreboard players add __ftime__time__ __temp__ {int(FLOAT_PREC / 20)}")
    return CplScore(token, "__ftime__time__ __temp__", "float")


add_lib(FunctionDeclaration(
    type="python-cpl",
    name="time",
    function=lib_time,
), FunctionDeclaration(
    type="python-cpl",
    name="ftime",
    function=lib_ftime,
))
