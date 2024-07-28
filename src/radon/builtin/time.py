from ..cpl.score import CplScore
from ..transpiler import FunctionDeclaration, TranspilerContext, add_lib
from ..utils import FLOAT_PREC

_ = 0


def lib_time(ctx: TranspilerContext, _):
    tr = ctx.transpiler
    tr.files["__load__"].append("scoreboard players set __time__time__ 0")
    tr.tickFile.append("scoreboard players add __time__time__ 1")


def lib_ftime(ctx: TranspilerContext, _):
    lib_time(ctx, _)
    tr = ctx.transpiler
    tr.files["__load__"].append(
        f"scoreboard players set FTIME_FLOAT_PREC __temp__ {int(FLOAT_PREC / 20)}"
    )
    ctx.file.append(
        f"scoreboard players operation __ftime__time__ *= FTIME_FLOAT_PREC __temp__"
    )


add_lib(FunctionDeclaration(
    type="python",
    name="time",
    returns=CplScore(None, "__time__time__ --temp-", "int"),
    arguments=[],
    function=lib_time,
))

add_lib(FunctionDeclaration(
    type="python",
    name="ftime",
    returns=CplScore(None, "__ftime__time__ --temp-", "float"),
    arguments=[],
    function=lib_ftime,
))
