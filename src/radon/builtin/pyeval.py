from ..cpl.float import CplFloat
from ..cpl.int import CplInt
from ..cpl.string import CplString
from ..error import raise_error
from ..tokenizer import GroupToken
from ..transpiler import FunctionDeclaration, TranspilerContext, add_lib


def py_to_cpl(v):
    if isinstance(v, str):
        return CplString(None, v)
    if isinstance(v, int):
        return CplInt(None, v)
    if isinstance(v, float):
        return CplFloat(None, v)
    if isinstance(v, bool):
        return CplInt(None, 1 if v else 0)
    return CplInt(None, 0)


def lib_eval(_ctx: TranspilerContext, token: GroupToken):
    try:
        return py_to_cpl(eval(token.value[7:-1]))
    except Exception as e:
        raise_error("Eval error", str(e), token)
        return None


def lib_exec(_ctx: TranspilerContext, token: GroupToken):
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
