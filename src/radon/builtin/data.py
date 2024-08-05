import json
from typing import List

from ..cpl.int import CplInt
from ..cpl.nbt import val_nbt, CplNBT
from ..cpl.nbtstring import CplStringNBT
from ..cpl.object import CplObject
from ..cpl.score import CplScore
from ..error import raise_syntax_error
from ..tokenizer import GroupToken, cpl_def_from_tokens, Token
from ..transpiler import TranspilerContext, add_lib, CustomCplObject, FunctionDeclaration
from ..utils import VariableDeclaration, TokenType, get_uuid


def data_helper(s):
    if s[0] == "@":
        return "entity " + s
    if s[0] in list("0123456789~^-."):
        return "block " + s
    return "storage " + s


def lib_data_get(ctx: TranspilerContext, args: List[GroupToken], token: GroupToken):
    if len(args) != 2:
        raise_syntax_error(f"Expected 2 arguments for Data.get()", token)
    cpl_def = cpl_def_from_tokens(ctx.transpiler.classes, args[0].children)
    return val_nbt(token, data_helper(args[1].value), cpl_def)


def lib_data_set(ctx: TranspilerContext, args: List[GroupToken], token: GroupToken):
    if len(args) != 2:
        raise_syntax_error(f"Expected 2 arguments for Data.set()", token)
    expr = args[1].cpl(ctx)
    cmd = f"data modify {data_helper(args[0].value)} set {expr.get_data_str(ctx)}"
    ctx.transpiler.run_cmd(ctx, Token(cmd, TokenType.POINTER, 0, len(cmd)))
    return expr


def lib_data_append(ctx: TranspilerContext, args: List[GroupToken], token: GroupToken):
    if len(args) != 2:
        raise_syntax_error(f"Expected 2 arguments for Data.append()", token)
    expr = args[1].cpl(ctx)
    cmd = f"data modify {data_helper(args[0].value)} append {expr.get_data_str(ctx)}"
    ctx.transpiler.run_cmd(ctx, Token(cmd, TokenType.POINTER, 0, len(cmd)))
    return expr


def lib_data_merge(ctx: TranspilerContext, args: List[GroupToken], token: GroupToken):
    if len(args) != 2:
        raise_syntax_error(f"Expected 2 arguments for Data.merge()", token)
    expr = args[1].cpl(ctx)
    if expr.unique_type.type not in {"array", "object", "tuple"}:
        raise_syntax_error(f"Expected a merge-able object for the second argument of Data.merge()", token)
    if " " in args[0].value:
        cmd = f"data modify {data_helper(args[0].value)} merge {expr.get_data_str(ctx)}"
    else:
        py_val = expr.get_py_value()
        if py_val is None or not isinstance(expr, CplObject):
            raise_syntax_error(
                f"Expected a literal object for the first argument of Data.merge() when the merging nbt location is an nbt root",
                token)
        cmd = f"data merge {data_helper(args[0].value)} {json.dumps(py_val)}"
    ctx.transpiler.run_cmd(ctx, Token(cmd, TokenType.POINTER, 0, len(cmd)))
    return expr


def lib_data_remove(ctx: TranspilerContext, args: List[GroupToken], token: GroupToken):
    if len(args) != 1:
        raise_syntax_error(f"Expected 1 argument for Data.remove()", token)
    cmd = f"data remove {data_helper(args[0].value)}"
    ctx.transpiler.run_cmd(ctx, Token(cmd, TokenType.POINTER, 0, len(cmd)))
    return CplInt(token, 0)


def lib_vset(ctx: TranspilerContext, args: List[GroupToken], token: GroupToken):
    if len(args) != 2:
        raise_syntax_error(f"Expected 2 arguments for vset()", token)
    val = args[0].cpl(ctx)
    if isinstance(val, CplNBT):
        cmd = f"data modify {val.location} set value {args[1].value}"
    elif isinstance(val, CplScore):
        cmd = f"scoreboard players {val.location} set {args[1].value}"
    else:
        raise_syntax_error(f"Expected an nbt/score pointer for the first argument of vset()", token)
        raise ValueError("")
    ctx.transpiler.run_cmd(ctx, Token(cmd, TokenType.POINTER, 0, len(cmd)))
    return CplInt(token, 0)


def lib_mset(ctx: TranspilerContext, args: List[GroupToken], token: GroupToken):
    if len(args) != 2:
        raise_syntax_error(f"Expected 2 arguments for mset()", token)
    val = args[0].cpl(ctx)
    if isinstance(val, CplNBT):
        cmd = f"data modify {val.location} set from {data_helper(args[1].value)}"
    elif isinstance(val, CplScore):
        cmd = f"scoreboard players operation {val.location} = {args[1].value}"
    else:
        raise_syntax_error(f"Expected an nbt/score pointer for the first argument of mset()", token)
        raise ValueError("")
    ctx.transpiler.run_cmd(ctx, Token(cmd, TokenType.POINTER, 0, len(cmd)))
    return CplInt(token, 0)


def lib_mstr(ctx: TranspilerContext, args: List[GroupToken], token: GroupToken):
    if len(args) != 1:
        raise_syntax_error(f"Expected 1 argument for mstr()", token)
    nbt_loc = f"temp _{get_uuid()}"
    cmd = f'data modify {nbt_loc} set value "{args[0].value}"'
    ctx.transpiler.run_cmd(ctx, Token(cmd, TokenType.POINTER, 0, len(cmd)))
    return CplStringNBT(token, nbt_loc)


def lib_run_cmd(ctx: TranspilerContext, args: List[GroupToken], token: GroupToken):
    if len(args) != 1:
        raise_syntax_error(f"Expected 1 argument for runCommand()", token)
    cmd = args[0].value
    return ctx.transpiler.run_cmd(ctx, Token(cmd, TokenType.POINTER, 0, len(cmd)))


add_lib(VariableDeclaration(
    name="Data",
    type=CustomCplObject({}, {
        "get": lib_data_get,
        "set": lib_data_set,
        "append": lib_data_append,
        "merge": lib_data_merge,
        "remove": lib_data_remove
    }),
    constant=True
), FunctionDeclaration(
    name="vset",
    type="python-raw",
    function=lib_vset
), FunctionDeclaration(
    name="mset",
    type="python-raw",
    function=lib_mset
), FunctionDeclaration(
    name="mstr",
    type="python-raw",
    function=lib_mstr
), FunctionDeclaration(
    name="runCommand",
    type="python-raw",
    function=lib_run_cmd
))
