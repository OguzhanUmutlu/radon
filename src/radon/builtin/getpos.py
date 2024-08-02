from typing import List

from ..cpl._base import CompileTimeValue
from ..cpl.nbtarray import CplArrayNBT
from ..error import raise_syntax_error
from ..tokenizer import Token
from ..transpiler import FunctionDeclaration, TranspilerContext, add_lib
from ..utils import CplDefArray, FLOAT_TYPE


def lib_get_pos(ctx: TranspilerContext, args: List[CompileTimeValue], token: Token | None):
    if len(args) != 0:
        raise_syntax_error("Expected 0 arguments", token)
    ctx.transpiler.files["__getpos__/getpos"] = [
        "data modify storage __getpos__ pos set from entity @s Pos",
        "kill @s"
    ]
    ctx.file.append(f"execute summon marker run function {ctx.transpiler.pack_namespace}:__getpos__/getpos")
    return CplArrayNBT(token, "storage __getpos__ pos", CplDefArray(FLOAT_TYPE))


add_lib(FunctionDeclaration(
    type="python-cpl",
    name="getpos",
    function=lib_get_pos
))
