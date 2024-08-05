from math import isqrt
from typing import List

from ._literal import CplLiteral
from ._base import CompileTimeValue
from ..error import raise_syntax_error
from ..tokenizer import Token
from ..utils import INT_TYPE, TokenType, FLOAT_PREC


class CplInt(CplLiteral):
    def __init__(self, token, value):
        # type: (Token | None, int) -> None
        value = int(value)
        if token is None:
            token = Token(str(value), TokenType.INT_LITERAL, 0, len(str(value)))
        super().__init__(token, value)
        self.unique_type = INT_TYPE

    def get_py_value(self):
        return self.value

    def as_float(self):
        return CplFloat(self.token, self.value)

    def as_string(self):
        return CplString(self.token, self.value)

    def _cache(self, ctx, score_loc=None, nbt_loc=None, force=None, force_t=None):
        v = self.value
        if force_t == "float":
            v *= FLOAT_PREC
        if force == "nbt":
            ctx.file.append(f"data modify {nbt_loc} set value {v}")
            return CplIntNBT(self.token, nbt_loc)
        ctx.file.append(f"scoreboard players set {score_loc} {v}")
        return CplScore(self.token, score_loc)

    def get_data_str(self, ctx):
        return f"value {self.value}"

    def _call_index(self, ctx, index: str, arguments: List[CompileTimeValue], token):
        if index == "toString":
            if len(arguments) > 0:
                return 0
            return self.as_string()
        if index == "sqrt":
            return CplInt(self.token, isqrt(self.value))
        if index == "int":
            if len(arguments) > 0:
                raise_syntax_error("Expected 0 arguments for <int>.int()", self.token)
                assert False
            return self
        if index == "float":
            if len(arguments) > 0:
                raise_syntax_error("Expected 0 arguments for <int>.float()", self.token)
                assert False
            return self.as_float()

    def tellraw_object(self, ctx):
        return {"text": str(self.value)}


from .nbtint import CplIntNBT
from .score import CplScore
from .string import CplString
from .float import CplFloat
from ._number import make_num

make_num(CplInt)
