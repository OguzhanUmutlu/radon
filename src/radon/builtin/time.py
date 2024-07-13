from ..utils import FunctionDeclaration, TranspilerContext
from ..utils import FLOAT_PREC


def lib_time(ctx: TranspilerContext, _):
    tr = ctx.transpiler
    tr.files["__load__"].append("scoreboard players set __time__time__ 0")
    tr.tickFile.append("scoreboard players add __time__time__ 1")


def lib_ftime(ctx: TranspilerContext, _):
    lib_time(ctx, _)
    tr = ctx.transpiler
    tr.files["__load__"].append(
        f"scoreboard players set FTIME_FLOAT_PREC --temp-- {int(FLOAT_PREC / 20)}"
    )
    ctx.file.append(
        f"scoreboard players operation __ftime__time__ *= FTIME_FLOAT_PREC --temp--"
    )


LIB = [
    FunctionDeclaration(
        type="python",
        name="time",
        returns="int",
        returnId="__time__time__",
        arguments=[],
        direct=True,
        function=lib_time,
    ),
    FunctionDeclaration(
        type="python",
        name="ftime",
        returns="float",
        returnId="__ftime__time__",
        arguments=[],
        direct=True,
        function=lib_ftime,
    ),
]
