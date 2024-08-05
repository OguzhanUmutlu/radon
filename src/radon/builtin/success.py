from typing import List

from ..cpl import CplScore
from ..tokenizer import GroupToken, Token
from ..transpiler import FunctionDeclaration, TranspilerContext, add_lib
from ..utils import TokenType


def lib_success(ctx: TranspilerContext, _args: List[GroupToken], token: GroupToken):
    c = token.value[8:-1]
    ctx.transpiler.run_cmd(ctx, Token(c, TokenType.POINTER, 0, len(c)), "int_success __temp__", "success")


add_lib(FunctionDeclaration(
    type="python-raw",
    name="success",
    returns=CplScore(None, "int_success __temp__"),
    function=lib_success
))
