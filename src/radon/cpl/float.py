from math import sqrt
from typing import Union, List

from ._literal import CplLiteral
from .base import CompileTimeValue
from ..error import raise_syntax_error
from ..tokenizer import Token
from ..utils import FLOAT_TYPE, FLOAT_PREC, TokenType


class CplFloat(CplLiteral):
    def __init__(self, token: Union[Token, None], value: float):
        value = float(value)
        if token is None:
            token = Token(str(value), TokenType.FLOAT_LITERAL, 0, len(str(value)))
        super().__init__(token, value)
        self.unique_type = FLOAT_TYPE

    def get_py_value(self):
        return self.value

    def as_int(self):
        return CplInt(self.token, self.value)

    def as_string(self):
        return CplString(self.token, self.value)

    def _cache(self, ctx, score_loc=None, nbt_loc=None, force=None, force_t=None):
        t = force_t or "float"
        v = self.value
        if force_t == "int":
            v = int(self.value)
        if force == "nbt":
            ctx.file.append(f"data modify {nbt_loc} set value {v}")
            return CplFloatNBT(self.token, nbt_loc)
        if t == "float":
            v = int(v * FLOAT_PREC)
        ctx.file.append(f"scoreboard players set {score_loc} {v}")
        return CplScore(self.token, score_loc)

    def get_data_str(self, ctx):
        return f"value {self.value}"

    def _get_index(self, ctx, index: CompileTimeValue):
        return None

    def _get_slice(self, ctx, index1, index2, index3):
        return None

    def _call_index(self, ctx, index: str, arguments: List[CompileTimeValue]):
        if index == "toString":
            if len(arguments) > 0:
                return 0
            return self.as_string()
        if index == "sqrt":
            return CplFloat(self.token, sqrt(self.value))
        if index == "cbrt":
            return CplFloat(self.token, self.value ** (1 / 3))
        if index == "int":
            if len(arguments) > 0:
                raise_syntax_error("Expected 0 arguments for <float>.int()", self.token)
                assert False
            return self.as_int()
        if index == "float":
            if len(arguments) > 0:
                raise_syntax_error("Expected 0 arguments for <float>.float()", self.token)
                assert False
            return self

    def tellraw_object(self, ctx):
        return f"'{self.value}'"


from .int import CplInt
from .nbtfloat import CplFloatNBT
from .score import CplScore
from .string import CplString
from ._number import make_num

make_num(CplInt)
