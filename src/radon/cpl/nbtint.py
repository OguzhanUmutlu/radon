from typing import Union, List

from ._base import CompileTimeValue
from .nbt import CplNBT
from ..tokenizer import Token
from ..utils import INT_TYPE


class CplIntNBT(CplNBT):
    def __init__(self, token: Union[Token, None], location: str):
        super().__init__(token, location, INT_TYPE)

    def _cache(self, ctx, score_loc=None, nbt_loc=None, force=None, force_t=None):
        if force == "score":
            ctx.file.append(f"execute store result score {score_loc} run data get {self.location}")
            t = "int"
            if force_t == "float":
                ctx.file.append(f"scoreboard players operation {score_loc} *= FLOAT_PREC __temp__")
                t = "float"
            return CplScore(self.token, score_loc, t)
        return super()._cache(ctx, score_loc, nbt_loc, force, force_t)

    def _call_index(self, ctx, index: str, arguments: List[CompileTimeValue], token):
        return self.cache(ctx, force="score")._call_index(ctx, index, arguments, token)


from .score import CplScore
from ._number import make_nbt_num

make_nbt_num(CplIntNBT)
