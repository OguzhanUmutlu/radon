from typing import List

from ..cpl.base import CompileTimeValue
from ..error import raise_error
from ..transpiler import FunctionDeclaration, TranspilerContext, add_lib, NULL_VALUE

_ = 0


def lib_print(ctx: TranspilerContext, args: List[CompileTimeValue], _):
    ctx.file.append(f"tellraw @a [{','.join(x.tellraw_object(ctx) for x in args)}]")
    return NULL_VALUE


add_lib(FunctionDeclaration(
    type="python-cpl",
    name="print",
    arguments=[],
    function=lib_print
))
