from typing import Union, Any, List

from ..error import raise_syntax_error, raise_syntax_error_t
from ..tokenizer import Token
from ..utils import CplDef, get_expr_id


class CompileTimeValue:
    def __init__(self, token):
        # type: (Token | None) -> None
        self.unique_type: CplDef = CplDef("unknown")
        self.token = token

    def get_py_value(self) -> Any:
        return None

    def get_data_str(self, ctx):
        # type: (TranspilerContext) -> str
        raise ValueError("")

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(token={self.token}, type={self.unique_type})"

    def _cache(self, ctx, score_loc=None, nbt_loc=None, force=None, force_t=None):
        # type: (TranspilerContext, str | None, str | None, str | None, str | None) -> Union[CplScore, CplNBT]
        pass

    def _compute_check(self, res, op, cpl):
        if res is None:
            t1 = self.token
            t2 = cpl.token
            if t1.start > t2.start:
                t1 = t2
                t2 = self.token
            raise_syntax_error_t(
                f"Cannot compute {self.__class__.__name__}({self.unique_type}) {op} {cpl.__class__.__name__}({cpl.unique_type})",
                t1.code, t1.start, t2.end)
            assert False

    def compute(self, ctx, op, cpl):
        # type: (TranspilerContext, str, CompileTimeValue) -> CompileTimeValue
        if op == "+":
            res = self._add(ctx, cpl)
            print(res)
        elif op == "-":
            res = self._sub(ctx, cpl)
        elif op == "*":
            res = self._mul(ctx, cpl)
        elif op == "/":
            res = self._div(ctx, cpl)
        elif op == "%":
            res = self._mod(ctx, cpl)
        elif op == "+=":
            res = self._set_add(ctx, cpl)
        elif op == "-=":
            res = self._set_sub(ctx, cpl)
        elif op == "*=":
            res = self._set_mul(ctx, cpl)
        elif op == "/=":
            res = self._set_div(ctx, cpl)
        elif op == "%=":
            res = self._set_mod(ctx, cpl)
        elif op == "=":
            res = self._set(ctx, cpl)
        elif op == "==" or op == "is":
            res = self._eq(ctx, cpl)
        elif op == "!=" or op == "is not":
            res = self._neq(ctx, cpl)
        elif op == ">":
            res = self._gt(ctx, cpl)
        elif op == "<":
            res = self._lt(ctx, cpl)
        elif op == ">=":
            res = self._gte(ctx, cpl)
        elif op == "<=":
            res = self._lte(ctx, cpl)
        elif op == "&&" or op == "and":
            res = self._and(ctx, cpl)
        elif op == "||" or op == "or":
            res = self._or(ctx, cpl)
        else:
            assert False
        self._compute_check(res, op, cpl)
        return res

    def cache(self, ctx, score_loc=None, nbt_loc=None, force=None, force_t=None):
        # type: (TranspilerContext, str | None, str | None, str | None, str | None) -> Union[CplScore, CplNBT]
        nbt_got_id = None
        if not nbt_loc and force != "score":
            nbt_got_id = get_expr_id()
            nbt_loc = f"storage temp _{nbt_got_id}"
        if not score_loc and force != "nbt":
            t = self.unique_type if force_t is None else force_t
            score_loc = f"{t}_{nbt_got_id or get_expr_id()} --temp--"
        return self._cache(ctx, score_loc, nbt_loc, force, force_t)

    def compute_cache(self, ctx, op, cpl, score_loc=None, nbt_loc=None, force=None, is_reversed=False):
        # type: (TranspilerContext, str, CompileTimeValue, str | None, str | None, str | None, bool) -> CompileTimeValue
        if self.get_py_value() is not None:
            return self.compute(ctx, op, cpl, is_reversed)
        return self.cache(ctx, score_loc, nbt_loc, force).compute(ctx, op, cpl, is_reversed)

    def _get_index(self, ctx, index):
        # type: (TranspilerContext, CompileTimeValue) -> CompileTimeValue | None
        return None

    def _get_slice(self, ctx, index1, index2, index3):
        # type: (TranspilerContext, CompileTimeValue, CompileTimeValue, CompileTimeValue) -> CompileTimeValue | None
        return None

    def _call_index(self, ctx, index, arguments):
        # type: (TranspilerContext, str, List[CompileTimeValue]) -> CompileTimeValue | int | None
        return None

    def get_index(self, ctx, index):
        # type: (TranspilerContext, CompileTimeValue) -> CompileTimeValue
        r = self._get_index(ctx, index)
        if r is None:
            ind = index
            if isinstance(ind, CompileTimeValue):
                ind = ind.unique_type
            raise_syntax_error(f"Cannot index into {self.unique_type} with {ind}", self.token)
        return r

    def get_slice(self, ctx, index1, index2, index3):
        # type: (TranspilerContext, CompileTimeValue, CompileTimeValue, CompileTimeValue) -> CompileTimeValue
        r = self._get_slice(ctx, index1, index2, index3)
        if r is None:
            ind = ":".join(map(lambda x: x.unique_type, [index1, index2, index3]))
            raise_syntax_error(f"Cannot index into {self.unique_type} with [{ind}]", self.token)
        return r

    def call_index(self, ctx, index, arguments):
        # type: (TranspilerContext, str, List[CompileTimeValue]) -> CompileTimeValue
        r = self._call_index(ctx, index, arguments)
        if r is None:
            raise_syntax_error(f"Cannot call into {self.unique_type} with {index}", self.token)
        if isinstance(r, int):
            raise_syntax_error(f"Expected {r} arguments for {self.unique_type}.{index}()", self.token)
        return r

    def _set(self, ctx, cpl):
        return None

    def _set_add(self, ctx, cpl):
        return None

    def _set_sub(self, ctx, cpl):
        return None

    def _set_mul(self, ctx, cpl):
        return None

    def _set_div(self, ctx, cpl):
        return None

    def _set_mod(self, ctx, cpl):
        return None

    def _add(self, ctx, cpl):
        return None

    def _sub(self, ctx, cpl):
        return None

    def _mul(self, ctx, cpl):
        return None

    def _div(self, ctx, cpl):
        return None

    def _mod(self, ctx, cpl):
        return None

    def _eq_neq(self, ctx, cpl, is_eq):
        return None

    def _eq(self, ctx, cpl):
        return self._eq_neq(ctx, cpl, True)

    def _neq(self, ctx, cpl):
        return self._eq_neq(ctx, cpl, False)

    def _cmp(self, ctx, cpl, op):
        return None

    def _gt(self, ctx, cpl):
        return self._cmp(ctx, cpl, ">")

    def _lt(self, ctx, cpl):
        return self._cmp(ctx, cpl, "<")

    def _gte(self, ctx, cpl):
        return self._cmp(ctx, cpl, ">=")

    def _lte(self, ctx, cpl):
        return self._cmp(ctx, cpl, "<=")

    def _and(self, ctx, cpl):
        return None

    def _or(self, ctx, cpl):
        return None

    def tellraw_object(self, ctx):
        raise_syntax_error(
            f"Cannot read {self.unique_type} value with a $str() macro",
            self.token
        )


from .nbt import CplNBT
from .score import CplScore
from ..transpiler import TranspilerContext
