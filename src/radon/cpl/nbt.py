from typing import Union

from ._base import CompileTimeValue
from ..tokenizer import Token
from ..utils import get_uuid, CplDef, CplDefObject, CplDefArray


class CplNBT(CompileTimeValue):
    def __init__(self, token: Union[Token, None], location: str, type: CplDef):
        super().__init__(token)
        self.location = location
        self.unique_type = type

    def _cache(self, ctx, score_loc=None, nbt_loc=None, force=None, force_t=None):
        if force == "score":
            return None
        if not nbt_loc:
            nbt_loc = f"storage temp _{get_uuid()}"
        ctx.file.append(f"data modify {nbt_loc} set from {self.location}")
        return val_nbt(self.token, nbt_loc, self.unique_type)

    def _set(self, ctx, cpl):
        if self.unique_type != cpl.unique_type:
            return None
        cpl.cache(ctx, nbt_loc=self.location, force="nbt")
        return self

    def tellraw_object(self, ctx):
        ls = self.location.split(" ")
        ls1 = ls[1]
        ls2 = " ".join(ls[2:])
        if ls[0] == "block":
            ls1 = ls[1] + " " + ls[2] + " " + ls[3]
            ls2 = " ".join(ls[4:])
        return '{"' + ls[0] + '":"' + ls1 + '","nbt":"' + ls2 + '"}'

    def get_data_str(self, ctx):
        return f"from {self.location}"


def val_nbt(
        token: Union[Token, None],
        location: str,
        u_type: CplDef
) -> CplNBT:
    ut = u_type.type
    if ut == "int":
        return CplIntNBT(token, location)
    elif ut == "float":
        return CplFloatNBT(token, location)
    elif ut == "string":
        return CplStringNBT(token, location)
    elif isinstance(u_type, CplDefArray):
        return CplArrayNBT(token, location, u_type)
    elif isinstance(u_type, CplDefObject):
        return CplObjectNBT(token, location, u_type)
    raise ValueError("Invalid type")


def object_get_index_nbt(ctx, content_type, cpl, index):
    eid = f"storage object_index _{get_uuid()}"
    file_name = ctx.transpiler.get_temp_file_name("$data modify {eid} set from $(_0).$(_1)")

    cpl.cache(ctx, force="nbt", nbt_loc="object_get_index _0")
    index.cache(ctx, force="nbt", nbt_loc="object_get_index _1")
    ctx.file.append(f"function {ctx.transpiler.pack_namespace}:{file_name} with storage object_get_index")
    return val_nbt(cpl.token, eid, content_type)


from .nbtarray import CplArrayNBT
from .nbtfloat import CplFloatNBT
from .nbtint import CplIntNBT
from .nbtobject import CplObjectNBT
from .nbtstring import CplStringNBT
