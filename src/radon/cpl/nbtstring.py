from typing import Union

from ._base import CompileTimeValue
from .nbt import CplNBT
from ..error import raise_syntax_error
from ..tokenizer import Token
from ..utils import STRING_TYPE, get_uuid


class CplStringNBT(CplNBT):
    def __init__(self, token: Union[Token, None], location: str):
        super().__init__(token, location, STRING_TYPE)

    def _get_index(self, ctx, index: CompileTimeValue):
        if isinstance(index, CplString) and index.value == "length":
            eid = f"int_{get_uuid()} __temp__"
            ctx.file.append(f"execute store result score {eid} run data get {self.location}")
            return CplScore(self.token, eid)
        return None

    def _call_index(self, ctx, index, arguments, token):
        if index == "toString":
            if len(arguments) > 0:
                return 0
            return self
        if index == "substr":
            if len(arguments) != 2:
                return 2
            arg0 = arguments[0]
            arg1 = arguments[1]
            if not isinstance(arg0, CplInt) or not isinstance(arg1, CplInt):
                raise_syntax_error("Not implemented", token)
            res = CplStringNBT(self.token, f"storage temp _{get_uuid()}")
            ctx.file.append(f"data modify {res.location} set string {self.location} {arg0.value} {arg1.value}")
            return res
        return None

    def _set_add(self, ctx, cpl):
        if isinstance(cpl, CplString):
            file_name = ctx.transpiler.get_temp_file_name(
                f"$data modify {self.location} set value '$(_0){cpl.value}'")
            self.cache(ctx, nbt_loc="string_concat _0", force="nbt")
            ctx.file.append(f"function {ctx.transpiler.pack_namespace}:{file_name} with storage string_concat")
            return self
        if not isinstance(cpl, CplStringNBT):
            file_name = ctx.transpiler.get_temp_file_name(
                f"$data modify {self.location} set value '$(_0)$(_1)'")
            self.cache(ctx, nbt_loc="string_concat _0", force="nbt")
            cpl.cache(ctx, nbt_loc="string_concat _1", force="nbt")
            ctx.file.append(f"function {ctx.transpiler.pack_namespace}:{file_name} with storage string_concat")
            return self
        return None

    def _add(self, ctx, cpl):
        if isinstance(cpl, CplString):
            eid = f"storage temp _{get_uuid()}"
            file_name = ctx.transpiler.get_temp_file_name(
                f"$data modify {eid} set value '$(_0){cpl.value}'")
            self.cache(ctx, nbt_loc="string_concat _0", force="nbt")
            ctx.file.append(f"function {ctx.transpiler.pack_namespace}:{file_name} with storage string_concat")
            return CplStringNBT(self.token, eid)
        if not isinstance(cpl, CplStringNBT):
            eid = f"storage temp _{get_uuid()}"
            file_name = ctx.transpiler.get_temp_file_name(
                f"$data modify {eid} set value '$(_0)$(_1)'")
            self.cache(ctx, nbt_loc="string_concat _0", force="nbt")
            cpl.cache(ctx, nbt_loc="string_concat _1", force="nbt")
            ctx.file.append(f"function {ctx.transpiler.pack_namespace}:{file_name} with storage string_concat")
            return CplStringNBT(self.token, eid)
        return None

    def _and(self, ctx, cpl):
        return cpl._and(ctx, self.get_index(ctx, CplString(self.token, "length"), self.token))

    def _or(self, ctx, cpl):
        return cpl._or(ctx, self.get_index(ctx, CplString(self.token, "length"), self.token))


from .string import CplString
from .int import CplInt
from .score import CplScore
