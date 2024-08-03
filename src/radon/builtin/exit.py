from typing import List

from ..tokenizer import GroupToken
from ..transpiler import FunctionDeclaration, TranspilerContext, add_lib


def lib_exit(ctx: TranspilerContext, _args: List[GroupToken], token: GroupToken):
    ctx.file.append("return " + token.value[5:-1])


add_lib(FunctionDeclaration(
    type="python-raw",
    name="exit",
    returns="void",
    function=lib_exit
))
