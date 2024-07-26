from ..error import raise_error
from ..tokenizer import GroupToken
from ..transpiler import FunctionDeclaration, TranspilerContext, add_lib

_ = 0


def lib_eval(ctx: TranspilerContext, token: GroupToken):
    try:
        eval(token.value[7:-1])
    except Exception as e:
        raise_error("Eval error", str(e), token)


add_lib(FunctionDeclaration(
    type="python-raw",
    name="python",
    returns="void",
    function=lib_eval,
))
