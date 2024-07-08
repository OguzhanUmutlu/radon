from __future__ import annotations
from typing import List, Tuple
from error import raise_syntax_error, raise_syntax_error_t
from enum import Enum

SET_OP = ["=", "+=", "-=", "*=", "/=", "%="]


def is_float(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


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

    POINTER = "pointer"  # This is not a token type. This is used to point to a part of the user code.


OPERATORS = list("+-*/!=%")
OPERATORS_L = [
    "==",
    "!=",
    "++",
    "--",
    "+=",
    "-=",
    "*=",
    "/=",
    "%=",
    "**",
    "&&",
    "||",
    ">=",
    ">",
    "<=",
    "<",
    "is not",
    "is",
    "and",
    "or",
]
INC_OP = ["++", "--"]
CMP_OP = ["==", "!=", ">", "<", ">=", "<=", "is", "is not"]
CMP_COMBINE_OP = ["&&", "||", "and", "or"]
SYMBOL = list("}]){[(:,@\\")
QUOTES = list("\"'")
WHITESPACE = list(" \t\v")
EOL_CHAR = "\n"
EOE_CHAR = ";"
NON_WORD_CHARACTERS = OPERATORS + QUOTES + WHITESPACE + SYMBOL + [EOL_CHAR, EOE_CHAR]

KEYWORDS = [
    "if",
    "else",
    "elif",
    "for",
    "while",
    "until",
    "function",
    "return",
    "break",
    "continue",
    "define",
    "int",
    "float",
    "string",
]
EXTRA_KEYWORDS = ["and", "or", "is", "not"]

OPEN_GROUP = list("{[(")
CLOSE_GROUP = list("}])")
CLOSE_MATCH = {"}": "{", "]": "[", ")": "("}


class Token:
    def __init__(self, code: str, type: TokenType, start: int, end: int):
        self.code = code
        self.type = type
        self.start = start
        self.end = end
        self.value = ""
        self.update_value()

    def update_value(self):
        self.value = self.code[self.start : self.end]
        return self.value

    def __str__(self) -> str:
        return f"Token(type={self.type}, start={self.start}, end={self.end}, value={self.value})"


class Tokenizer:
    def split_tokens(tokens: List[Token], sep=","):
        ind = 0
        parts = [[]]
        while True:
            if ind == len(tokens):
                break
            token = tokens[ind]
            if token.value == sep:
                if len(parts[-1]) == 0:
                    raise_syntax_error("Unexpected comma", token)
                parts.append([])
            else:
                parts[-1].append(token)
            ind += 1

        if len(parts[-1]) == 0:
            if len(parts) != 1:
                raise_syntax_error("Unexpected comma", tokens[-1])
            parts.pop()

        return parts

    # Convert {[(...)]} and func(...) into its own tokens
    def group_tokens(tokens: List[Token]) -> List[Token]:
        length = len(tokens)
        if length == 0:
            return []
        code = tokens[0].code
        parent = Token(code, TokenType.GROUP, 0, len(code))
        base = parent
        parent.parent = None
        parent.children = []
        parent.open = None
        parent.close = None
        parent.func = None

        index = -1
        while True:
            index += 1
            if index >= length:
                break
            token = tokens[index]
            pc = parent.children
            lc = len(pc)
            if token.type == TokenType.SYMBOL and token.value in OPEN_GROUP:
                func = None

                # @r[...something]
                is_selector = (
                    token.value == "["
                    and index != 0
                    and lc != 0
                    and (
                        pc[-1].type == TokenType.SELECTOR
                        or pc[-1].type == TokenType.SELECTOR_IDENTIFIER
                    )
                    and len(
                        (
                            pc[-1]
                            if pc[-1].type == TokenType.SELECTOR
                            else pc[-1].selector
                        ).value
                    )
                    == 2  # has to be a short selector like @a, @r
                )

                # func(arguments...)
                if (
                    not is_selector
                    and token.value == "("
                    and index != 0
                    and lc != 0
                    and pc[-1].type == TokenType.IDENTIFIER
                    and pc[-1].value[0] not in list("0123456789.")
                ):
                    func = tokens[index - 1]
                    pc.pop()

                tok = Token(code, TokenType.GROUP, token.start, 0)
                tok.parent = parent
                tok.children = []
                tok.open = token
                tok.func = None

                if is_selector:
                    tok.type = (
                        TokenType.SELECTOR
                        if pc[-1].type == TokenType.SELECTOR
                        else TokenType.SELECTOR_IDENTIFIER
                    )

                if func != None:
                    tok.type = TokenType.FUNCTION_CALL
                    tok.func = func
                    tok.start = func.start

                if not is_selector:
                    pc.append(tok)
                parent = tok
                continue
            if token.type == TokenType.SYMBOL and token.value in CLOSE_GROUP:
                if (
                    parent.parent == None
                    or parent.open.value != CLOSE_MATCH[token.value]
                ):
                    raise_syntax_error("Unexpected parentheses", token)
                parent._close = token
                parent.end = token.end
                parent.update_value()
                merge = None
                if (
                    parent.type == TokenType.SELECTOR
                    or parent.type == TokenType.SELECTOR_IDENTIFIER
                ):
                    merge = parent.parent.children[-1]
                    merge.end = parent.end
                    merge.update_value()
                if parent.type == TokenType.SELECTOR_IDENTIFIER:
                    merge.selector.end = parent.end
                    merge.selector.update_value()
                parent = parent.parent
                continue
            pc.append(token)

        if base != parent:
            parent.end = parent.start + 1
            raise_syntax_error("Incomplete parentheses", parent)

        return parent.children

    def _tokenize_iterate(
        code: str, tokens: List[Token], macros: List, index: List[int], can_macro: bool
    ):
        char = code[index[0]]
        if char == EOE_CHAR:
            tokens.append(Token(code, TokenType.EOE, index[0], index[0] + 1))
            return
        if char in WHITESPACE:
            # tokens.append(Token(code, TokenType.WHITESPACE, index[0], index[0] + 1))
            return
        if char == EOL_CHAR:
            tokens.append(Token(code, TokenType.EOL, index[0], index[0] + 1))
            return
        if (
            char == "@"
            and index[0] != len(code) - 1
            and code[index[0] + 1] in list("praens")
        ):
            selToken = Token(code, TokenType.SELECTOR, index[0], index[0] + 2)
            if (
                len(tokens) > 1
                and tokens[-1].value == ":"
                and tokens[-2].type == TokenType.IDENTIFIER
            ):
                token = Token(
                    code, TokenType.SELECTOR_IDENTIFIER, tokens[-2].start, index[0] + 2
                )
                token.selector = selToken
                token.sep = tokens[-1]
                token.name = tokens[-2]
                tokens.pop()
                tokens.pop()
                tokens.append(token)
                index[0] += 1
                return
            tokens.append(selToken)
            index[0] += 1
            return
        if code[index[0] : index[0] + 8] == "#define " and (
            len(tokens) == 0 or tokens[-1].type == TokenType.EOL
        ):
            if not can_macro:
                raise_syntax_error_t("Unexpected #define", code, index[0], index[0] + 8)
            si = index[0] + 8
            while index[0] < len(code):
                if code[index[0]] == "\n":
                    break
                index[0] += 1
            index[0] -= 1
            m = code[si : index[0] + 1].split(" ")
            macros.append([m[0], Tokenizer._tokenize(" ".join(m[1:]), False)[0][:-1]])
            return
        if char in SYMBOL:
            tokens.append(Token(code, TokenType.SYMBOL, index[0], index[0] + 1))
            return
        if char == "/" and index[0] != len(code) - 1 and code[index[0] + 1] == "/":
            while index[0] < len(code):
                if code[index[0]] == "\n":
                    break
                index[0] += 1
            return
        if char == "/" and index[0] != len(code) - 1 and code[index[0] + 1] == "*":
            line_index = 0
            while index[0] < len(code):
                if code[index[0]] == "\n":
                    line_index = index[0]
                if (
                    code[index[0]] == "*"
                    and index[0] + 1 < len(code)
                    and code[index[0] + 1] == "/"
                ):
                    index[0] += 1
                    if line_index != 0:
                        tokens.append(
                            Token(code, TokenType.EOL, line_index, line_index + 1)
                        )
                    break
                index[0] += 1
            return

        for op in OPERATORS_L:
            if code[index[0] : index[0] + len(op)] == op:
                token = Token(code, TokenType.OPERATOR, index[0], index[0] + len(op))
                if op in INC_OP:
                    if len(tokens) == 0 or (
                        tokens[-1].type != TokenType.IDENTIFIER
                        and tokens[-1].type != TokenType.SELECTOR_IDENTIFIER
                    ):
                        raise_syntax_error_t(
                            "Expected an identifier before the " + op + " token",
                            code,
                            index[0],
                            index[0] + len(op),
                        )
                    ident = tokens.pop()
                    group = Token(
                        code, TokenType.GROUP, ident.start, index[0] + len(op)
                    )
                    group.children = [ident, token]
                    group.open = Token("(", TokenType.SYMBOL, 0, 1)
                    group.close = Token(")", TokenType.SYMBOL, 0, 1)
                    tokens.append(group)
                else:
                    tokens.append(token)
                index[0] += len(op) - 1
                return
        if char in OPERATORS:
            tokens.append(Token(code, TokenType.OPERATOR, index[0], index[0] + 1))
            return
        if char in QUOTES:
            startIndex = index[0]
            index[0] += 1
            backslash = False
            while index[0] < len(code):
                char2 = code[index[0]]
                if (char2 == char and not backslash) or char2 == EOL_CHAR:
                    break
                if char == "\\":
                    backslash = not backslash
                else:
                    backslash = False
                index[0] += 1
            if index[0] == len(code) or code[index[0]] == EOL_CHAR:
                raise_syntax_error_t(
                    "Unterminated string", code, startIndex, startIndex + 1
                )
            value = code[startIndex + 1 : index[0]]
            token: Token = Token(
                code, TokenType.STRING_LITERAL, startIndex, index[0] + 1
            )
            tokens.append(token)
            return
        startIndex = index[0]
        index[0] += 1
        while index[0] < len(code):
            char2 = code[index[0]]
            if char2 in NON_WORD_CHARACTERS:
                index[0] -= 1
                break
            index[0] += 1
        if index[0] == len(code):
            index[0] -= 1
        value = code[startIndex : index[0] + 1]
        type = TokenType.IDENTIFIER
        if value in KEYWORDS:
            type = TokenType.KEYWORD
        elif str.isnumeric(value):
            type = TokenType.INT_LITERAL
        elif is_float(value):
            type = TokenType.FLOAT_LITERAL
        if value not in KEYWORDS and len(tokens) > 0 and tokens[-1].value == "-":
            tokens.pop()
            startIndex -= 1
        token = Token(code, type, startIndex, index[0] + 1)
        tokens.append(token)

    def _tokenize(code: str, can_macro=True) -> Tuple[List]:
        code = code.replace("\r", "")

        tokens: List[Token] = []
        macros = []

        index = [0]
        length = len(code)
        while index[0] < length:
            Tokenizer._tokenize_iterate(code, tokens, macros, index, can_macro)
            index[0] += 1

        tokens.append(Token(code, TokenType.EOF, length, length))
        return (tokens, macros)

    def apply_macros(tokens: List[Token], macros: List):
        new_tokens = []
        for token in tokens:
            found = False
            for macro in macros:
                if token.type == TokenType.IDENTIFIER and token.value == macro[0]:
                    found = True
                    new_tokens.extend(macro[1])
                    break
            if not found:
                new_tokens.append(token)
        return new_tokens

    def tokenize(code: str):
        (tokens, macros) = Tokenizer._tokenize(code)
        return (Tokenizer.group_tokens(Tokenizer.apply_macros(tokens, macros)), macros)
