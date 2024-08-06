from enum import Enum
from typing import Dict, Union, List, Any

FLOAT_PREC = 1000
INT_LIMIT = 2147483647


def get_float_limit():
    return INT_LIMIT / FLOAT_PREC


_expr_id = 0

VERSION_RADON = "2.1.3"


def basic_calc(a: Union[int, float], op: str, b: Union[int, float]) -> int | float:
    if op == "+":
        return a + b
    elif op == "-":
        return a - b
    elif op == "*":
        return a * b
    elif op == "/":
        return a / b
    elif op == "%":
        return a % b
    else:
        assert False


def basic_cmp(a, op: str, b):
    if op == ">":
        return a > b
    elif op == "<":
        return a < b
    elif op == ">=":
        return a >= b
    elif op == "<=":
        return a <= b
    else:
        assert False


def inv_cmp(op: str):
    if op == ">":
        return "<="
    elif op == "<":
        return ">="
    elif op == ">=":
        return "<"
    elif op == "<=":
        return ">"
    elif op == "==":
        return "!="
    elif op == "!=":
        return "=="
    else:
        assert False


# Version argument can be: a pack format, a minecraft version like 1.16.5, or a snapshot version like 23w32a
def get_pack_format(version):
    if not version:
        return None
    if isinstance(version, int):
        return version
    if version.isnumeric() and (4 <= int(version) <= 18 or version == "48"):
        return int(version)
    version = version.split("-")[0]
    if len(version) > 2 and version[2] == "w":
        version = version[:-1]
        spl = version.split("w")
        v = spl[0]
        if not v.isnumeric():
            return None
        v = int(v)
        k = spl[1]
        if not k.isnumeric():
            return None
        k = int(k)
        if v < 17 or (v == 17 and k < 48):
            return None
        if v < 20:
            return 4
        if v < 21:
            return 7
        if v < 22:
            return 8
        if v < 23:
            return 10
        if v < 24:
            if k < 6:
                return 11
            if k < 12:
                return 12
            if k < 16:
                return 13
            if k < 18:
                return 14
            if k < 31:
                return 15
            if k < 32:
                return 16
            if k > 35:
                return None
            return 17
        return None
    spl = version.split(".")
    if spl[0] != "1" or len(spl) == 1 or len(spl) > 3:
        return None
    v = spl[1]
    if not v.isnumeric():
        return None
    v = int(v)
    k = spl[2] if len(spl) == 3 else "0"
    if not k.isnumeric():
        return None
    k = int(k)
    if v > 21 or k > 100:
        return None
    vk = v * 100 + k
    if vk < 1300:
        return None
    if vk < 1500:
        return 4
    if vk < 1602:
        return 5
    if vk < 1700:
        return 6
    if vk < 1800:
        return 7
    if vk < 1802:
        return 8
    if vk < 1900:
        return 9
    if vk < 1904:
        return 10
    if vk < 2000:
        return 12
    if vk < 2002:
        return 15
    if vk < 2100:
        return 18
    return 48


def reset_expr_id():
    global _expr_id
    _expr_id = 0


def get_uuid():
    global _expr_id
    _expr_id += 1
    return _expr_id


class TokenType(Enum):
    KEYWORD = "keyword"
    IDENTIFIER = "identifier"
    STRING_LITERAL = "string_literal"
    INT_LITERAL = "int_literal"
    FLOAT_LITERAL = "float_literal"
    OPERATOR = "operator"
    WHITESPACE = "whitespace"
    SYMBOL = "symbol"
    EOL = "eol"  # end of line, new line
    EOF = "eof"  # end of file
    EOE = "eoe"  # end of expression, semicolon

    GROUP = "group"
    FUNCTION_CALL = "function_call"
    LAMBDA_FUNCTION = "lambda_function"
    SELECTOR = "selector"
    SELECTOR_IDENTIFIER = "selector_identifier"
    BLOCK_IDENTIFIER = "block_identifier"

    POINTER = "pointer"  # This is not a token type. This is used to point to a part of the user code.


class UniversalStrMixin:
    def __str__(self):
        attributes = [
            f"{key}={list(map(str, value)) if isinstance(value, list) else value}"
            for key, value in filter(lambda x: x[0] != "code", self.__dict__.items())
        ]
        return f"{self.__class__.__name__}({', '.join(attributes)})"


class CplDef:
    def __init__(self, type: str):
        self.type = type

    def __eq__(self, other) -> bool:
        return str(self) == str(other)

    def __ne__(self, other):
        return str(self) != str(other)

    def get_sample_value(self) -> str:
        return ""


class VariableDeclaration:
    def __init__(self, name: str, type: Any, constant: bool, init_func=None, get_func=None):
        self.name = name
        self.value = None
        if not type.__class__.__name__.startswith("CplDef"):
            self.value = type
            type = type.unique_type
        self.type = type
        self.constant = constant
        self.init_func = init_func
        self.get_func = get_func


class CplDefInt(CplDef):
    def __init__(self):
        super().__init__("int")

    def __str__(self) -> str:
        return "int"

    def get_sample_value(self) -> str:
        return "0"


class CplDefFloat(CplDef):
    def __init__(self):
        super().__init__("float")

    def __str__(self) -> str:
        return "float"

    def get_sample_value(self) -> str:
        return "0.0"


class CplDefString(CplDef):
    def __init__(self):
        super().__init__("string")

    def __str__(self) -> str:
        return "string"

    def get_sample_value(self) -> str:
        return "''"


class CplDefArray(CplDef):
    def __init__(self, content: CplDef):
        super().__init__("array")
        self.content = content

    def __str__(self) -> str:
        return str(self.content) + "[]"

    def get_sample_value(self) -> str:
        return f"[{self.content.get_sample_value()}]"


class CplDefTuple(CplDef):
    def __init__(self, content: List[CplDef]):
        super().__init__("tuple")
        self.content = content

    def __str__(self) -> str:
        return "[" + ", ".join(map(str, self.content)) + "]"

    def get_sample_value(self) -> str:
        return f"[{', '.join(map(lambda x: x.get_sample_value(), self.content))}]"


class CplDefObject(CplDef):
    def __init__(self, type: Dict[str, CplDef], class_name: str | None = None):
        super().__init__("object")
        self.content = type
        self.class_name = class_name

    def __str__(self) -> str:
        if self.class_name:
            return self.class_name
        return (
                "{"
                + ", ".join([str(k) + ": " + str(v) for k, v in self.content.items()])
                + "}"
        )

    def get_sample_value(self) -> str:
        return (
                "{"
                + ", ".join([k + ": " + self.content[k].get_sample_value() for k in self.content])
                + "}"
        )


class CplDefSelector(CplDef):
    def __init__(self):
        super().__init__("selector")

    def __str__(self) -> str:
        return "selector"

    def get_sample_value(self) -> str:
        raise "Selectors cannot be sampled"


class CplDefFunction(CplDef):
    def __init__(self, arguments: List[CplDef], returns: CplDef | None):
        super().__init__("string")
        self.arguments = arguments
        self.returns = returns

    def __str__(self) -> str:
        return "((" + ", ".join(map(str, self.arguments)) + ") => " + str(self.returns or "void") + ")"

    def get_sample_value(self) -> str:
        raise "Functions cannot be sampled"


INT_TYPE = CplDefInt()
FLOAT_TYPE = CplDefFloat()
STRING_TYPE = CplDefString()
SELECTOR_TYPE = CplDefSelector()

str_counter = {}


def get_str_count(s):
    if s in str_counter:
        return str_counter[s]
    str_counter[s] = get_uuid()
    return str_counter[s]
