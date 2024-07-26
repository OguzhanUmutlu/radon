import json
from typing import List

from .base import CompileTimeValue
from .float import CplFloat
from .int import CplInt
from .string import CplString
from ..error import raise_syntax_error
from ..tokenizer import Token
from ..utils import CplDefArray, CplDefTuple


class CplTuple(CompileTimeValue):
    def __init__(self, token, value):
        # type: (Token | None, List[CompileTimeValue]) -> None
        self.unique_type: CplDefArray
        super().__init__(token)
        self.value = value
        self.unique_type = CplDefTuple(list(map(lambda x: x.unique_type, value)))
        ls = []
        for v in value:
            vl = v.get_py_value()
            if vl is None:
                raise_syntax_error("Tuples(constant arrays) cannot have non-literal values", token)
            ls.append(vl)
        self._py_val = ls

    def get_py_value(self):
        return self._py_val

    def _get_index(self, ctx, index: CompileTimeValue):
        if isinstance(index, CplString) and index.value == "length":
            return len(self.value)
        if isinstance(index, CplInt) or isinstance(index, CplString):
            try:
                return self.value[int(index.value)]
            except IndexError:
                return None
        if isinstance(index, CplFloat):
            return None
        return None

    def _get_slice(self, ctx, index1, index2, index3):
        # TODO: this
        return None

    def _call_index(self, ctx, index: str, arguments: List[CompileTimeValue]):
        return None

    def tellraw_object(self, ctx):
        return json.dumps(self._py_val)
