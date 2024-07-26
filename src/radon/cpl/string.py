import json
from typing import Union, List

from ._literal import CplLiteral
from .base import CompileTimeValue
from ..tokenizer import Token
from ..utils import STRING_TYPE, TokenType, get_expr_id


class CplString(CplLiteral):
    def __init__(self, token, value):
        # type: (Union | None, str) -> None
        value = str(value)
        if token is None:
            token = Token(str(value), TokenType.STRING_LITERAL, 0, len(str(value)))
        super().__init__(token, value)
        self.unique_type = STRING_TYPE

    def get_py_value(self):
        return self.value

    def _cache(self, ctx, score_loc=None, nbt_loc=None, force=None, force_t=None):
        if force == "score":
            raise ValueError("Cannot store string as score")
        ctx.file.append(f"data modify {nbt_loc} set {self.get_data_str(ctx)}")
        return CplStringNBT(self.token, nbt_loc)

    def get_data_str(self, ctx):
        return f"value {json.dumps(self.value)}"

    def _get_index(self, ctx, index: CompileTimeValue):
        if isinstance(index, CplString) and index.value == "length":
            return CplInt(self.token, len(self.value))
        return None

    def _get_slice(self, ctx, index1, index2, index3):
        return None

    def _call_index(self, ctx, index: str, arguments: List[CompileTimeValue]):
        if index == "toString":
            if len(arguments) > 0:
                return 0
            return self
        return None

    def _add(self, ctx, cpl):
        if isinstance(cpl, CplString):
            return CplString(self.token, self.value + cpl.value)
        if not isinstance(cpl, CplStringNBT):
            return None
        eid = f"storage temp _{get_expr_id()}"
        file_name = ctx.transpiler.get_temp_file_name(
            f"$data modify {eid} set value '{self.value}$(_0)'")
        cpl.cache(ctx, nbt_loc="string_concat _0", force="nbt")
        ctx.file.append(f"function {ctx.transpiler.pack_namespace}:{file_name} with storage string_concat")
        return CplStringNBT(self.token, eid)

    def tellraw_object(self, ctx):
        return json.dumps(self.value)


from .int import CplInt
from .nbtstring import CplStringNBT
