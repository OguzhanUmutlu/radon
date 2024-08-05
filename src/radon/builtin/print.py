from typing import List

from ..cpl import CplString, Cpl, CplInt, CplSelector
from ..utils import VariableDeclaration
from ..error import raise_syntax_error
from ..transpiler import FunctionDeclaration, TranspilerContext, add_lib, CustomCplObject


def _lib_print(ctx: TranspilerContext, args: List[Cpl], token, prefix: str, name: str):
    if len(args) < 1:
        raise_syntax_error(f"Invalid arguments. Expected usage: {name}(selector, ...anything)", token)
    if not isinstance(args[0], CplSelector):
        args.insert(0, CplSelector(token, "@a"))
    prefix = prefix.replace("@", args[0].value)
    if len(args) == 2:
        ctx.file.append(f"{prefix} {args[1].tellraw_object_str(ctx)}")
    else:
        ctx.file.append(f"{prefix} [{", ".join(x.tellraw_object_str(ctx) for x in args[1:])}]")
    return CplInt(token, 0)


def lib_print(ctx: TranspilerContext, args: List[Cpl], token):
    return _lib_print(ctx, args, token, "tellraw @", "print")


def lib_print_title(ctx: TranspilerContext, args: List[Cpl], token):
    return _lib_print(ctx, args, token, "title @ title", "printTitle")


def lib_print_subtitle(ctx: TranspilerContext, args: List[Cpl], token):
    return _lib_print(ctx, args, token, "title @ subtitle", "printSubtitle")


def lib_print_actionbar(ctx: TranspilerContext, args: List[Cpl], token):
    return _lib_print(ctx, args, token, "title @ actionbar", "printActionbar")


class CplFormat(Cpl):
    def __init__(self, token, fmt, value: Cpl):
        super().__init__(token)
        self.fmt = fmt
        self.value = value

    def _raw_call_index(self, ctx, index, args, token):
        if index == "hover":
            if len(args) != 2:
                raise_syntax_error("Expected 2 arguments for fmt.hover()", token)
            if "hoverEvent" in self.fmt:
                raise_syntax_error("fmt.hover() already set", token)
            args[0] = args[0].cpl(ctx)
            self.fmt["hoverEvent"] = {"action": args[0].value, "contents": lambda: args[1].value}
            return self
        return None

    def _call_index(self, ctx, index, args, token):
        if index == "insertion":
            if len(args) != 1:
                raise_syntax_error("Expected 1 argument for fmt.insertion()", token)
            if "insertion" in self.fmt:
                raise_syntax_error("fmt.insertion() already set", token)
            if not isinstance(args[0], CplString):
                raise_syntax_error("Expected a string argument for fmt.insertion()", token)
            self.fmt["insertion"] = args[0].value
            return self
        if index == "extend":
            if len(args) != 1:
                raise_syntax_error("Expected 1 argument for fmt.extend()", token)
            if not isinstance(args[0], CplFormat):
                raise_syntax_error("Expected a RadonFormat argument for fmt.extend()", token)
            if "extra" not in self.fmt:
                self.fmt["extra"] = []
            self.fmt["extra"].append(args[0].tellraw_object(ctx))
            return self
        if index == "click":
            if len(args) != 2:
                raise_syntax_error("Expected 2 arguments for fmt.click()", token)
            if "clickEvent" in self.fmt:
                raise_syntax_error("fmt.click() already set", token)
            if not isinstance(args[0], CplString) or not isinstance(args[1], CplString):
                raise_syntax_error("Expected 2 string arguments for fmt.click()", token)
            self.fmt["clickEvent"] = {"action": args[0].value, "value": args[1].value}
            return self
        return None

    def tellraw_object(self, ctx):
        obj = {}
        obj.update(self.value.tellraw_object(ctx))
        obj.update(self.fmt)
        return obj


def lib_fmt(ctx, args, token):
    fmt = {}
    for arg in args[:-1]:
        value = arg.value
        if (value in {"black", "dark_blue", "dark_green", "dark_aqua", "dark_red", "dark_purple", "gold", "gray",
                      "dark_gray", "blue", "green", "aqua", "red", "light_purple", "yellow", "white"}
                or value[0] == "#"):
            if "color" in fmt:
                raise_syntax_error("Cannot use multiple colors", token)
            fmt["color"] = value
        elif value in {"bold", "italic", "underlined", "strikethrough", "obfuscated"}:
            fmt[value] = True
        else:
            raise_syntax_error("Invalid format style", arg)

    val = args[-1].cpl(ctx)
    while isinstance(val, CplFormat):
        fmt.update(val.fmt)
        val = val.value
    return CplFormat(token, fmt, val)


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
), VariableDeclaration(
    name="fmt",
    type=CustomCplObject(),
    constant=True
), FunctionDeclaration(
    type="python-raw",
    name="fmt",
    function=lib_fmt
))
