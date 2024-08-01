from typing import Any, Dict, List

from .error import raise_syntax_error, raise_syntax_error_t

SET_OP = ["=", "+=", "-=", "*=", "/=", "%="]


def is_float(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


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
WORD_OPERATORS = ["is not", "is", "and", "or"]
INC_OP = ["++", "--"]
CMP_OP = ["==", "!=", ">", "<", ">=", "<=", "is", "is not"]
CMP_COMBINE_OP = ["&&", "||", "and", "or"]
SYMBOL = list("}]){[(:,@\\.~^$")
QUOTES = list("\"'")
WHITESPACE = list(" \t\v")
EOL_CHAR = "\n"
EOE_CHAR = ";"
NON_WORD_CHARACTERS = OPERATORS + QUOTES + WHITESPACE + SYMBOL + [EOL_CHAR, EOE_CHAR]

KEYWORDS = [
    "if",
    "unless",
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
    # "int",
    # "float",
    "string",
    "from",
    "import",
    "as",
]
EXTRA_KEYWORDS = ["and", "or", "is", "not"]

OPEN_GROUP = list("{[(")
CLOSE_GROUP = list("}])")
CLOSE_MATCH = {"}": "{", "]": "[", ")": "("}


class Token:
    def __init__(self, code: str, type: Any, start: int, end: int):
        self.code = code
        self.type = type
        self.start = start
        self.end = end
        self.value = ""
        self.update_value()

    def update_value(self):
        self.value = self.code[self.start: self.end]
        return self.value

    def __str__(self) -> str:
        return f"Token(type={self.type}, start={self.start}, end={self.end}, value={self.value})"


from .utils import (
    FLOAT_TYPE,
    INT_TYPE,
    STRING_TYPE,
    CplDef,
    CplDefArray,
    CplDefObject,
    TokenType, SELECTOR_TYPE, CplDefFunction,
)

EmptyToken = Token("", TokenType.SYMBOL, 0, 0)


class GroupToken(Token):
    def __init__(self, code: str, start: int, end: int):
        super().__init__(code, TokenType.GROUP, start, end)
        self.parent: GroupToken = EmptyGroup
        self.children: List[Token | GroupToken] = []
        self.open: Token = EmptyToken
        self.close: Token = EmptyToken
        self.func: Token | None = None
        self._temp: Any = None


EmptyGroup: GroupToken = Token("", TokenType.GROUP, 0, 0)  # type: ignore


class SelectorIdentifierToken(Token):
    def __init__(
            self,
            code: str,
            start: int,
            end: int,
            selector: Token,
            sep: Token,
            name: Token,
    ):
        super().__init__(code, TokenType.SELECTOR_IDENTIFIER, start, end)
        self.selector = selector
        self.sep = sep
        self.name = name


class BlockIdentifierToken(Token):
    def __init__(
            self,
            code: str,
            start: int,
            end: int,
            block: GroupToken,
            sep: Token,
            name: Token,
    ):
        super().__init__(code, TokenType.BLOCK_IDENTIFIER, start, end)
        self.block = block
        self.sep = sep
        self.name = name


class LambdaFunctionToken(Token):
    def __init__(
            self,
            code: str,
            start: int,
            end: int,
            arguments: GroupToken,
            body: GroupToken
    ):
        super().__init__(code, TokenType.LAMBDA_FUNCTION, start, end)
        self.arguments = arguments
        self.body = body


def cpl_def_from_tokens(classes, tokens):
    # type: (Dict[str, Any] | List[str], List[Token]) -> CplDef | None
    """
    Valid type examples:
    int
    float
    string
    int[]
    string[][][]
    {"a": int, "b": float}
    """
    if len(tokens) == 0:
        return None
    type = None
    t0 = tokens[0]
    if t0.value == "int":
        type = INT_TYPE
    if t0.value == "float":
        type = FLOAT_TYPE
    if t0.value == "string":
        type = STRING_TYPE
    if t0.value == "selector":
        type = SELECTOR_TYPE
    if isinstance(t0, GroupToken) and t0.open.value == "(" and len(t0.children) > 2:
        t0c = t0.children
        if not isinstance(t0c[0], GroupToken) or t0c[0].open.value != "(" or t0c[1].value != "=" or t0c[2].value != ">":
            return None

        type = CplDefFunction(
            list(map(lambda x: cpl_def_from_tokens(classes, x), split_tokens(t0c[0].children))),
            cpl_def_from_tokens(classes, t0c[3:])
        )
    if isinstance(t0, GroupToken) and t0.open.value == "{":
        dct = {}
        spl = split_tokens(t0.children)
        for part in spl:
            if (
                    len(part) < 3
                    or part[0].type not in {TokenType.STRING_LITERAL, TokenType.IDENTIFIER}
                    or part[1].value != ":"
            ):
                return None
            k = part[0].value
            if part[0].type == TokenType.STRING_LITERAL:
                k = k[1:-1]
            dct[k] = cpl_def_from_tokens(classes, part[2:])
        type = CplDefObject(dct, None)
    if not type:
        if t0.type == TokenType.IDENTIFIER:
            if t0.value not in classes:
                return None
            type = classes[t0.value].attributes.unique_type if isinstance(classes, dict) else CplDefObject({}, t0.value)
        else:
            return None
    for t in tokens[1:]:
        if not isinstance(t, GroupToken) or t.open.value != "[" or len(t.children) != 0:
            return None
        type = CplDefArray(type)
    return type


def split_tokens(tokens: List[Token], sep=",", comma_errors=True) -> List[List[Token]]:
    ind = 0
    parts = [[]]
    while True:
        if ind == len(tokens):
            break
        token = tokens[ind]
        if token.value == sep:
            if comma_errors and len(parts[-1]) == 0:
                raise_syntax_error(f"Unexpected '{sep}'", token)
            parts.append([])
        else:
            parts[-1].append(token)
        ind += 1

    if comma_errors and len(parts[-1]) == 0:
        if len(parts) != 1:
            raise_syntax_error(f"Unexpected '{sep}'", tokens[-1])
        parts.pop()

    return parts


# Convert {[(...)]} and func(...) into its own tokens
def group_tokens(tokens: List[Token]) -> List[Token]:
    length = len(tokens)
    if length == 0:
        return []
    code = tokens[0].code
    parent: GroupToken = GroupToken(code, 0, len(code))
    base = parent

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
                    and len(pc[-1].selector.value
                            if isinstance(pc[-1], SelectorIdentifierToken)
                            else pc[-1].value) == 2  # has to be a short selector like @a, @r
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

            tok = GroupToken(code, token.start, 0)
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

            if func is not None:
                tok.type = TokenType.FUNCTION_CALL
                tok.func = func
                tok.start = func.start

            is_block_identifier = (
                    token.value == "["
                    and len(pc) > 1
                    and pc[-1].value == ":"
                    and pc[-2].type == TokenType.IDENTIFIER
            )

            if is_block_identifier:
                tok._temp = "block"

            if not is_selector and not is_block_identifier:
                pc.append(tok)
            parent = tok
            continue
        if token.type == TokenType.SYMBOL and token.value in CLOSE_GROUP:
            if parent.parent is None or parent.open.value != CLOSE_MATCH[token.value]:
                raise_syntax_error("Unexpected parentheses", token)
            parent.close = token
            parent.end = token.end
            parent.update_value()

            ppc = parent.parent.children

            if (token.value == "}" and len(ppc) > 3 and ppc[-2].value == ">" and ppc[-3].value == "="
                    and ppc[-4].type == TokenType.GROUP and ppc[-4].open.value == "("):
                ppc.pop()
                ppc.pop()
                ppc.pop()
                arguments = ppc.pop()
                ppc.append(
                    LambdaFunctionToken(
                        parent.code,
                        arguments.start,
                        parent.end,
                        arguments,
                        parent
                    )
                )

            if parent._temp == "block":
                colon = ppc.pop()
                ident = ppc.pop()
                ppc.append(
                    BlockIdentifierToken(
                        parent.code,
                        ident.start,
                        parent.end,
                        parent,
                        colon,
                        ident,
                    )
                )

            if (
                    parent.type == TokenType.SELECTOR
                    or parent.type == TokenType.SELECTOR_IDENTIFIER
            ):
                merge = ppc[-1]
                merge.end = parent.end
                merge.update_value()
                if isinstance(merge, SelectorIdentifierToken):
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
                and tokens[-1].end == index[0]
                and tokens[-2].type == TokenType.IDENTIFIER
        ):
            token = SelectorIdentifierToken(
                code,
                start=tokens[-2].start,
                end=index[0] + 2,
                selector=selToken,
                sep=tokens[-1],
                name=tokens[-2],
            )
            tokens.pop()
            tokens.pop()
            tokens.append(token)
            index[0] += 1
            return
        tokens.append(selToken)
        index[0] += 1
        return
    if code[index[0]: index[0] + 8] == "#define " and (
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
        m = code[si: index[0] + 1].split(" ")
        macros.append([m[0], _tokenize(" ".join(m[1:]), False)[0][:-1]])
        return
    if char == ":" and index[0] != len(code) - 1 and code[index[0] + 1] == ":":
        tokens.append(Token(code, TokenType.SYMBOL, index[0], index[0] + 2))
        index[0] += 1
        return
    if char in SYMBOL:
        tokens.append(Token(code, TokenType.SYMBOL, index[0], index[0] + 1))
        return
    if (char == "#") or (
            char == "/" and index[0] != len(code) - 1 and code[index[0] + 1] == "/"
    ):
        while index[0] < len(code):
            if code[index[0]] == "\n":
                index[0] -= 1
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
        op_got = code[index[0]: index[0] + len(op)]
        if op_got == op and (op not in WORD_OPERATORS or code[index[0] + len(op)] == " "):
            tokens.append(Token(code, TokenType.OPERATOR, index[0], index[0] + len(op)))
            index[0] += len(op) - 1
            return
    if char in OPERATORS:
        tokens.append(Token(code, TokenType.OPERATOR, index[0], index[0] + 1))
        return
    if char in QUOTES:
        start_index = index[0]
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
                "Unterminated string", code, start_index, start_index + 1
            )
        value = code[start_index + 1: index[0]]
        token: Token = Token(code, TokenType.STRING_LITERAL, start_index, index[0] + 1)
        tokens.append(token)
        return
    start_index = index[0]
    index[0] += 1
    while index[0] < len(code):
        char2 = code[index[0]]
        if char2 in NON_WORD_CHARACTERS:
            index[0] -= 1
            break
        index[0] += 1
    if index[0] == len(code):
        index[0] -= 1
    value = code[start_index: index[0] + 1]
    type = TokenType.IDENTIFIER
    if value in KEYWORDS:
        type = TokenType.KEYWORD
    elif str.isnumeric(value):
        type = TokenType.INT_LITERAL
    if value not in KEYWORDS and len(tokens) > 0 and tokens[-1].value == "-" and (
            len(tokens) == 1 or tokens[-2].type in {TokenType.OPERATOR, TokenType.SYMBOL}):
        tokens.pop()
        start_index -= 1
    if (
            type == TokenType.INT_LITERAL
            and len(tokens) > 0
            and tokens[-1].value == "."
            and tokens[-1].end == start_index
            and (len(tokens) == 1 or tokens[-2].end != start_index - 1 or tokens[-2].type == TokenType.INT_LITERAL)):
        if len(tokens) > 1 and tokens[-2].type == TokenType.INT_LITERAL:
            tokens.pop()
        start = tokens.pop().start
        tokens.append(Token(code, TokenType.FLOAT_LITERAL, start, index[0] + 1))
        return True
    new_t = Token(code, type, start_index, index[0] + 1)
    if type == TokenType.IDENTIFIER and len(tokens) > 1 and tokens[-1].value == ":" and tokens[-2].type == TokenType.IDENTIFIER:
        sep = tokens.pop()
        ident = tokens.pop()
        tokens.append(SelectorIdentifierToken(code, ident.start, index[0] + 1, new_t, sep, ident))
        return True
    tokens.append(new_t)


def _tokenize(code: str, can_macro=True):
    code = code.replace("\r", "")

    tokens: List[Token] = []
    macros = []

    index = [0]
    length = len(code)
    while index[0] < length:
        _tokenize_iterate(code, tokens, macros, index, can_macro)
        index[0] += 1

    tokens.append(Token(code, TokenType.EOF, length, length))
    return tokens, macros


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
    (tokens, macros) = _tokenize(code)
    new_tokens = group_tokens(apply_macros(tokens, macros))
    return new_tokens, macros
