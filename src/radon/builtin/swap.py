from typing import List

from ..cpl import Cpl, CplInt
from ..error import raise_syntax_error
from ..tokenizer import Token
from ..transpiler import FunctionDeclaration, TranspilerContext, add_lib


def lib_swap(ctx: TranspilerContext, args: List[Cpl], token: Token | None):
    if len(args) != 2:
        raise_syntax_error("Expected 2 arguments for <array>.swap()", token)
    arg0_cached = args[0].cache(ctx)
    args[0].compute(ctx, "=", args[1], token)
    args[1].compute(ctx, "=", arg0_cached, token)
    return CplInt(token, 0)


add_lib(FunctionDeclaration(
    type="python-cpl",
    name="swap",
    arguments=[],
    function=lib_swap
))
