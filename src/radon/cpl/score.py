from typing import Union, List

from .base import CompileTimeValue
from ..error import raise_syntax_error
from ..tokenizer import Token
from ..utils import INT_TYPE, get_expr_id, FLOAT_PREC, FLOAT_TYPE, inv_cmp


class CplScore(CompileTimeValue):
    def __init__(
            self,
            token: Union[Token, None],
            location: str,
            type: str | None = None,
    ):
        super().__init__(token)
        if type is None:
            type = location.split("_")[0]  # type: ignore
        self.location = location
        if type == "int":
            self.unique_type = INT_TYPE
        elif type == "float":
            self.unique_type = FLOAT_TYPE

    def as_int(self, ctx, score_loc=None):
        if self.unique_type.type == "int":
            return self
        eid = score_loc or f"int_{get_expr_id()} --temp--"
        ctx.file.append(f"scoreboard players operation {eid} = {self.location}")
        ctx.file.append(f"scoreboard players operation {eid} /= FLOAT_PREC --temp--")
        return CplScore(self.token, eid)

    def as_float(self, ctx, score_loc=None):
        if self.unique_type.type == "float":
            return self
        eid = score_loc or f"float_{get_expr_id()} --temp--"
        ctx.file.append(f"scoreboard players operation {eid} = {self.location}")
        ctx.file.append(f"scoreboard players operation {eid} *= FLOAT_PREC --temp--")
        return CplScore(self.token, eid)

    def _force_float(self, ctx):  # ONLY USE THIS ON RECENTLY CACHED SCORES!
        if self.unique_type == FLOAT_TYPE:
            return
        self.unique_type = FLOAT_TYPE
        ctx.file.append(f"scoreboard players operation {self.location} *= FLOAT_PREC --temp--")

    def _force_int(self, ctx):  # ONLY USE THIS ON RECENTLY CACHED SCORES!
        if self.unique_type == FLOAT_TYPE:
            return
        self.unique_type = FLOAT_TYPE
        ctx.file.append(f"scoreboard players operation {self.location} /= FLOAT_PREC --temp--")

    def _force_type(self, ctx, type):  # ONLY USE THIS ON RECENTLY CACHED SCORES!
        if type == "int":
            return self._force_int(ctx)
        self._force_float(ctx)

    def _cache(self, ctx, score_loc=None, nbt_loc=None, force=None, force_t=None):
        if force == "nbt":
            t_have = self.unique_type.type
            mul = "int 1"
            if force_t == "float" and t_have == "int":
                mul = f"int {FLOAT_PREC}"
            if t_have == "float":
                mul = f"float {1 / FLOAT_PREC:.7f}"
            ctx.file.append(f"execute store result {nbt_loc} {mul} run scoreboard players get {self.location}")
            return val_nbt(self.token, nbt_loc, force_t or self.unique_type)
        if not score_loc:
            score_loc = f"{self.unique_type.type}_{get_expr_id()} --temp--"
        ctx.file.append(
            f"scoreboard players operation {score_loc} = {self.location}"
        )
        score = CplScore(self.token, score_loc, self.unique_type.type)
        if force_t == "int" or force_t == "float":
            score._force_type(ctx, force_t)
        return score

    def _get_index(self, ctx, index: CompileTimeValue):
        return None

    def _get_slice(self, ctx, index1, index2, index3):
        return None

    def _call_index(self, ctx, index: str, arguments: List[CompileTimeValue]):
        t = self.unique_type.type
        if index == "sqrt":
            return ctx.transpiler.run_function_with_cpl(ctx, "isqrt" if t == "int" else "sqrt", [self], self.token)
        if index == "cbrt":
            return ctx.transpiler.run_function_with_cpl(ctx, "cbrt", [self.as_float(ctx)], self.token)
        if index == "int":
            if len(arguments) > 0:
                raise_syntax_error("Expected 0 arguments for <score>.int()", self.token)
                assert False
            return self.as_int(ctx)
        if index == "float":
            if len(arguments) > 0:
                raise_syntax_error("Expected 0 arguments for <score>.int()", self.token)
                assert False
            return self.as_float(ctx)
        return None

    def __score_help(self, cpl):
        t_want = self.unique_type.type
        t_have = cpl.unique_type.type
        v = cpl.value
        if t_want == "int" and t_have == "float":
            v = int(v)
        if t_want == "float":
            v = int(v * FLOAT_PREC)
        return v

    def _set(self, ctx, cpl):
        if isinstance(cpl, CplInt) or isinstance(cpl, CplFloat):
            v = self.__score_help(cpl)
            ctx.file.append(f"scoreboard players set {self.location} {v}")
            return self
        t_want = self.unique_type.type
        t_have = cpl.unique_type.type
        if not isinstance(cpl, CplScore) and not isinstance(cpl, CplIntNBT) and not isinstance(cpl, CplFloatNBT):
            return None
        if isinstance(cpl, CplScore):
            ctx.file.append(f"scoreboard players operation {self.location} = {cpl.location}")
        else:
            if t_want == "int":
                ctx.file.append(f"execute result store score {self.location} run data get {cpl.location}")
            ctx.file.append(f"execute store result score {self.location} run data get {cpl.location} {FLOAT_PREC}")
            return self
        if t_want == "int" and t_have == "float":
            ctx.file.append(f"scoreboard players operation {self.location} /= FLOAT_PREC --temp--")
        if t_want == "float" and t_have == "int":
            ctx.file.append(f"scoreboard players operation {self.location} *= FLOAT_PREC --temp--")
        return self

    def _set_add(self, ctx, cpl):
        if isinstance(cpl, CplInt) or isinstance(cpl, CplFloat):
            ctx.file.append(f"scoreboard players add {self.location} {self.__score_help(cpl)}")
            return self
        if isinstance(cpl, CplScore):
            t_want = self.unique_type.type
            t_have = cpl.unique_type.type
            if t_want != t_have:
                cpl = cpl.cache(ctx, force=t_want)
            ctx.file.append(f"scoreboard players operation {self.location} += {cpl.location}")
            return self
        if not isinstance(cpl, CplIntNBT) and not isinstance(cpl, CplFloatNBT):
            return None
        return self._set_add(ctx, cpl.cache(ctx, force="score", force_t=self.unique_type.type))

    def _set_sub(self, ctx, cpl):
        if isinstance(cpl, CplInt) or isinstance(cpl, CplFloat):
            ctx.file.append(f"scoreboard players remove {self.location} {self.__score_help(cpl)}")
            return self
        if isinstance(cpl, CplScore):
            t_want = self.unique_type.type
            t_have = cpl.unique_type.type
            if t_want != t_have:
                cpl = cpl.cache(ctx, force_t=t_want)
            ctx.file.append(f"scoreboard players operation {self.location} -= {cpl.location}")
            return self
        if not isinstance(cpl, CplIntNBT) and not isinstance(cpl, CplFloatNBT):
            return None
        return self._set_sub(ctx, cpl.cache(ctx, force="score", force_t=self.unique_type.type))

    def _set_mul(self, ctx, cpl):
        if isinstance(cpl, CplInt) or isinstance(cpl, CplFloat):
            return self._set_mul(ctx, cpl.cache(ctx, force="score", force_t=self.unique_type.type))
        if isinstance(cpl, CplScore):
            ctx.file.append(f"scoreboard players operation {self.location} *= {cpl.location}")
            if cpl.unique_type.type == "float":
                ctx.file.append(f"scoreboard players operation {self.location} /= FLOAT_PREC --temp--")
            return self
        if not isinstance(cpl, CplIntNBT) and not isinstance(cpl, CplFloatNBT):
            return None
        return self._set_mul(ctx, cpl.cache(ctx, force="score", force_t=self.unique_type.type))

    def _set_div(self, ctx, cpl):
        if isinstance(cpl, CplInt) or isinstance(cpl, CplFloat):
            return self._set_div(ctx, cpl.cache(ctx, force="score", force_t=self.unique_type.type))
        if isinstance(cpl, CplScore):
            ctx.file.append(f"scoreboard players operation {self.location} /= {cpl.location}")
            if cpl.unique_type.type == "float":
                ctx.file.append(f"scoreboard players operation {self.location} *= FLOAT_PREC --temp--")
            return self
        if not isinstance(cpl, CplIntNBT) and not isinstance(cpl, CplFloatNBT):
            return None
        return self._set_div(ctx, cpl.cache(ctx, force="score", force_t=self.unique_type.type))

    def _set_mod(self, ctx, cpl):
        if isinstance(cpl, CplInt) or isinstance(cpl, CplFloat):
            return self._set_mod(ctx, cpl.cache(ctx, force="score", force_t=self.unique_type.type))
        if isinstance(cpl, CplScore):
            t_want = self.unique_type.type
            t_have = cpl.unique_type.type
            if t_want != t_have:
                cpl = cpl.cache(ctx, force_t=t_want)
            ctx.file.append(f"scoreboard players operation {self.location} %= {cpl.location}")
            return self
        if not isinstance(cpl, CplIntNBT) and not isinstance(cpl, CplFloatNBT):
            return None
        return self._set_mod(ctx, cpl.cache(ctx, force="score", force_t=self.unique_type.type))

    def _add(self, ctx, cpl):
        return self.cache(ctx)._set_add(ctx, cpl)

    def _sub(self, ctx, cpl):
        return self.cache(ctx)._set_sub(ctx, cpl)

    def _mul(self, ctx, cpl):
        return self.cache(ctx)._set_mul(ctx, cpl)

    def _div(self, ctx, cpl):
        return self.cache(ctx)._set_div(ctx, cpl)

    def _mod(self, ctx, cpl):
        return self.cache(ctx)._set_mod(ctx, cpl)

    def _eq_neq(self, ctx, cpl, is_eq):
        return self._cmp(ctx, cpl, "==" if is_eq else "!=")

    def _cmp(self, ctx, cpl, op):
        if isinstance(cpl, CplInt) or isinstance(cpl, CplFloat):
            if op == "==" or op == "!=":
                return cpl._eq_neq(ctx, self, op == "==")
            return cpl._cmp(ctx, self, inv_cmp(op))

        if isinstance(cpl, CplIntNBT) or isinstance(cpl, CplFloatNBT):
            cpl = cpl.cache(ctx, force="score", force_t=self.unique_type.type)

        if isinstance(cpl, CplScore):
            op_if = "unless" if op == "!=" else "if"
            eid = f"int_{get_expr_id()} --temp--"
            t_want = self.unique_type.type
            t_have = cpl.unique_type.type
            if t_want != t_have:
                cpl = cpl.cache(ctx, force_t=t_want)
            if op == "==" or op == "!=":
                op = "="
            ctx.file.append(f"scoreboard players set {eid} 0")
            ctx.file.append(f"execute {op_if} score {self.location} {op} {cpl.location} "
                            f"run scoreboard players set {eid} 1")
            return CplScore(self.token, eid)
        return None

    def _and(self, ctx, cpl):
        eid = f"int_{get_expr_id()} --temp--"
        ctx.file.append(f"scoreboard players set {eid} 0")
        ctx.file.append(f"execute "
                        f"unless score {self.location} matches 0..0 "
                        f"unless score {cpl.location} matches 0..0 "
                        f"run scoreboard players set {eid} 1")
        return CplScore(self.token, eid)

    def _or(self, ctx, cpl):
        eid = f"int_{get_expr_id()} --temp--"
        ctx.file.append(f"scoreboard players set {eid} 0")
        ctx.file.append(f"execute "
                        f"unless score {self.location} matches 0..0 "
                        f"run scoreboard players set {eid} 1")
        ctx.file.append(f"execute "
                        f"unless score {cpl.location} matches 0..0 "
                        f"run scoreboard players set {eid} 1")
        return CplScore(self.token, eid)

    def tellraw_object(self, ctx):
        if self.unique_type.type == "int":
            ls = self.location.split(" ")
            return ('{"score":{"name":"'
                    + ls[0]
                    + '","objective":"'
                    + ls[1]
                    + '"}}')
        eid = get_expr_id()
        ctx.file.append(
            f"execute store result storage temp _{eid} float {1 / FLOAT_PREC:.7f} run scoreboard players get {self.location}")
        return '{"storage":"temp","nbt":"_' + str(eid) + '"}'


from .float import CplFloat
from .int import CplInt
from .nbt import val_nbt
from .nbtfloat import CplFloatNBT
from .nbtint import CplIntNBT
