from typing import Union, Any

from ..tokenizer import Token
from ._base import CompileTimeValue


class CplLiteral(CompileTimeValue):
    def __init__(self, token: Union[Token, None], value: Any):
        super().__init__(token)
        self.value = value
