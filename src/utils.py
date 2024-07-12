from typing import Any, List, Union, Literal
from enum import Enum
import os
import sys


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
        type: Union[Literal["radon"], Literal["mcfunction"], Literal["python"], Literal["python-raw"]],
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
