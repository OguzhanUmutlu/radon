from typing import List

from ..cpl.int import CplInt
from ..error import raise_syntax_error
from ..cpl._base import CompileTimeValue
from ..transpiler import FunctionDeclaration, TranspilerContext, add_lib


def _lib_print(ctx: TranspilerContext, args: List[CompileTimeValue], token, prefix: str, name: str):
    if len(args) < 2:
        raise_syntax_error(f"Invalid arguments. Expected usage: {name}(selector, ...anything)", token)
    prefix = prefix.replace("@", args[0].value)
    if len(args) == 2:
        ctx.file.append(f"{prefix} {args[1].tellraw_object(ctx)}")
    else:
        ctx.file.append(f"{prefix} [{','.join(x.tellraw_object(ctx) for x in args[1:])}]")
    return CplInt(token, 0)


def lib_print(ctx: TranspilerContext, args: List[CompileTimeValue], token):
    return _lib_print(ctx, args, token, "tellraw @", "print")


def lib_print_title(ctx: TranspilerContext, args: List[CompileTimeValue], token):
    return _lib_print(ctx, args, token, "title @ title", "printTitle")


def lib_print_subtitle(ctx: TranspilerContext, args: List[CompileTimeValue], token):
    return _lib_print(ctx, args, token, "title @ subtitle", "printSubtitle")


def lib_print_actionbar(ctx: TranspilerContext, args: List[CompileTimeValue], token):
    return _lib_print(ctx, args, token, "title @ subtitle", "printActionbar")


add_lib(FunctionDeclaration(
    type="python-cpl",
    name="print",
    arguments=[],
    function=lib_print
), FunctionDeclaration(
    type="python-cpl",
    name="printTitle",
    arguments=[],
    function=lib_print_title
), FunctionDeclaration(
    type="python-cpl",
    name="printSubtitle",
    arguments=[],
    function=lib_print_subtitle
), FunctionDeclaration(
    type="python-cpl",
    name="printActionbar",
    arguments=[],
    function=lib_print_actionbar
))
