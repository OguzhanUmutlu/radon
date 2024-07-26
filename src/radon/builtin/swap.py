from typing import List

from ..cpl.base import CompileTimeValue
from ..error import raise_syntax_error
from ..tokenizer import Token
from ..transpiler import FunctionDeclaration, TranspilerContext, add_lib, NULL_VALUE

_ = 0


def lib_swap(ctx: TranspilerContext, args: List[CompileTimeValue], token: Token | None):
    if len(args) != 2:
        raise_syntax_error("Expected 2 arguments for <array>.swap()", token)
    arg0_cached = args[0].cache(ctx)
    args[0]._set(ctx, args[1])
    args[1]._set(ctx, arg0_cached)
    return NULL_VALUE


add_lib(FunctionDeclaration(
    type="python-cpl",
    name="swap",
    arguments=[],
    function=lib_swap
))
