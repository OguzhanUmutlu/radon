from typing import Union, List

from ._base import CompileTimeValue
from .nbt import CplNBT, object_get_index_nbt, val_nbt
from .tuple import CplTuple
from ..error import raise_syntax_error
from ..tokenizer import Token
from ..utils import CplDefArray, get_uuid


class CplArrayNBT(CplNBT):
    def __init__(self, token: Union[Token, None], location: str, type: CplDefArray):
        super().__init__(token, location, type)
        self.unique_type = type

    def _set(self, ctx, cpl):
        if isinstance(cpl, CplTuple) and len(cpl.value) == 0:
            ctx.file.append(f"data modify {self.location} set value []")
            return self
        return super()._set(ctx, cpl)

    def _get_index(self, ctx, index: CompileTimeValue):
        if isinstance(index, CplString) and index.value == "length":
            eid = f"int_{get_uuid()} __temp__"
            ctx.file.append(f"execute store result score {eid} run data get {self.location}")
            return CplScore(self.token, eid)
        if isinstance(index, CplInt) or isinstance(index, CplString):
            ind = str(index.value)
            if not ind.isnumeric():
                return None
            content = self.unique_type.content
            return val_nbt(self.token, self.location + "[" + ind + "]", content)

        return object_get_index_nbt(ctx, self.unique_type.content, self, index)

    def _call_index(self, ctx, index: str, arguments: List[CompileTimeValue], token):
        if index == "pop":
            if len(arguments) != 0:
                raise_syntax_error("Expected 0 arguments for <array>.pop()", self.token)
            eid = f"storage temp _{get_uuid()}"
            ctx.file.append(f"data modify {eid} set from {self.location}[-1]")
            ctx.file.append(f"data remove {self.location}[-1]")
            return val_nbt(self.token, eid, self.unique_type.content)
        if index == "push":
            if len(arguments) == 0:
                raise_syntax_error("Expected at least 1 argument for array.push()", self.token)
            for arg in arguments:
                ctx.file.append(f"data modify {self.location} append {arg.get_data_str(ctx)}")
            return self.get_index(ctx, CplString(self.token, "length"))
        if index == "insert":
            if len(arguments) != 2:
                raise_syntax_error("Expected 2 arguments for <array>.insert()", self.token)
            a0 = arguments[0]
            a1 = arguments[1]
            if isinstance(a0, CplInt):
                ctx.file.append(f"data modify {self.location} insert {a0.value} {a1.get_data_str(ctx)}")
                return a1
            if isinstance(a0, CplIntNBT):
                fl = []
                ctx.file.append(f"$data modify {self.location} insert $(_0) {a1.get_data_str(ctx)}")
                file_name = ctx.transpiler.get_temp_file_name(fl)
                a0.cache(ctx, nbt_loc="storage array_insert _0", force="nbt")
                ctx.file.append(f"function {ctx.transpiler.pack_namespace}:{file_name} with storage array_insert")
                return a1
            raise_syntax_error("Expected an int as the first argument for array.insert()", self.token)
        if index == "merge":
            if len(arguments) != 1:
                raise_syntax_error("Expected 1 argument for array.merge()", self.token)
            a0 = arguments[0]
            if isinstance(a0, CplArray):
                a0 = a0.cache(ctx)
            if not isinstance(a0, CplArrayNBT):
                raise_syntax_error("Expected an array as the first argument for array.insert()", self.token)
            if a0.unique_type != self.unique_type:
                raise_syntax_error("Expected an array of the same type for array.merge()", self.token)
            ctx.file.append(f"data modify {self.location} merge {a0.get_data_str(ctx)}")
            return self
        return None

    def _add(self, ctx, cpl):
        if self.unique_type != cpl.unique_type:
            return None
        # TODO: array merging
        return None

    def _and(self, ctx, cpl):
        return cpl

    def _or(self, ctx, cpl):
        return self


from .array import CplArray
from .int import CplInt
from .nbtint import CplIntNBT
from .score import CplScore
from .string import CplString
