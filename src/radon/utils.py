from typing import Any, List, Union, Literal
from enum import Enum

FLOAT_PREC = 1000

_expr_id = 0

VERSION_RADON = "0.0.3"


# Version argument can be: a pack format, a minecraft version like 1.16.5, or a snapshot version like 23w32a
def get_pack_format(version: str):
    if version.isnumeric() and (4 <= int(version) <= 18 or version == "48"):
        return int(version)
    version = version.split("-")[0]
    if version[2] == "w":
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


def get_expr_id():
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
    SELECTOR = "selector"
    SELECTOR_IDENTIFIER = "selector_identifier"
    STORAGE_NBT_IDENTIFIER = "storage_nbt_identifier"
    ENTITY_NBT_IDENTIFIER = "entity_nbt_identifier"

    POINTER = "pointer"  # This is not a token type. This is used to point to a part of the user code.


class UniversalStrMixin:
    def __str__(self):
        attributes = [
            f"{key}={list(map(str,value)) if isinstance(value, list) else value}"
            for key, value in filter(lambda x: x[0] != "code", self.__dict__.items())
        ]
        return f"{self.__class__.__name__}({', '.join(attributes)})"


class FunctionArgument:
    def __init__(self, type: str, name: str, id: str = ""):
        self.type = type
        self.name = name
        self.id = id


class VariableDeclaration:
    def __init__(self, type: str, constant: bool):
        self.type = type
        self.constant = constant


class FunctionDeclaration:
    def __init__(
        self,
        type: Union[
            Literal["radon"],
            Literal["mcfunction"],
            Literal["python"],
            Literal["python-raw"],
        ],
        name: str,
        returns: str,
        returnId: str,
        arguments: List[FunctionArgument] = [],
        direct: bool = False,
        libs: List[str] = [],
        initLibs: List[str] = [],
        function: Any = None,
        file_name: str = "",
    ):
        self.type = type
        self.name = name
        self.file_name = file_name
        self.returns = returns
        self.returnId = returnId
        self.arguments = arguments
        self.direct = direct
        self.libs = libs
        self.initLibs = initLibs
        self.function = function


class TranspilerContext:
    def __init__(
        self,
        transpiler,
        file_name: str,
        file: List[str],
        function: FunctionDeclaration | None,
        loop,
    ):
        self.transpiler = transpiler
        self.file_name = file_name
        self.file = file
        self.function = function
        self.loop = loop
