import json
import math
from types import FunctionType
from typing import Union, Any, List, Dict

from .error import raise_syntax_error, raise_syntax_error_t
from .nbt_definitions import ENTITIES_OBJ
from .tokenizer import Token, GroupToken
from .utils import CplDef, get_uuid, FLOAT_PREC, basic_cmp, inv_cmp, CplDefArray, TokenType, FLOAT_TYPE, INT_TYPE, \
    CplDefObject, STRING_TYPE, SELECTOR_TYPE, CplDefTuple


def tellraw_dumps(obj):
    if isinstance(obj, FunctionType):
        return obj()
    if isinstance(obj, str) or isinstance(obj, bool):
        return json.dumps(obj)
    if isinstance(obj, list):
        return '[' + ",".join(map(tellraw_dumps, obj)) + ']'
    if isinstance(obj, dict):
        return '{' + ",".join(map(lambda x: f'"{x[0]}":{tellraw_dumps(x[1])}', obj.items())) + '}'
    raise ValueError("Unexpected tellraw value: " + str(obj))


def _call_obj(obj):
    for k in obj:
        if isinstance(obj[k], FunctionType):
            obj[k] = obj[k]()
        if isinstance(obj[k], Dict):
            _call_obj(obj[k])
    return obj


class Cpl:
    def __init__(self, token):
        # type: (Token | None) -> None
        self.type = self.__class__.__name__
        self.unique_type: CplDef = CplDef("unknown")
        self.token = token

    def get_py_value(self) -> Any:
        return None

    def get_data_str(self, ctx):
        # type: (TranspilerContext) -> str
        raise ValueError("")

    def __str__(self) -> str:
        return f"{self.type}(token={self.token}, type={self.unique_type})"

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
                f"Cannot compute {self.type}({self.unique_type}) {op} {cpl.c}({cpl.unique_type})",
                t1.code, t1.start, t2.end)
            assert False

    def compute(self, ctx, op, cpl, token):
        # type: (TranspilerContext, str, Cpl, Token) -> Cpl
        st = self.token
        if not st:
            self.token = token
        if op == "+":
            res = self._add(ctx, cpl)
        elif op == "-":
            res = self._sub(ctx, cpl)
        elif op == "*":
            res = self._mul(ctx, cpl)
        elif op == "/":
            res = self._div(ctx, cpl)
        elif op == "%":
            res = self._mod(ctx, cpl)
        elif op == "**":
            res = self._pow(ctx, cpl)
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
        elif op == "**=":
            res = self._set_pow(ctx, cpl)
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
            nbt_got_id = get_uuid()
            nbt_loc = f"storage temp _{nbt_got_id}"
        if not score_loc and force != "nbt":
            t = force_t or self.unique_type.type
            score_loc = f"{t}_{nbt_got_id or get_uuid()} __temp__"
        return self._cache(ctx, score_loc, nbt_loc, force, force_t)

    def _get_index(self, ctx, index):
        # type: (TranspilerContext, Cpl) -> Cpl | None
        return None

    def _get_slice(self, ctx, index1, index2, index3, token):
        # type: (TranspilerContext, Cpl, Cpl, Cpl, Token) -> Cpl | None
        return None

    def _call_index(self, ctx, index, arguments, token):
        # type: (TranspilerContext, str, List[Cpl], Token) -> Cpl | int | None
        return None

    def _raw_call_index(self, ctx: "TranspilerContext", index: str, arguments: "List[GroupToken]",
                        token: Token) -> "Cpl | int | None":
        return None

    def _call(self, ctx: "TranspilerContext", arguments: "List[Cpl]", token: Token) -> "Cpl | None":
        return None

    def _raw_call(self, ctx: "TranspilerContext", arguments: "List[GroupToken]", token: "Token") -> "Cpl | None":
        return None

    def get_index(self, ctx, index, token=None):
        # type: (TranspilerContext, Cpl, Token | None) -> Cpl
        st = self.token
        if not st:
            self.token = token
        r = self._get_index(ctx, index)
        self.token = st
        if r is None:
            ind = index
            if isinstance(ind, Cpl):
                ind = ind.unique_type
            raise_syntax_error(f"Cannot index into {self.unique_type} with {ind}", self.token)
        return r

    def get_slice(self, ctx: "TranspilerContext", index1: "Cpl", index2: "Cpl", index3: "Cpl",
                  token: "Token | None" = None):
        st = self.token
        if not st:
            self.token = token
        r = self._get_slice(ctx, index1, index2, index3, token)
        self.token = st
        if r is None:
            ind = ":".join(map(lambda x: str(x.unique_type), [index1, index2, index3]))
            raise_syntax_error(f"Cannot index into {self.unique_type} with [{ind}]", self.token)
        return r

    def call_index(self, ctx: "TranspilerContext", index: str, arguments: "List[Cpl] | GroupToken",
                   token: "Token | None" = None):
        if isinstance(arguments, GroupToken):
            raw_res = self._raw_call_index(ctx, index, raw_group_args(arguments), arguments)
            if raw_res is not None:
                return raw_res
            arguments = ctx.transpiler.arg_tokens_to_cpl(ctx, arguments.children)

        st = self.token
        if not st:
            self.token = token
        r = self._call_index(ctx, index, arguments, token)
        self.token = st
        if r is None:
            raise_syntax_error(f"Cannot call into {self.unique_type} with {index}", token or self.token)
        if isinstance(r, int):
            raise_syntax_error(f"Expected {r} arguments for {self.unique_type}.{index}()", token or self.token)
        return r

    def call(self, ctx: "TranspilerContext", arguments: "List[Cpl] | GroupToken",
             token: "Token | None" = None) -> "Cpl":
        if isinstance(arguments, GroupToken):
            raw_res = self._raw_call(ctx, raw_group_args(arguments), arguments)
            if raw_res is not None:
                return raw_res
            arguments = ctx.transpiler.arg_tokens_to_cpl(ctx, arguments.children)

        st = self.token
        if not st:
            self.token = token
        r = self._call(ctx, arguments, token)
        self.token = st
        if r is None:
            raise_syntax_error(f"Cannot call into {self.unique_type}", token or self.token)
        if isinstance(r, int):
            raise_syntax_error(f"Expected {r} arguments for {self.unique_type}()", token or self.token)
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

    def _set_pow(self, ctx, cpl):
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

    def tellraw_object(self, ctx) -> Dict:
        raise_syntax_error(
            f"Cannot read {self.unique_type} value with a $str() macro",
            self.token
        )
        return {}

    def tellraw_object_str(self, ctx):
        return tellraw_dumps(self.tellraw_object(ctx))

    def __iadd__(self, other):
        self._set_add(other[0], other[1])
        return self

    def __isub__(self, other):
        self._set_sub(other[0], other[1])
        return self

    def __imul__(self, other):
        self._set_mul(other[0], other[1])
        return self

    def __idiv__(self, other):
        self._set_div(other[0], other[1])
        return self

    def __imod__(self, other):
        self._set_mod(other[0], other[1])
        return self

    def __add__(self, other):
        return self._add(other[0], other[1])

    def __sub__(self, other):
        return self._sub(other[0], other[1])

    def __mul__(self, other):
        return self._mul(other[0], other[1])

    def __div__(self, other):
        return self._div(other[0], other[1])

    def __mod__(self, other):
        return self._mod(other[0], other[1])

    def __eq__(self, other):
        if not isinstance(other, list) or len(other) != 2 or not isinstance(other[1], Cpl):
            return self is other
        return self._eq(other[0], other[1])

    def __ne__(self, other):
        if not isinstance(other, list) or len(other) != 2 or not isinstance(other[1], Cpl):
            return self is not other
        return self._neq(other[0], other[1])

    def __gt__(self, other):
        if not isinstance(other, list) or len(other) != 2 or not isinstance(other[1], Cpl):
            return False
        return self._gt(other[0], other[1])

    def __lt__(self, other):
        if not isinstance(other, list) or len(other) != 2 or not isinstance(other[1], Cpl):
            return False
        return self._lt(other[0], other[1])

    def __ge__(self, other):
        if not isinstance(other, list) or len(other) != 2 or not isinstance(other[1], Cpl):
            return False
        return self._gte(other[0], other[1])

    def __le__(self, other):
        if not isinstance(other, list) or len(other) != 2 or not isinstance(other[1], Cpl):
            return False
        return self._lte(other[0], other[1])

    def __and__(self, other):
        if not isinstance(other, list) or len(other) != 2 or not isinstance(other[1], Cpl):
            return False
        return self._and(other[0], other[1])

    def __call__(self, *args, **kwargs):
        return self.call(args[0], list(args[1:]))

    def is_lit_eq(self, v):
        return (isinstance(self, CplInt) or isinstance(self, CplFloat)) and self.value == v


class CplLiteral(Cpl):
    def __init__(self, token: Union[Token, None], value: Any):
        super().__init__(token)
        self.value = value


def num_add(self, ctx, cpl):
    if isinstance(cpl, CplInt) or isinstance(cpl, CplFloat):
        if isinstance(self, CplInt) and isinstance(cpl, CplInt):
            return CplInt(self.token, self.value + cpl.value)
        return CplFloat(self.token, self.value + cpl.value)
    if self.value == 0:
        return cpl
    return self.cache(ctx)._set_add(ctx, cpl)


def num_sub(self, ctx, cpl):
    if isinstance(cpl, CplInt) or isinstance(cpl, CplFloat):
        if isinstance(self, CplInt) and isinstance(cpl, CplInt):
            return CplInt(self.token, self.value - cpl.value)
        return CplFloat(self.token, self.value - cpl.value)
    return self.cache(ctx)._set_sub(ctx, cpl)


def num_mul(self, ctx, cpl):
    if isinstance(cpl, CplInt) or isinstance(cpl, CplFloat):
        if isinstance(self, CplInt) and isinstance(cpl, CplInt):
            return CplInt(self.token, self.value * cpl.value)
        return CplFloat(self.token, self.value * cpl.value)
    if self.value == 0:
        return self
    if self.value == 1:
        return cpl
    return self.cache(ctx)._set_mul(ctx, cpl)


def num_div(self, ctx, cpl):
    if isinstance(cpl, CplInt) or isinstance(cpl, CplFloat):
        if isinstance(self, CplInt) and isinstance(cpl, CplInt):
            return CplInt(self.token, self.value / cpl.value)
        return CplFloat(self.token, self.value / cpl.value)
    if self.value == 0:
        raise_syntax_error("Division by zero", self.token)
    return self.cache(ctx)._set_div(ctx, cpl)


def num_mod(self, ctx, cpl):
    if isinstance(cpl, CplInt) or isinstance(cpl, CplFloat):
        if isinstance(self, CplInt) and isinstance(cpl, CplInt):
            return CplInt(self.token, self.value % cpl.value)
        return CplFloat(self.token, self.value % cpl.value)
    if self.value == 0:
        raise_syntax_error("Modulo by zero", self.token)
    return self.cache(ctx)._set_mod(ctx, cpl)


def num_pow(self, ctx, cpl):
    if isinstance(cpl, CplInt) or isinstance(cpl, CplFloat):
        if isinstance(self, CplInt):
            return CplInt(self.token, self.value ** cpl.value)
        return CplFloat(self.token, self.value ** cpl.value)
    return self.cache(ctx)._set_pow(ctx, cpl)


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
        eid = f"int_{get_uuid()} __temp__"
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
    eid = f"int_{get_uuid()} __temp__"
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
    if cpl.is_lit_eq(0):
        return self
    nbt_add(self, ctx, cpl).cache(ctx, nbt_loc=self.location, force="nbt")
    return self


def nbt_set_sub(self, ctx, cpl):
    if cpl.is_lit_eq(0):
        return self
    nbt_sub(self, ctx, cpl).cache(ctx, nbt_loc=self.location, force="nbt")
    return self


def nbt_set_mul(self, ctx, cpl):
    if cpl.is_lit_eq(1):
        return self
    nbt_mul(self, ctx, cpl).cache(ctx, nbt_loc=self.location, force="nbt")
    return self


def nbt_set_div(self, ctx, cpl):
    if cpl.is_lit_eq(0):
        raise_syntax_error("Division by zero", self.token)
    if cpl.is_lit_eq(1):
        return self
    nbt_div(self, ctx, cpl).cache(ctx, nbt_loc=self.location, force="nbt")
    return self


def nbt_set_mod(self, ctx, cpl):
    if cpl.is_lit_eq(0):
        raise_syntax_error("Modulo by zero", self.token)
    if cpl.is_lit_eq(1) and self.unique_type.type == "int":
        return self
    nbt_mod(self, ctx, cpl).cache(ctx, nbt_loc=self.location, force="nbt")
    return self


def nbt_set_pow(self, ctx, cpl):
    if cpl.is_lit_eq(0):
        return CplInt(self.token, 1)
    nbt_pow(self, ctx, cpl).cache(ctx, nbt_loc=self.location, force="nbt")
    return self


def nbt_add(self, ctx, cpl):
    if cpl.is_lit_eq(0):
        return self
    return self.cache(ctx, force="score")._set_add(ctx, cpl)


def nbt_sub(self, ctx, cpl):
    if cpl.is_lit_eq(0):
        return self
    return self.cache(ctx, force="score")._set_sub(ctx, cpl)


def nbt_mul(self, ctx, cpl):
    if cpl.is_lit_eq(1):
        return self
    if cpl.is_lit_eq(0):
        return cpl
    return self.cache(ctx, force="score")._set_mul(ctx, cpl)


def nbt_div(self, ctx, cpl):
    if cpl.is_lit_eq(0):
        raise_syntax_error("Division by zero", self.token)
    if cpl.is_lit_eq(1):
        return self
    return self.cache(ctx, force="score")._set_div(ctx, cpl)


def nbt_mod(self, ctx, cpl):
    if cpl.is_lit_eq(0):
        raise_syntax_error("Modulo by zero", self.token)
    if cpl.is_lit_eq(1) and self.unique_type.type == "int":
        return self
    return self.cache(ctx, force="score")._set_mod(ctx, cpl)


def nbt_pow(self, ctx, cpl):
    if cpl.is_lit_eq(0):
        return CplInt(self.token, 1)
    if cpl.is_lit_eq(1):
        return self
    return self.cache(ctx, force="score")._set_pow(ctx, cpl)


def nbt_eq_neq(self, ctx, cpl, is_eq):
    return self.cache(ctx, force="score")._eq_neq(ctx, cpl, is_eq)


def nbt_cmp(self, ctx, cpl, op):
    return self.cache(ctx, force="score")._cmp(ctx, cpl, op)


def nbt_and(self, ctx, cpl):
    return self.cache(ctx, force="score")._and(ctx, cpl)


def nbt_or(self, ctx, cpl):
    return self.cache(ctx, force="score")._or(ctx, cpl)


def make_num(cpl):
    cpl._add = num_add
    cpl._sub = num_sub
    cpl._mul = num_mul
    cpl._div = num_div
    cpl._mod = num_mod
    cpl._pow = num_pow
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
    cpl._set_pow = nbt_set_pow
    cpl._add = nbt_add
    cpl._sub = nbt_sub
    cpl._mul = nbt_mul
    cpl._div = nbt_div
    cpl._mod = nbt_mod
    cpl._pow = nbt_pow
    cpl._eq_neq = nbt_eq_neq
    cpl._cmp = nbt_cmp
    cpl._and = nbt_and
    cpl._or = nbt_or


class CplArray(Cpl):
    def __init__(self, token, value):
        # type: (Token | None, List[Cpl]) -> None
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

    def _get_index(self, ctx, index: Cpl):
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
        return {"text": json.dumps(py_v)}


class CplFloat(CplLiteral):
    def __init__(self, token: Union[Token, None], value: float):
        value = float(value)
        if token is None:
            token = Token(str(value), TokenType.FLOAT_LITERAL, 0, len(str(value)))
        super().__init__(token, value)
        self.unique_type = FLOAT_TYPE

    def get_py_value(self):
        return self.value

    def as_int(self):
        return CplInt(self.token, self.value)

    def as_string(self):
        return CplString(self.token, self.value)

    def _cache(self, ctx, score_loc=None, nbt_loc=None, force=None, force_t=None):
        t = force_t or "float"
        v = self.value
        if force_t == "int":
            v = int(self.value)
        if force == "nbt":
            ctx.file.append(f"data modify {nbt_loc} set value {v}")
            return CplFloatNBT(self.token, nbt_loc)
        if t == "float":
            v = int(v * FLOAT_PREC)
        ctx.file.append(f"scoreboard players set {score_loc} {v}")
        return CplScore(self.token, score_loc)

    def get_data_str(self, ctx):
        return f"value {self.value}"

    def _call_index(self, ctx, index: str, arguments: List[Cpl], token):
        if index == "toString":
            if len(arguments) > 0:
                return 0
            return self.as_string()
        if index == "sqrt":
            return CplFloat(self.token, math.sqrt(self.value))
        if index == "cbrt":
            return CplFloat(self.token, self.value ** (1 / 3))
        if index == "int":
            if len(arguments) > 0:
                raise_syntax_error("Expected 0 arguments for <float>.int()", self.token)
                assert False
            return self.as_int()
        if index == "float":
            if len(arguments) > 0:
                raise_syntax_error("Expected 0 arguments for <float>.float()", self.token)
                assert False
            return self

    def tellraw_object(self, ctx):
        return {"text": str(self.value)}


class CplInt(CplLiteral):
    def __init__(self, token, value):
        # type: (Token | None, int) -> None
        value = int(value)
        if token is None:
            token = Token(str(value), TokenType.INT_LITERAL, 0, len(str(value)))
        super().__init__(token, value)
        self.unique_type = INT_TYPE

    def get_py_value(self):
        return self.value

    def as_float(self):
        return CplFloat(self.token, self.value)

    def as_string(self):
        return CplString(self.token, self.value)

    def _cache(self, ctx, score_loc=None, nbt_loc=None, force=None, force_t=None):
        v = self.value
        if force_t == "float":
            v *= FLOAT_PREC
        if force == "nbt":
            ctx.file.append(f"data modify {nbt_loc} set value {v}")
            return CplIntNBT(self.token, nbt_loc)
        ctx.file.append(f"scoreboard players set {score_loc} {v}")
        return CplScore(self.token, score_loc)

    def get_data_str(self, ctx):
        return f"value {self.value}"

    def _call_index(self, ctx, index: str, arguments: List[Cpl], token):
        if index == "toString":
            if len(arguments) > 0:
                return 0
            return self.as_string()
        if index == "sqrt":
            return CplInt(self.token, math.isqrt(self.value))
        if index == "int":
            if len(arguments) > 0:
                raise_syntax_error("Expected 0 arguments for <int>.int()", self.token)
                assert False
            return self
        if index == "float":
            if len(arguments) > 0:
                raise_syntax_error("Expected 0 arguments for <int>.float()", self.token)
                assert False
            return self.as_float()
        return None

    def tellraw_object(self, ctx):
        return {"text": str(self.value)}


class CplNBT(Cpl):
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

    def _eq_neq(self, ctx, cpl, is_eq):
        if self.unique_type != cpl.unique_type:
            return CplInt(self.token, 0)
        val = cpl._cache(ctx, force="nbt")
        score = CplScore(self.token, f"int_{get_uuid()} __temp__")
        ctx.file.append(
            f"execute store success score {score.location} run data modify {val.location} set from {self.location}")
        if not is_eq:
            score._sub(ctx, CplInt(self.token, 1))
            score._mul(ctx, CplInt(self.token, -1))
        return score

    def tellraw_object(self, ctx):
        ls = self.location.split(" ")
        ls1 = ls[1]
        ls2 = " ".join(ls[2:])
        if ls[0] == "block":
            ls1 = ls[1] + " " + ls[2] + " " + ls[3]
            ls2 = " ".join(ls[4:])
        return {
            ls[0]: ls1,
            "nbt": ls2
        }

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


class CplArrayNBT(CplNBT):
    def __init__(self, token: Union[Token, None], location: str, type: CplDefArray):
        super().__init__(token, location, type)
        self.unique_type = type

    def _set(self, ctx, cpl):
        if isinstance(cpl, CplTuple) and len(cpl.value) == 0:
            ctx.file.append(f"data modify {self.location} set value []")
            return self
        return super()._set(ctx, cpl)

    def _get_index(self, ctx, index: Cpl):
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

    def _call_index(self, ctx, index: str, arguments: List[Cpl], token):
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


class CplFloatNBT(CplNBT):
    def __init__(self, token: Union[Token, None], location: str):
        super().__init__(token, location, FLOAT_TYPE)

    def _cache(self, ctx, score_loc=None, nbt_loc=None, force=None, force_t=None):
        if force == "score":
            t = "float" or force_t
            if t == "int":
                ctx.file.append(f"execute store result score {score_loc} run data get {self.location}")
            else:
                ctx.file.append(f"execute store result score {score_loc} run data get {self.location} {FLOAT_PREC}")
            return CplScore(self.token, score_loc, t)
        return super()._cache(ctx, score_loc, nbt_loc, force, force_t)

    def _get_index(self, ctx, index: Cpl):
        return None

    def _get_slice(self, ctx, index1, index2, index3, token):
        return None

    def _call_index(self, ctx, index: str, arguments: List[Cpl], token):
        return self.cache(ctx, force="score")._call_index(ctx, index, arguments, token)


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

    def _call_index(self, ctx, index: str, arguments: List[Cpl], token):
        return self.cache(ctx, force="score")._call_index(ctx, index, arguments, token)


class CplObjectNBT(CplNBT):
    def __init__(self, token: Union[Token, None], location: str, type: CplDefObject):
        super().__init__(token, location, type)
        self.unique_type = type

    def _get_index(self, ctx, index: Cpl):
        if isinstance(index, CplInt) or isinstance(index, CplFloat) or isinstance(index, CplString):
            ind = str(index.value)
            if ind not in self.unique_type.content:
                raise_syntax_error(f"Key '{ind}' is not in the object: {self.unique_type}", index.token)
            return val_nbt(self.token, self.location + "." + ind, self.unique_type.content[ind])
        values = self.unique_type.content.values()
        if len(set(map(str, values))) > 1:
            raise_syntax_error(
                "Cannot index into an object with a non-literal value if it has multiple value types. "
                "This is because for the compiler it's impossible to know what the type of the unknown key "
                "will correspond to. Use the myObject[myKey : valueType] syntax instead",
                self.token
            )
        content_type = list(values)[0]

        return object_get_index_nbt(ctx, content_type, self, index)

    def _get_slice(self, ctx, index1, index2, index3, token):
        pass

    def _call_index(self, ctx, index: str, arguments: List[Cpl], token):
        if self.unique_type.class_name is None:
            return None
        cls = self.unique_type.class_name
        return ctx.transpiler.run_function_with_cpl(
            ctx=ctx,
            name=cls + "." + index,
            args=arguments,
            base=self.token,
            class_name=cls
        )

    def _add(self, ctx, cpl):
        if self.unique_type.class_name != cpl.unique_type.class_name:
            return None
        if self.unique_type != cpl.unique_type:
            return None
        # TODO: array merging
        return None

    def _and(self, ctx, cpl):
        return cpl

    def _or(self, ctx, cpl):
        return self


class CplStringNBT(CplNBT):
    def __init__(self, token: Union[Token, None], location: str):
        super().__init__(token, location, STRING_TYPE)

    def _get_index(self, ctx, index: Cpl):
        if isinstance(index, CplString) and index.value == "length":
            eid = f"int_{get_uuid()} __temp__"
            ctx.file.append(f"execute store result score {eid} run data get {self.location}")
            return CplScore(self.token, eid)
        if isinstance(index, CplInt):
            temp = f"storage temp _{get_uuid()}"
            ctx.file.append(f"data modify {temp} set string {self.location} {index.value} {index.value + 1}")
            return CplStringNBT(self.token, temp)
        if isinstance(index, CplScore) and index.unique_type.type == "int":
            index = index.cache(ctx, force="nbt")
        if isinstance(index, CplIntNBT):
            index.cache(ctx, nbt_loc="storage temp __get_str_index__ _0", force="nbt")
            index.cache(ctx, force="score")._set_add(ctx, CplInt(self.token, 1)).cache(
                ctx, nbt_loc="storage temp __get_str_index__ _1", force="nbt")
            fn_name = f"__lib__/get_str_index/{get_uuid()}"
            ctx.file.append(f"function {ctx.transpiler.pack_namespace}:{fn_name} with storage temp __get_str_index__")
            ctx.transpiler.files[fn_name] = [
                f"$data modify storage temp __get_str_index__result set string {self.location} $(_0) $(_1)"
            ]
            return CplStringNBT(self.token, "storage temp __get_str_index__result")
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
        if index == "toLowerCase" or index == "toUpperCase":
            if len(arguments) != 0:
                return 0
            ind_name = "lower" if index == "toLowerCase" else "upper"

            length = self._get_index(ctx, CplString(token, "length"))
            i = CplScore(token, f"__to_{ind_name}__i __temp__", "int")
            i._set(ctx, length)

            if f"__lib__/str_to_{ind_name}" not in ctx.transpiler.files:
                fil = []
                ctx.transpiler.files[f"__lib__/str_to_{ind_name}"] = fil

            return self
        if index == "replace" or index == "replaceAll":
            if len(arguments) != 2:
                return 2
            arg0 = arguments[0]
            arg1 = arguments[1]
            if arg0.unique_type.type != "string" or arg1.unique_type.type != "string":
                return None
            if isinstance(arg0, CplString):
                arg0 = arg0.cache(ctx)
            if isinstance(arg1, CplString):
                arg1 = arg1.cache(ctx)
            return None
        if index == "split":
            if len(arguments) != 1:
                return 1
            arg0 = arguments[0]
            if arg0.unique_type.type != "string":
                return None
            if isinstance(arg0, CplString):
                arg0 = arg0.cache(ctx)
            return None
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


class CplObject(Cpl):
    def __init__(self, token=None, value=None, class_name=None):
        # type: (Token | None, Dict[str, Cpl] | None, str | None) -> None
        if value is None:
            value = dict()
        self.unique_type: CplDefObject
        super().__init__(token)
        self.value = value
        t = dict()
        for k, v in self.value.items():
            t[k] = v.unique_type
        self.unique_type = CplDefObject(t, class_name)

    def get_py_value(self):
        d = dict()
        for k, v in self.value.items():
            vl = v.get_py_value()
            if vl is None:
                return None
            d[k] = vl
        return d

    def _cache(self, ctx, score_loc=None, nbt_loc=None, force=None, force_t=None):
        if force == "score":
            return None
        py_val = self.get_py_value()
        if py_val is not None:
            ctx.file.append(f"data modify {nbt_loc} set value {json.dumps(py_val)}")
        else:
            init = []
            keys = []

            for k in self.value:
                v = self.value[k]
                v_py_val = v.get_py_value()
                if v_py_val is not None:
                    init.append(json.dumps(k) + ":" + json.dumps(v_py_val))
                else:
                    init.append(
                        json.dumps(k) + ":" + v.unique_type.get_sample_value()
                    )
                    keys.append(k)
            ctx.file.append(
                f"data modify {nbt_loc} set value {'{'}{','.join(init)}{'}'}"
            )

            for k in self.value:
                v = self.value[k]
                if k in keys:
                    v.cache(ctx, nbt_loc=f"{nbt_loc}.{k}", force="nbt")
        return CplObjectNBT(self.token, nbt_loc, self.unique_type)

    def _get_index(self, ctx, index: Cpl):
        if isinstance(index, CplInt) or isinstance(index, CplFloat) or isinstance(index, CplString):
            return self.value[str(index.value)]
        return self.cache(ctx).get_index(ctx, index)

    def _add(self, ctx, cpl):
        if isinstance(cpl, CplObject):
            if cpl.unique_type.class_name != self.unique_type.class_name:
                return None
            d = dict(self.value)
            d.update(cpl.value)
            return CplObject(self.token, d, self.unique_type.class_name)
        if not isinstance(cpl, CplObjectNBT):
            return None
        return self.cache(ctx)._add(ctx, cpl)

    def tellraw_object(self, ctx):
        py_v = self.get_py_value()
        if py_v is None:
            return self.cache(ctx).tellraw_object(ctx)
        return {"text": json.dumps(py_v)}


class CplScore(Cpl):
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

    def get_data_str(self, ctx):
        return "from " + self.cache(ctx, force="nbt").location

    def as_int(self, ctx, score_loc=None):
        if self.unique_type.type == "int":
            return self
        eid = score_loc or f"int_{get_uuid()} __temp__"
        ctx.file.append(f"scoreboard players operation {eid} = {self.location}")
        ctx.file.append(f"scoreboard players operation {eid} /= FLOAT_PREC __temp__")
        return CplScore(self.token, eid)

    def as_float(self, ctx, score_loc=None):
        if self.unique_type.type == "float":
            return self
        eid = score_loc or f"float_{get_uuid()} __temp__"
        ctx.file.append(f"scoreboard players operation {eid} = {self.location}")
        ctx.file.append(f"scoreboard players operation {eid} *= FLOAT_PREC __temp__")
        return CplScore(self.token, eid)

    def _force_float(self, ctx):  # ONLY USE THIS ON RECENTLY CACHED SCORES!
        if self.unique_type == FLOAT_TYPE:
            return
        self.unique_type = FLOAT_TYPE
        ctx.file.append(f"scoreboard players operation {self.location} *= FLOAT_PREC __temp__")

    def _force_int(self, ctx):  # ONLY USE THIS ON RECENTLY CACHED SCORES!
        if self.unique_type == INT_TYPE:
            return
        self.unique_type = INT_TYPE
        ctx.file.append(f"scoreboard players operation {self.location} /= FLOAT_PREC __temp__")

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
            score_loc = f"{self.unique_type.type}_{get_uuid()} __temp__"
        ctx.file.append(
            f"scoreboard players operation {score_loc} = {self.location}"
        )
        score = CplScore(self.token, score_loc, self.unique_type.type)
        if force_t:
            score._force_type(ctx, force_t)
        return score

    def _call_index(self, ctx, index: str, arguments: List[Cpl], token):
        t = self.unique_type.type
        if index == "sqrt":
            return ctx.transpiler.builtin_vars["Math"].value._call_index(ctx, "isqrt" if t == "int" else "sqrt", [self],
                                                                         token)
        if index == "cbrt":
            return ctx.transpiler.builtin_vars["Math"].value._call_index(ctx, "cbrt", [self], token)
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
                ctx.file.append(f"execute store result score {self.location} run data get {cpl.location}")
            else:
                ctx.file.append(f"execute store result score {self.location} run data get {cpl.location} {FLOAT_PREC}")
            return self
        if t_want == "int" and t_have == "float":
            ctx.file.append(f"scoreboard players operation {self.location} /= FLOAT_PREC __temp__")
        if t_want == "float" and t_have == "int":
            ctx.file.append(f"scoreboard players operation {self.location} *= FLOAT_PREC __temp__")
        return self

    def _set_add(self, ctx, cpl):
        if cpl.is_lit_eq(0):
            return self
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
        if cpl.is_lit_eq(0):
            return self
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
        if cpl.is_lit_eq(1):
            return self
        if isinstance(cpl, CplInt) or isinstance(cpl, CplFloat):
            return self._set_mul(ctx, cpl.cache(ctx, force="score", force_t=self.unique_type.type))
        if isinstance(cpl, CplScore):
            ctx.file.append(f"scoreboard players operation {self.location} *= {cpl.location}")
            if cpl.unique_type.type == "float":
                ctx.file.append(f"scoreboard players operation {self.location} /= FLOAT_PREC __temp__")
            return self
        if not isinstance(cpl, CplIntNBT) and not isinstance(cpl, CplFloatNBT):
            return None
        return self._set_mul(ctx, cpl.cache(ctx, force="score", force_t=self.unique_type.type))

    def _set_div(self, ctx, cpl):
        if cpl.is_lit_eq(0):
            raise_syntax_error("Divide by zero", self.token)
        if cpl.is_lit_eq(1):
            return self
        if isinstance(cpl, CplInt) or isinstance(cpl, CplFloat):
            return self._set_div(ctx, cpl.cache(ctx, force="score", force_t=self.unique_type.type))
        if isinstance(cpl, CplScore):
            if cpl.unique_type.type == "float":
                ctx.file.append(f"scoreboard players operation {self.location} *= FLOAT_PREC __temp__")
            ctx.file.append(f"scoreboard players operation {self.location} /= {cpl.location}")
            return self
        if not isinstance(cpl, CplIntNBT) and not isinstance(cpl, CplFloatNBT):
            return None
        return self._set_div(ctx, cpl.cache(ctx, force="score", force_t=self.unique_type.type))

    def _set_mod(self, ctx, cpl):
        if cpl.is_lit_eq(0):
            raise_syntax_error("Modulo by zero", self.token)
        if cpl.is_lit_eq(1) and self.unique_type.type == "int":
            return self
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

    def _set_pow(self, ctx, cpl):
        if cpl.unique_type.type == "float":
            return None
        return self._set(ctx,
                         ctx.transpiler.builtin_vars["Math"].value._call_index(ctx, "ipow", [self, cpl], self.token))

    def _add(self, ctx, cpl):
        if cpl.is_lit_eq(0):
            return self
        c = self._cache(ctx)
        if self.unique_type.type == "int" and cpl.unique_type.type == "float":
            c._force_float(ctx)
        return c._set_add(ctx, cpl)

    def _sub(self, ctx, cpl):
        if cpl.is_lit_eq(0):
            return self
        c = self._cache(ctx)
        if self.unique_type.type == "int" and cpl.unique_type.type == "float":
            c._force_float(ctx)
        return c._set_sub(ctx, cpl)

    def _mul(self, ctx, cpl):
        if cpl.is_lit_eq(0):
            return cpl
        if cpl.is_lit_eq(1):
            return self
        c = self._cache(ctx)
        if self.unique_type.type == "int" and cpl.unique_type.type == "float":
            c._force_float(ctx)
        return c._set_mul(ctx, cpl)

    def _div(self, ctx, cpl):
        if cpl.is_lit_eq(0):
            raise_syntax_error("Divide by zero", self.token)
        if cpl.is_lit_eq(1):
            return cpl
        c = self._cache(ctx)
        if self.unique_type.type == "int" and cpl.unique_type.type == "float":
            c._force_float(ctx)
        return c._set_div(ctx, cpl)

    def _mod(self, ctx, cpl):
        if cpl.is_lit_eq(0):
            raise_syntax_error("Modulo by zero", self.token)
        if cpl.is_lit_eq(1) and self.unique_type.type == "int":
            return cpl
        c = self._cache(ctx)
        if self.unique_type.type == "int" and cpl.unique_type.type == "float":
            c._force_float(ctx)
        return c._set_mod(ctx, cpl)

    def _pow(self, ctx, cpl):
        if cpl.unique_type.type == "float":
            return None
        return ctx.transpiler.builtin_vars["Math"].value._call_index(ctx, "ipow", [self, cpl], self.token)

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
            eid = f"int_{get_uuid()} __temp__"
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
        if isinstance(cpl, CplSelector):
            return cpl._and(ctx, self)
        if cpl.unique_type.type in {"array", "object"}:
            return self
        if isinstance(cpl, CplInt) or isinstance(cpl, CplFloat) or isinstance(cpl, CplString):
            if not cpl.value:
                return CplInt(self.token, 0)
            return self
        if isinstance(cpl, CplNBT):
            cpl = cpl.cache(ctx, force="score")
        eid = f"int_{get_uuid()} __temp__"
        ctx.file.append(f"scoreboard players set {eid} 0")
        ctx.file.append(f"execute "
                        f"unless score {self.location} matches 0..0 "
                        f"unless score {cpl.location} matches 0..0 "
                        f"run scoreboard players set {eid} 1")
        return CplScore(self.token, eid)

    def _or(self, ctx, cpl):
        if isinstance(cpl, CplSelector):
            return cpl._and(ctx, self)
        if cpl.unique_type.type in {"array", "object"}:
            return CplInt(self.token, 1)
        if isinstance(cpl, CplInt) or isinstance(cpl, CplFloat) or isinstance(cpl, CplString):
            if cpl.value:
                return CplInt(self.token, 1)
            return self
        if isinstance(cpl, CplNBT):
            cpl = cpl.cache(ctx, force="score")
        eid = f"int_{get_uuid()} __temp__"
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
            return {
                "score": {
                    "name": ls[0],
                    "objective": ls[1]
                }
            }
        eid = get_uuid()
        ctx.file.append(
            f"execute store result storage temp _{eid} float {1 / FLOAT_PREC:.7f} run scoreboard players get {self.location}")
        return {
            "storage": "temp",
            "nbt": f"_{eid}"
        }


class CplSelector(Cpl):
    def __init__(self, token, value):
        # type: (Token | None, str) -> None
        super().__init__(token)
        self.value = value
        self.unique_type = SELECTOR_TYPE

    def get_py_value(self):
        return None

    def _get_index(self, ctx, index):
        if not isinstance(index, CplString):
            return None
        if index.value not in ENTITIES_OBJ.content:
            return None
        return val_nbt(self.token, f"entity {self.value} {index.value}", ENTITIES_OBJ.content[index.value])

    def _cache(self, ctx, score_loc=None, nbt_loc=None, force=None, force_t=None):
        raise_syntax_error("Selectors cannot be stored", self.token)

    def get_data_str(self, ctx):
        raise_syntax_error("Selectors cannot be used in operations", self.token)

    def tellraw_object(self, ctx):
        return {"selector": self.value}

    def _and(self, ctx, cpl):
        if isinstance(cpl, CplInt) or isinstance(cpl, CplFloat):
            return self if cpl.value != 0 else CplInt(self.token, 0)
        score_loc = f"int_{get_uuid()} __temp__"
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
        score_loc = f"int_{get_uuid()} __temp__"
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


class CplString(CplLiteral):
    def __init__(self, token, value, is_fn_reference=False):
        # type: (Union | None, str, bool) -> None
        value = str(value)
        if token is None:
            token = Token(str(value), TokenType.STRING_LITERAL, 0, len(str(value)))
        super().__init__(token, value)
        self.unique_type = STRING_TYPE
        self.is_fn_reference = is_fn_reference

    def get_py_value(self):
        return self.value

    def _call(self, ctx, arguments, token):
        if not self.is_fn_reference:
            return None
        return ctx.transpiler.run_function_with_cpl(ctx, self.value, arguments, self.token)

    def _cache(self, ctx, score_loc=None, nbt_loc=None, force=None, force_t=None):
        if force == "score":
            raise ValueError("Cannot store string as score")
        ctx.file.append(f"data modify {nbt_loc} set {self.get_data_str(ctx)}")
        return CplStringNBT(self.token, nbt_loc)

    def get_data_str(self, ctx):
        return f"value {json.dumps(self.value)}"

    def _get_index(self, ctx, index: Cpl):
        if isinstance(index, CplString) and index.value == "length":
            return CplInt(self.token, len(self.value))
        return None

    def _get_slice(self, ctx, index1, index2, index3, token):
        if isinstance(index1, CplInt) and isinstance(index2, CplInt) and isinstance(index3, CplInt):
            return CplString(self.token, self.value[index1.value:index2.value:index3.value])
        return self.cache(ctx)._get_slice(ctx, index1, index2, index3, token)

    def _call_index(self, ctx, index: str, arguments: List[Cpl], token):
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
                return self._cache(ctx)._call_index(ctx, index, arguments, token)
            return CplString(self.token, self.value[arg0.value:arg1.value])
        if index == "toArray":
            if len(arguments) != 0:
                return 0
            return CplArray(self.token, list(map(lambda x: CplString(self.token, x), self.value)))
        if index == "toLowerCase" or index == "toUpperCase":
            if len(arguments) != 0:
                return 0
            return CplString(self.token, self.value.upper() if index == "toUpperCase" else self.value.lower())
        if index == "replace" or index == "replaceAll":
            if len(arguments) != 2:
                return 2
            arg0 = arguments[0]
            arg1 = arguments[1]
            if isinstance(arg0, CplString) and isinstance(arg1, CplString):
                return CplString(self.token,
                                 self.value.replace(arg0.value, arg1.value, 1 if index == "replace" else -1))
            if not isinstance(arg0, CplStringNBT):
                return None
            return self.cache(ctx)._call_index(ctx, index, arguments, token)
        if index == "split":
            if len(arguments) != 1:
                return 1
            arg0 = arguments[0]
            if isinstance(arg0, CplString):
                return CplString(self.token, self.value.split(arg0.value))
            if not isinstance(arg0, CplStringNBT):
                return None
            return self.cache(ctx)._call_index(ctx, index, arguments, token)
        return None

    def _add(self, ctx, cpl):
        if isinstance(cpl, CplString):
            return CplString(self.token, self.value + cpl.value)
        if not isinstance(cpl, CplStringNBT):
            return None
        eid = f"storage temp _{get_uuid()}"
        file_name = ctx.transpiler.get_temp_file_name(
            f"$data modify {eid} set value '{self.value}$(_0)'")
        cpl.cache(ctx, nbt_loc="string_concat _0", force="nbt")
        ctx.file.append(f"function {ctx.transpiler.pack_namespace}:{file_name} with storage string_concat")
        return CplStringNBT(self.token, eid)

    def _and(self, ctx, cpl):
        return cpl._and(ctx, CplInt(self.token, len(self.value)))

    def _or(self, ctx, cpl):
        return cpl._or(ctx, CplInt(self.token, len(self.value)))

    def _eq_neq(self, ctx, cpl, is_eq):
        if isinstance(cpl, CplString):
            return CplInt(self.token, (self.value == cpl.value) * is_eq)
        if not isinstance(cpl, CplStringNBT):
            return None
        return cpl._eq_neq(ctx, self, is_eq)

    def tellraw_object(self, ctx):
        return {"text": self.value}


class CplTuple(Cpl):
    def __init__(self, token, value):
        # type: (Token | None, List[Cpl]) -> None
        self.unique_type: CplDefArray
        super().__init__(token)
        self.value = value
        self.unique_type = CplDefTuple(list(map(lambda x: x.unique_type, value)))
        ls = []
        for v in value:
            vl = v.get_py_value()
            if vl is None:
                raise_syntax_error("Tuples(constant arrays) cannot have non-literal values", token)
            ls.append(vl)
        self._py_val = ls

    def get_py_value(self):
        return self._py_val

    def _get_index(self, ctx, index: Cpl):
        if isinstance(index, CplString) and index.value == "length":
            return len(self.value)
        if isinstance(index, CplInt) or isinstance(index, CplString):
            try:
                return self.value[int(index.value)]
            except IndexError:
                return None
        if isinstance(index, CplFloat):
            return None
        return None

    def _get_slice(self, ctx, index1, index2, index3, token):
        # TODO: this
        return None

    def tellraw_object(self, ctx):
        return {"text": json.dumps(self._py_val)}


from .transpiler import TranspilerContext, raw_group_args
