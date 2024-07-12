from error import raise_error
from tokenizer import GroupToken, Token
from typing import List
from utils import FunctionDeclaration, TranspilerContext


def lib_eval(ctx: TranspilerContext, arguments: List[List[Token]], token: GroupToken):
    try:
        eval(token.value[7:-1])
    except Exception as e:
        raise_error("Eval error", str(e), token)


LIB = FunctionDeclaration(
    type="python-raw",
    name="python",
    returns="void",
    returnId="null",
    direct=True,
    function=lib_eval,
)
