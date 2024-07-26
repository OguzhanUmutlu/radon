from .float import CplFloat
from .int import CplInt
from .nbtfloat import CplFloatNBT
from .nbtint import CplIntNBT
from .score import CplScore
from ..utils import get_expr_id, basic_cmp, FLOAT_PREC, inv_cmp


def num_add(self, ctx, cpl):
    if isinstance(cpl, CplInt) or isinstance(cpl, CplFloat):
        if isinstance(self, CplInt) and isinstance(cpl, CplInt):
            return CplInt(self.token, self.value + cpl.value)
        return CplFloat(self.token, self.value + cpl.value)
    return self.cache(ctx)._add(ctx, cpl)


def num_sub(self, ctx, cpl):
    if isinstance(cpl, CplInt) or isinstance(cpl, CplFloat):
        if isinstance(self, CplInt) and isinstance(cpl, CplInt):
            return CplInt(self.token, self.value - cpl.value)
        return CplFloat(self.token, self.value - cpl.value)
    return self.cache(ctx)._sub(ctx, cpl)


def num_mul(self, ctx, cpl):
    if isinstance(cpl, CplInt) or isinstance(cpl, CplFloat):
        if isinstance(self, CplInt) and isinstance(cpl, CplInt):
            return CplInt(self.token, self.value * cpl.value)
        return CplFloat(self.token, self.value * cpl.value)
    return self.cache(ctx)._mul(ctx, cpl)


def num_div(self, ctx, cpl):
    if isinstance(cpl, CplInt) or isinstance(cpl, CplFloat):
        if isinstance(self, CplInt) and isinstance(cpl, CplInt):
            return CplInt(self.token, self.value / cpl.value)
        return CplFloat(self.token, self.value / cpl.value)
    return self.cache(ctx)._div(ctx, cpl)


def num_mod(self, ctx, cpl):
    if isinstance(cpl, CplInt) or isinstance(cpl, CplFloat):
        if isinstance(self, CplInt) and isinstance(cpl, CplInt):
            return CplInt(self.token, self.value % cpl.value)
        return CplFloat(self.token, self.value % cpl.value)
    return self.cache(ctx)._mod(ctx, cpl)


def num_eq_neq(self, ctx, cpl, is_eq):
    if isinstance(cpl, CplInt) or isinstance(cpl, CplFloat):
        v = float(cpl.value) == float(self.value)
        if not is_eq:
            v = not v
        return CplInt(self.token, v)

    if isinstance(cpl, CplIntNBT) or isinstance(cpl, CplFloatNBT):
        cpl = cpl.cache(ctx, force="score", force_t=self.unique_type.type)

    if isinstance(cpl, CplScore):
        v = self.value
        self_t = self.unique_type.type
        score_t = cpl.unique_type.type
        if score_t == "int" and self_t == "float":
            v = int(v)
        if score_t == "float":
            v = int(v * FLOAT_PREC)
        eid = f"int_{get_expr_id()} --temp--"
        ctx.file.append(f"scoreboard players set {eid} 0")
        ctx.file.append(f"execute if score {cpl.location} matches {v}..{v} "
                        f"run scoreboard players set {eid} 1")
        return CplScore(self.token, eid)
    return None


def num_cmp(self, ctx, cpl, op):
    if isinstance(cpl, CplInt) or isinstance(cpl, CplFloat):
        return CplInt(self.token, basic_cmp(float(self.value), op, float(cpl.value)))
    if isinstance(cpl, CplIntNBT) or isinstance(cpl, CplFloatNBT):
        cpl = cpl.cache(ctx, force="score")
    if not isinstance(cpl, CplScore):
        return None
    self_t = self.unique_type.type
    score_t = cpl.unique_type.type
    inv_op = inv_cmp(op)
    # score INV_OP self
    v = self.value
    if score_t == "int" and self_t == "float":
        v = int(v)
    if score_t == "float":
        v = int(v * FLOAT_PREC)
    eid = f"int_{get_expr_id()} --temp--"
    ctx.file.append(f"scoreboard players set {eid} 0")
    matcher = ""
    if inv_op == ">":
        matcher = f"{v + 1}.."
    elif inv_op == "<":
        matcher = f"..{v - 1}"
    elif inv_op == ">=":
        matcher = f"{v}.."
    elif inv_op == "<=":
        matcher = f"..{v}"
    ctx.file.append(f"execute if score {cpl.location} matches {matcher} run scoreboard players set {eid} 1")
    return CplScore(self.token, eid)


def num_and(self, _, cpl):
    if self.value == 0:
        return CplInt(self.token, 0)
    return cpl


def num_or(self, _, cpl):
    if self.value == 0:
        return cpl
    return CplInt(self.token, 1)


def nbt_set_add(self, ctx, cpl):
    nbt_add(self, ctx, cpl).cache(ctx, nbt_loc=self.location, force="nbt")
    return self


def nbt_set_sub(self, ctx, cpl):
    nbt_sub(self, ctx, cpl).cache(ctx, nbt_loc=self.location, force="nbt")
    return self


def nbt_set_mul(self, ctx, cpl):
    nbt_mul(self, ctx, cpl).cache(ctx, nbt_loc=self.location, force="nbt")
    return self


def nbt_set_div(self, ctx, cpl):
    nbt_div(self, ctx, cpl).cache(ctx, nbt_loc=self.location, force="nbt")
    return self


def nbt_set_mod(self, ctx, cpl):
    nbt_mod(self, ctx, cpl).cache(ctx, nbt_loc=self.location, force="nbt")
    return self


def nbt_add(self, ctx, cpl):
    if self.unique_type != cpl.unique_type:
        return None
    return self.cache(ctx, force="score")._add(ctx, cpl)


def nbt_sub(self, ctx, cpl):
    if self.unique_type != cpl.unique_type:
        return None
    return self.cache(ctx, force="score")._sub(ctx, cpl)


def nbt_mul(self, ctx, cpl):
    if self.unique_type != cpl.unique_type:
        return None
    return self.cache(ctx, force="score")._mul(ctx, cpl)


def nbt_div(self, ctx, cpl):
    if self.unique_type != cpl.unique_type:
        return None
    return self.cache(ctx, force="score")._div(ctx, cpl)


def nbt_mod(self, ctx, cpl):
    if self.unique_type != cpl.unique_type:
        return None
    return self.cache(ctx, force="score")._mod(ctx, cpl)


def nbt_eq_neq(self, ctx, cpl, is_eq):
    return self.cache(ctx, force="score")._eq_neq(ctx, cpl, is_eq)


def nbt_cmp(self, ctx, cpl, op):
    if self.unique_type != cpl.unique_type:
        return None
    return self.cache(ctx, force="score")._cmp(ctx, cpl, op)


def nbt_and(self, ctx, cpl):
    if self.unique_type != cpl.unique_type:
        return None
    return self.cache(ctx, force="score")._and(ctx, cpl)


def nbt_or(self, ctx, cpl):
    if self.unique_type != cpl.unique_type:
        return None
    return self.cache(ctx, force="score")._or(ctx, cpl)


def make_num(cpl):
    cpl._add = num_add
    cpl._sub = num_sub
    cpl._mul = num_mul
    cpl._div = num_div
    cpl._mod = num_mod
    cpl._eq_neq = num_eq_neq
    cpl._cmp = num_cmp
    cpl._and = num_and
    cpl._or = num_or


def make_nbt_num(cpl):
    cpl._set_add = nbt_set_add
    cpl._set_sub = nbt_set_sub
    cpl._set_mul = nbt_set_mul
    cpl._set_div = nbt_set_div
    cpl._set_mod = nbt_set_mod
    cpl._add = nbt_add
    cpl._sub = nbt_sub
    cpl._mul = nbt_mul
    cpl._div = nbt_div
    cpl._mod = nbt_mod
    cpl._eq_neq = nbt_eq_neq
    cpl._cmp = nbt_cmp
    cpl._and = nbt_and
    cpl._or = nbt_or
