from typing import List

from ..error import raise_error
from ..tokenizer import GroupToken
from ..transpiler import FunctionDeclaration, TranspilerContext, add_lib, py_to_cpl


def lib_eval(_ctx: TranspilerContext, _args: List[GroupToken], token: GroupToken):
    try:
        return py_to_cpl(eval(token.value[7:-1]))
    except Exception as e:
        raise_error("Eval error", str(e), token)
        return None


def lib_exec(_ctx: TranspilerContext, _args: List[GroupToken], token: GroupToken):
    try:
        _globals = {"result": 0}
        exec(token.value[7:-1], _globals)
        return py_to_cpl(_globals["result"])
    except Exception as e:
        raise_error("Exec error", str(e), token)


add_lib(FunctionDeclaration(
    type="python-raw",
    name="pyeval",
    returns="void",
    function=lib_eval,
))

add_lib(FunctionDeclaration(
    type="python-raw",
    name="pyexec",
    returns="void",
    function=lib_exec,
))
