import json
from typing import List

from .base import CompileTimeValue
from ..error import raise_syntax_error
from ..tokenizer import Token
from ..utils import CplDefArray


class CplArray(CompileTimeValue):
    def __init__(self, token, value):
        # type: (Token | None, List[CompileTimeValue]) -> None
        self.unique_type: CplDefArray
        super().__init__(token)
        self.value = value
        if len(value) == 0:
            raise_syntax_error("Array cannot be empty", token)
        self.unique_type = CplDefArray(value[0].unique_type)
        for v in value:
            if v.unique_type != value[0].unique_type:
                raise_syntax_error("All array elements must be of the same type", token)

    def get_py_value(self):
        ls = []
        for v in self.value:
            vl = v.get_py_value()
            if vl is None:
                return None
            ls.append(vl)
        return ls

    def _cache(self, ctx, score_loc=None, nbt_loc=None, force=None, force_t=None):
        if force == "score":
            return None
        py_val = self.get_py_value()
        if py_val is not None:
            ctx.file.append(f"data modify {nbt_loc} set value {json.dumps(py_val)}")
        else:
            init = []
            keys = []

            for index, c in enumerate(self.value):
                c_py_val = c.get_py_value()
                if c_py_val is not None:
                    init.append(json.dumps(c_py_val))
                else:
                    init.append(c.unique_type.get_sample_value())
                    keys.append(index)
            ctx.file.append(f"data modify {nbt_loc} set value [{','.join(init)}]")

            for index, v in enumerate(self.value):
                if index in keys:
                    v.cache(ctx, nbt_loc=f"{nbt_loc}[{index}]", force="nbt")
        return CplArrayNBT(self.token, nbt_loc, self.unique_type)

    def _get_index(self, ctx, index: CompileTimeValue):
        if isinstance(index, CplString) and index.value == "length":
            return CplInt(self.token, len(self.value))
        if isinstance(index, CplInt) or isinstance(index, CplString):
            try:
                return self.value[int(index.value)]
            except IndexError:
                return None
        if isinstance(index, CplFloat):
            return None
        return self.cache(ctx).get_index(ctx, index)

    def _get_slice(self, ctx, index1, index2, index3):
        return None

    def _call_index(self, ctx, index: str, arguments: List[CompileTimeValue]):
        return None

    def _add(self, ctx, cpl):
        if isinstance(cpl, CplArray):
            return CplArray(self.token, self.value + cpl.value)
        if not isinstance(cpl, CplArrayNBT):
            return None
        return self.cache(ctx)._add(ctx, cpl)

    def tellraw_object(self, ctx):
        py_v = self.get_py_value()
        if py_v is None:
            return self.cache(ctx).tellraw_object(ctx)
        return json.dumps(py_v)


from .float import CplFloat
from .int import CplInt
from .nbtarray import CplArrayNBT
from .string import CplString
