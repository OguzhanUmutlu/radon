from .base import CompileTimeValue
from ..error import raise_syntax_error
from ..tokenizer import Token
from ..utils import SELECTOR_TYPE, get_expr_id


class CplSelector(CompileTimeValue):
    def __init__(self, token, value):
        # type: (Token | None, str) -> None
        super().__init__(token)
        self.value = value
        self.unique_type = SELECTOR_TYPE

    def get_py_value(self):
        return None

    def _cache(self, ctx, score_loc=None, nbt_loc=None, force=None, force_t=None):
        raise_syntax_error("Selectors cannot be used in operations", self.token)

    def get_data_str(self, ctx):
        raise_syntax_error("Selectors cannot be used in operations", self.token)

    def tellraw_object(self, ctx):
        return '{"selector":"' + self.value + '"}'

    def _and(self, ctx, cpl):
        if isinstance(cpl, CplInt) or isinstance(cpl, CplFloat):
            return self if cpl.value != 0 else CplInt(self.token, 0)
        score_loc = f"int_{get_expr_id()} --temp--"
        ctx.file.append(f"scoreboard players set {score_loc} 0")
        if isinstance(cpl, CplSelector):
            ctx.file.append(f"execute "
                            f"if entity {self.value} "
                            f"if entity {cpl.value} "
                            f"run scoreboard players add {score_loc} 1")
            return CplScore(self.token, score_loc)
        if isinstance(cpl, CplScore):
            ctx.file.append(f"execute "
                            f"unless score {cpl.location} matches 0..0 "
                            f"if entity {self.value} "
                            f"run scoreboard players add {score_loc} 1")
            return CplScore(self.token, score_loc)
        return None

    def _or(self, ctx, cpl):
        if isinstance(cpl, CplInt) or isinstance(cpl, CplFloat):
            return self if cpl.value == 0 else CplInt(self.token, 1)
        score_loc = f"int_{get_expr_id()} --temp--"
        ctx.file.append(f"scoreboard players set {score_loc} 0")
        if isinstance(cpl, CplSelector):
            ctx.file.append(f"execute if entity {self.value} run scoreboard players add {score_loc} 1")
            ctx.file.append(f"execute if entity {cpl.value} run scoreboard players add {score_loc} 1")
            return CplScore(self.token, score_loc)
        if isinstance(cpl, CplScore):
            ctx.file.append(f"execute if entity {self.value} "
                            f"run scoreboard players add {score_loc} 1")
            ctx.file.append(f"execute unless score {cpl.location} matches 0..0 "
                            f"run scoreboard players add {score_loc} 1")
            return CplScore(self.token, score_loc)
        return None


from .float import CplFloat
from .int import CplInt
from .score import CplScore