from enum import Enum
from typing import List, Tuple, Union

from .error import raise_syntax_error
from .tokenizer import (
    GroupToken,
    Token,
    TokenType,
    cpl_def_from_tokens,
    is_float,
    split_tokens,
    tokenize, CMP_OP, CMP_COMBINE_OP,
)
from .utils import UniversalStrMixin

ENDERS = [
    TokenType.EOL,
    TokenType.EOE,
    TokenType.EOF,
]

EXECUTE_MACROS = [
    "align",
    "anchored",
    "as",
    "at",
    "facing",
    "in",
    "on",
    "positioned",
    "rotated",
    "summon",
    "if",
    "unless",
    "store",
]

COMMANDS = [
    "ability",
    "advancement",
    "attribute",
    "ban",
    "ban-ip",
    "banlist",
    "bossbar",
    "clear",
    "clone",
    "damage",
    "data",
    "datapack",
    "debug",
    "defaultgamemode",
    "deop",
    "difficulty",
    "effect",
    "enchant",
    "execute",
    "experience",
    "xp",
    "fill",
    "fillbiome",
    "forceload",
    "function",
    "gamemode",
    "gamerule",
    "give",
    "item",
    "jfr",
    "kick",
    "kill",
    "list",
    "locate",
    "loot",
    "me",
    "msg",
    "tell",
    "w",
    "op",
    "pardon",
    "pardon-ip",
    "particle",
    "perf",
    "permission",
    "ops",
    "place",
    "playsound",
    "publish",
    "random",
    "sequence",
    "recipe",
    "reload",
    "return",
    "ride",
    "save-all",
    "save-off",
    "save-on",
    "say",
    "schedule",
    "scoreboard",
    "seed",
    "setblock",
    "setidletimeout",
    "setworldspawn",
    "spawnpoint",
    "spectate",
    "spreadplayers",
    "stop",
    "stopsound",
    "summon",
    "tag",
    "team",
    "teleport",
    "tp",
    "tell",
    "msg",
    "w",
    "tellraw",
    "time",
    "title",
    "tm",
    "teammsg",
    "tp",
    "teleport",
    "trigger",
    "w",
    "tell",
    "msg",
    "weather",
    "whitelist",
    "worldborder",
    "xp",
    "experience",
]

operators = {
    "**": {
        "p": 4,
        "a": "right",
    },
    "*": {
        "p": 3,
        "a": "left",
    },
    "/": {
        "p": 3,
        "a": "left",
    },
    "+": {
        "p": 2,
        "a": "left",
    },
    "-": {
        "p": 2,
        "a": "left",
    },
    "not": {
        "p": 2,
        "a": "left",
    },
    "is": {
        "p": 1,
        "a": "left",
    },
    "is not": {
        "p": 1,
        "a": "left",
    },
    "==": {
        "p": 1,
        "a": "left",
    },
    "!=": {
        "p": 1,
        "a": "left",
    },
    ">": {
        "p": 1,
        "a": "left",
    },
    "<": {
        "p": 1,
        "a": "left",
    },
    ">=": {
        "p": 1,
        "a": "left",
    },
    "<=": {
        "p": 1,
        "a": "left",
    },
    "or": {
        "p": 0,
        "a": "left",
    },
    "and": {
        "p": 0,
        "a": "left",
    },
    "||": {
        "p": 0,
        "a": "left",
    },
    "&&": {
        "p": 0,
        "a": "left",
    },
}

EXPR_EXPR = [
    TokenType.FUNCTION_CALL,
    TokenType.GROUP,
    TokenType.INT_LITERAL,
    TokenType.FLOAT_LITERAL,
    TokenType.STRING_LITERAL,
    TokenType.IDENTIFIER,
    TokenType.SELECTOR_IDENTIFIER,
    TokenType.SELECTOR,
    TokenType.LAMBDA_FUNCTION
]

EXPR_OP = list("+-*/%")


def is_time(token: Token):
    return (
            token.type == TokenType.IDENTIFIER
            and token.value[-1] in list("dst")
            and is_float(token.value[:-1])
    )


class StatementType(Enum):
    INLINE = "inline"
    SET_VARIABLE = "set_variable"
    DEFINE_FUNCTION = "define_function"
    RETURN = "return"
    BREAK = "break"
    CONTINUE = "continue"
    INTRODUCE_VARIABLE = "introduce_variable"
    EXECUTE_MACRO = "execute_macro"
    IF_FLOW = "if_flow"
    FOR = "for"
    WHILE = "while"
    LOOP = "loop"
    SCHEDULE = "schedule"
    IMPORT = "import"
    DEFINE_CLASS = "define_class"


class Statement(UniversalStrMixin):
    def __init__(self, type: StatementType, code: str, start: int, end: int):
        self.type = type
        self.code = code
        self.start = start
        self.end = end


class ImportStatement(Statement):
    def __init__(
            self, code: str, start: int, end: int, path: Token, as_: Token | None = None
    ):
        super().__init__(StatementType.IMPORT, code, start, end)
        self.path = path
        self.as_ = as_


class ScheduleStatement(Statement):
    def __init__(
            self, code: str, start: int, end: int, time: Token, body: List[Statement]
    ):
        super().__init__(StatementType.SCHEDULE, code, start, end)
        self.time = time
        self.body = body


class IfFlowStatement(Statement):
    def __init__(
            self,
            code: str,
            start: int,
            end: int,
            condition: List[Token],
            body: List[Statement],
            else_body: List[Statement] | None,
    ):
        super().__init__(StatementType.IF_FLOW, code, start, end)
        self.condition = condition
        self.body = body
        self.elseBody = else_body


class LoopStatement(Statement):
    def __init__(
            self, code: str, start: int, end: int, time: Token | None, body: List[Statement]
    ):
        super().__init__(StatementType.LOOP, code, start, end)
        self.time = time
        self.body = body


class IntroduceVariableStatement(Statement):
    def __init__(
            self, code: str, start: int, end: int, name: Token, var_type: List[Token]
    ):
        super().__init__(StatementType.INTRODUCE_VARIABLE, code, start, end)
        self.name = name
        self.varType = var_type


class DefineFunctionStatement(Statement):
    def __init__(
            self,
            code: str,
            start: int,
            end: int,
            name: Token,
            body: List[Statement],
            arguments: List[List[List[Token]]],
            returns: Union[List[Token], str],
    ):
        super().__init__(StatementType.DEFINE_FUNCTION, code, start, end)
        self.name = name
        self.body = body
        self.arguments = (
            arguments  # [ [ [TypeOfTheArgument...], [ NameOfTheArgument ] ] ]
        )
        self.returns = returns


class ReturnStatement(Statement):
    def __init__(
            self, code: str, start: int, end: int, keyword: Token, expr_tokens: List[Token]
    ):
        super().__init__(StatementType.RETURN, code, start, end)
        self.keyword = keyword
        self.exprTokens = expr_tokens


class BreakStatement(Statement):
    def __init__(self, code: str, start: int, end: int, keyword: Token):
        super().__init__(StatementType.BREAK, code, start, end)
        self.keyword = keyword


class ContinueStatement(Statement):
    def __init__(self, code: str, start: int, end: int, keyword: Token):
        super().__init__(StatementType.CONTINUE, code, start, end)
        self.keyword = keyword


class InlineStatement(Statement):
    def __init__(self, code: str, start: int, end: int, expr_tokens: List[Token]):
        super().__init__(StatementType.INLINE, code, start, end)
        self.exprTokens = expr_tokens


class ExecuteMacroStatement(Statement):
    def __init__(
            self, code: str, start: int, end: int, command: str, body: List[Statement]
    ):
        super().__init__(StatementType.EXECUTE_MACRO, code, start, end)
        self.command = command
        self.body = body


class DefineClassStatement(Statement):
    def __init__(
            self,
            code: str,
            start: int,
            end: int,
            name: Token,
            attributes: List[Tuple[str, List[Token]]] = None,
            methods: List[DefineFunctionStatement] = None,
    ):
        super().__init__(StatementType.DEFINE_CLASS, code, start, end)
        if attributes is None:
            attributes = []
        if methods is None:
            methods = []
        self.name = name
        self.attributes = attributes
        self.methods = methods


def read_until_curly(tokens: List[Token], start_index: int):
    length = len(tokens)
    index = start_index
    while index < length:
        t = tokens[index]
        if isinstance(t, GroupToken) and t.open.value == "{":
            return index
        index += 1
    return None


def read_until_types(tokens: List[Token], start_index: int, types: List[TokenType]):
    length = len(tokens)
    index = start_index
    while index < length:
        t = tokens[index]
        if t.type in types:
            return index
        index += 1
    return None


def read_expression(tokens: List[Token], start_index: int):
    length = len(tokens)
    index = start_index
    result = []
    if len(tokens) - 1 < index:
        return index, result

    while index < length:
        token = tokens[index]

        if token.type in {TokenType.EOF, TokenType.EOE}:
            break
        elif token.type == TokenType.EOL:
            tl = None if index == 0 else tokens[index - 1]
            if not tl or tl.value != "\\":
                break
            result.pop()
            index += 1
            continue

        result.append(token)
        index += 1

    return index, result


def chain_tokens_iterate(tokens: List[Token], index: List[int]) -> List[Token]:
    """
    Groups the first single token chain at the given index.

    Example return:
    Input: (a.d).b[c].test() + 1
    [GroupToken('(a.d)'), IdentifierToken('b'), GroupToken('[c]'), FunctionCallToken('test()')]
    """
    t0 = next_token(tokens, index)
    if t0 is None:
        return []
    branch = [t0]
    if t0.type not in {
        TokenType.GROUP,
        TokenType.IDENTIFIER,
        TokenType.BLOCK_IDENTIFIER,
        TokenType.SELECTOR_IDENTIFIER,
        TokenType.INT_LITERAL,
        TokenType.FLOAT_LITERAL,
        TokenType.STRING_LITERAL,
        TokenType.FUNCTION_CALL,
    } or (isinstance(t0, GroupToken) and t0.open.value not in {"(", "["}):
        return branch
    while True:
        tl = tokens[index[0]]
        tn = next_token(tokens, index)
        if tn is None:
            return branch
        if tn.value == ".":
            if tl.value == ".":
                index[0] -= 2
                return branch
            continue
        if (
                (
                        tn.type == TokenType.FUNCTION_CALL
                        or tn.type == TokenType.IDENTIFIER
                        or tn.type == TokenType.BLOCK_IDENTIFIER
                        or tn.type == TokenType.SELECTOR_IDENTIFIER
                        or tn.type == TokenType.INT_LITERAL
                )
                and tl.value == "."
                and tl.end == tn.start
        ):
            branch.append(tn)
            continue
        if isinstance(tn, GroupToken) and tn.open.value in {"[", "("}:
            branch.append(tn)
            continue
        index[0] -= 1
        return branch


def chain_tokens(tokens: List[Token]) -> List[List[Token]]:
    """
    Groups the indexing tokens into a single token.

    Things like:
    (a.b[c].d.f).e
    [1, 2, 3][0]
    a.b.test(5, 6, 7)[0].b

    Example return:
    Input: (a.d).b[c].test() + 1
    Output: [
        [GroupToken('(a.d)'), IdentifierToken('b'), GroupToken('[c]'), FunctionCallToken('test()')],
        [Token('+')],
        [Token('1')]
    ]

    See that GroupToken('a.d') stayed as it is because it will be dealt with in the next step
    """
    if len(tokens) == 0:
        return []
    chains = []
    index = [-1]

    while True:
        if len(tokens) > index[0] + 1 and tokens[index[0] + 1].type == TokenType.EOF:
            return chains
        chain = chain_tokens_iterate(tokens, index)
        if len(chain) == 0:
            return chains
        chains.append(chain)


def make_expr(chains: List[List[Token]]) -> List[List[Token]]:
    """
    Converts the given token chain group into an easily executable expression.
    Example:

    Input: [Token('a'), Token('+'), Token('b')] or a + b
    Output: [Token('a'), Token('b'), Token('+')] or a b +

    For more information: https://en.wikipedia.org/wiki/Shunting_yard_algorithm
    """
    new_chains = []
    for index, chain in enumerate(chains):
        if chain[0].type in ENDERS:
            continue
        new_chains.append(chain)
    chains = new_chains
    if len(chains) == 0:
        return []
    stack = []
    output = []
    for index, chain in enumerate(chains):
        if index % 2 == 0:
            if chain[0].type not in EXPR_EXPR:
                raise_syntax_error("Expected a non-operator non-symbol token", chain[0])
            output.append(chain)
            continue
        if chain[0].type != TokenType.OPERATOR or (
                chain[0].value not in EXPR_OP
                and chain[0].value not in CMP_OP
                and chain[0].value not in CMP_COMBINE_OP):
            raise_syntax_error("Expected an operator", chain[0])
        o1 = chain
        while True:
            o2 = stack[-1] if len(stack) > 0 else None
            if o2 is None or (
                    operators[o2[0].value]["p"] <= operators[o1[0].value]["p"]
                    and (
                            operators[o2[0].value]["p"] != operators[o1[0].value]["p"]
                            or operators[o1[0].value]["a"] != "left"
                    )
            ):
                break
            output.append(stack.pop())
        stack.append(chain)

    while len(stack) > 0:
        output.append(stack.pop())

    return output


def next_token(tokens: List[Token], index: List[int]):
    index[0] += 1
    if index[0] >= len(tokens):
        return None
    return tokens[index[0]]


def parse_str(code: str):
    (tokens, macros) = tokenize(code)
    return parse(tokens, macros), macros


def parse_iterate(
        statements: List[Statement],
        tokens: List[Token],
        index: List[int],
        macros: List,
        class_names: Union[List[str], None] = None,
) -> bool:
    if class_names is None:
        class_names = []
    t0 = next_token(tokens, index)
    if t0 is None:
        return False
    if t0.type == TokenType.EOF:
        return False
    if t0.type == TokenType.EOL or t0.type == TokenType.EOE:
        return True
    if t0.value == "class":
        # class <name> { <FUNCTION STATEMENTS...> }
        t1 = next_token(tokens, index)  # name of the class
        if not t1:
            raise_syntax_error("Expected a name for the class", t0)
            return False
        if t1.value in class_names:
            raise_syntax_error("Duplicate class name", t1)
            return False
        if t1 is None or t1.type != TokenType.IDENTIFIER:
            raise_syntax_error("Expected a name for the class", t0)
            return False
        t2 = next_token(tokens, index)  # class body
        if t2 is None or not isinstance(t2, GroupToken) or t2.open.value != "{":
            raise_syntax_error("Expected a class body", t0)
            return False
        attributes: List[Tuple[str, List[Token]]] = []
        methods: List[DefineFunctionStatement] = []
        class_index = [-1]
        class_tokens = t2.children

        # A class body will include these syntax:
        # <variableType> <variableName>
        # <variableType> <variableName> = <value>
        # <functionName> { <body> }
        # <functionName>: <returnType> { <body> }
        # <functionName>( <arguments> ) { <body> }
        # <functionName>( <arguments> ): <returnType> { <body> }

        class_names.append(t1.value)

        while True:
            nt0 = next_token(class_tokens, class_index)
            if nt0 is None:
                break
            if nt0.type in ENDERS:
                continue

            nt1 = next_token(class_tokens, class_index)

            if nt0.type == TokenType.IDENTIFIER and nt1 and nt1.value == "=":
                (ind, value) = read_expression(class_tokens, class_index[0] + 1)
                if len(value) == 0:
                    raise_syntax_error(
                        "Expected an expression after '='", nt1
                    )
                    return False
                class_index[0] = ind
                attributes.append((nt0.value, value))
                continue

            class_index[0] -= 1  # for t1 being useless

            st = []
            temp_tokens = [Token("fn", TokenType.KEYWORD, 0, 2)] + class_tokens[class_index[0]:]
            temp_index = [-1]
            res = parse_iterate(st, temp_tokens, temp_index, macros, class_names)
            if not res:
                raise_syntax_error("Expected a class method declaration", nt0)
                return False
            st0 = st[0]
            if not isinstance(st0, DefineFunctionStatement):
                raise_syntax_error("Expected a class method declaration", nt0)
                return False

            methods.append(st0)
            class_index[0] += temp_index[0]

        for method in methods:
            if method.type != StatementType.DEFINE_FUNCTION:
                raise_syntax_error("Expected a class function definition", method)
                return False
        statement = DefineClassStatement(
            code=t0.code,
            start=t0.start,
            end=t2.end,
            name=t1,
            attributes=attributes,
            methods=methods,
        )
        statements.append(statement)
        return True

    if t0.value == "import":
        t1 = next_token(tokens, index)
        if t1 is None or (t1.type != TokenType.IDENTIFIER and t1.type != TokenType.STRING_LITERAL):
            raise_syntax_error("Expected an identifier or a path", t0)
            return False

        _as = None

        if t1.type == TokenType.STRING_LITERAL and t1.value[:-1].endswith(".mcfunction"):
            t2 = next_token(tokens, index)
            if t2 is None or t2.value != "as":
                raise_syntax_error("Expected an 'as' keyword", t1)

            t3 = next_token(tokens, index)
            if t3 is None or t3.type != TokenType.IDENTIFIER:
                raise_syntax_error("Expected an identifier", t2)

            _as = t3

        statement = ImportStatement(
            code=t0.code, start=t0.start, end=(_as or t1).end, path=t1, as_=_as
        )
        statements.append(statement)
        return True
    if (
            t0.value == "schedule"
            and index[0] + 1 < len(tokens)
            and is_time(tokens[index[0] + 1])
    ):
        # schedule 1t { <body> }
        t1 = next_token(tokens, index)
        if t1 is None or not is_time(t1):
            raise_syntax_error("Expected a time", t0)
            return False
        body = next_token(tokens, index)
        if body is None:
            raise_syntax_error("Expected an expression", t0)
            return False
        if not isinstance(body, GroupToken) or body.open.value != "{":
            raise_syntax_error("Expected an expression inside the braces", body)

        statement = ScheduleStatement(
            code=t0.code, start=t0.start, end=body.end, time=t1, body=[]
        )

        statements.append(statement)
        return True
    if t0.value == "for":
        # for <time> (<init>; <condition>; <iterator>) { <body> }
        # for (<init>; <condition>; <iterator>) { <body> }
        t1 = next_token(tokens, index)
        if t1 is None:
            raise_syntax_error("Expected an expression", t0)
            return False
        tim = None
        if is_time(t1):
            tim = t1
            t1 = next_token(tokens, index)
        if not isinstance(t1, GroupToken) or t1.open.value != "(":
            raise_syntax_error(
                "Expected an initializer, condition, and iterator inside the parentheses",
                t1 or t0,
            )
            return False
        spl = split_tokens(t1.children, ";")
        body = next_token(tokens, index)
        if not isinstance(body, GroupToken) or body.open.value != "{":
            raise_syntax_error("Expected an expression inside the parentheses", body)
            return False
        init = parse(spl[0], macros, class_names)
        if len(init) != 1:
            raise_syntax_error("Expected an expression in the initializer", t0)
        init = init[0]

        it = parse(spl[2], macros, class_names)
        if len(it) != 1:
            raise_syntax_error("Expected an expression in the iterator", t0)
        it = it[0]

        statements.append(init)

        if_st = IfFlowStatement(
            code=t0.code,
            start=t1.start,
            end=t1.end,
            condition=spl[1],
            body=[],
            else_body=parse_str("break")[0],
        )

        loop_st_body = [if_st]
        loop_st_body.extend(parse(body.children, macros, class_names))
        loop_st_body.append(it)

        loop_st = LoopStatement(
            code=t0.code,
            start=t0.start,
            end=body.end,
            time=tim,
            body=loop_st_body
        )

        statements.append(loop_st)
        return True
    if t0.value == "do":
        # do { <body> } while <time> (<condition>)
        # do { <body> } until <time> (<condition>)
        # do { <body> } while(<condition>)
        # do { <body> } until(<condition>)
        body = next_token(tokens, index)
        if body is None:
            raise_syntax_error("Expected an expression", t0)
            return False
        if not isinstance(body, GroupToken) or body.open.value != "{":
            raise_syntax_error("Expected an expression inside the braces", body)
            return False
        t_while_until = next_token(tokens, index)
        if t_while_until is None or (t_while_until.value != "while" and t_while_until.value != "until"):
            raise_syntax_error("Expected 'while' or 'until'", t_while_until)
            return False
        tim = None
        condition = next_token(tokens, index)
        if condition is None:
            raise_syntax_error("Expected an expression", t_while_until)
            return False
        if is_time(condition):
            tim = condition
            condition = next_token(tokens, index)
        if not isinstance(condition, GroupToken) or condition.open.value != "(":
            raise_syntax_error(
                "Expected an expression inside the parentheses", condition
            )
            return False

        if_st = IfFlowStatement(
            code=condition.code,
            start=condition.start,
            end=condition.end,
            condition=condition.children,
            body=[],
            else_body=None,
        )

        if t_while_until.value == "while":
            if_st.body = []
            if_st.elseBody = parse_str("break")[0]
        else:
            if_st.body = parse_str("break")[0]
            if_st.elseBody = None

        loop_st = LoopStatement(
            code=t0.code,
            start=t0.start,
            end=condition.end,
            time=tim,
            body=parse(body.children, macros, class_names) + [if_st],
        )

        statements.append(loop_st)

        return True
    if t0.value == "while" or t0.value == "until":
        # while <time> (<condition>) { <body> }
        # until <time> (<condition>) { <body> }
        # while (<condition>) { <body> }
        # until (<condition>) { <body> }
        t1 = next_token(tokens, index)
        if t1 is None:
            raise_syntax_error("Expected an expression", t0)
            return False
        tim = None
        if is_time(t1):
            tim = t1
            t1 = next_token(tokens, index)
        if t1 is None:
            raise_syntax_error("Expected an expression", tim or t0)
            return False
        if not isinstance(t1, GroupToken) or t1.open.value != "(":
            raise_syntax_error("Expected a condition inside the parentheses", t1 or t0)
            return False
        body = next_token(tokens, index)
        if body is None:
            raise_syntax_error("Expected an expression", t1)
            return False
        if not isinstance(body, GroupToken) or body.open.value != "{":
            raise_syntax_error("Expected an expression inside the parentheses", body)
            return False

        if_st = IfFlowStatement(
            code=t0.code,
            start=t1.start,
            end=t1.end,
            condition=t1.children,
            body=[],
            else_body=None,
        )
        if t0.value == "while":
            if_st.elseBody = parse_str("break")[0]
        else:
            if_st.body = parse_str("break")[0]

        loop_st_body = [if_st]
        loop_st_body.extend(parse(body.children, macros, class_names))

        loop_st = LoopStatement(
            code=t0.code,
            start=t0.start,
            end=body.end,
            time=tim,
            body=loop_st_body
        )

        statements.append(loop_st)
        return True
    if t0.value == "loop":
        # loop <time> { <body> }
        # loop { <body> }
        body = next_token(tokens, index)
        if body is None:
            raise_syntax_error("Expected an expression", t0)
            return False
        tim = None
        if is_time(body):
            tim = body
            body = next_token(tokens, index)
        if body is None:
            raise_syntax_error("Expected an expression", tim or t0)
            return False
        if not isinstance(body, GroupToken) or body.open.value != "{":
            raise_syntax_error("Expected an expression inside the parentheses", body)
            return False
        statement = LoopStatement(
            code=t0.code,
            start=t0.start,
            end=body.end,
            time=tim,
            body=parse(body.children, macros, class_names),
        )

        statements.append(statement)
        return True
    if (
            (t0.value == "if" or t0.value == "unless" or t0.value == "else")
            and index[0] < len(tokens) - 2
            and (t0.value == "else" or tokens[index[0] + 1].type == TokenType.GROUP)
    ):
        # if ( <condition> ) { <body> } else { <body> }
        # unless ( <condition> ) { <body> } else { <body> }
        t1 = next_token(tokens, index)  # for else this is {} or statement start
        t2 = next_token(tokens, index) if t0.value != "else" else t1
        stats = []
        if t1 is None or t2 is None:
            raise_syntax_error("Expected an expression", t0)
            return False
        if t0.value != "else" and (
                not isinstance(t1, GroupToken) or t1.open.value != "("
        ):
            raise_syntax_error("Expected an expression inside the parentheses", t1)
            return False
        if t0.value == "else":
            if len(statements) == 0 or statements[-1].type != StatementType.IF_FLOW:
                raise_syntax_error(
                    "Expected an if statement before the else statement", t0
                )
            index[0] -= 1
        if isinstance(t2, GroupToken) and t2.open.value == "{":
            stats = parse(t2.children, macros, class_names)
            end_ind = t2.end
        else:
            if t0.value != "else":
                index[0] -= 1
            parse_iterate(stats, tokens, index, macros, class_names)
            if len(stats) != 1:
                raise_syntax_error("Expected a statement", t1)
            end_ind = stats[0].end
        if t0.value == "else":
            if_st = statements[-1]
            if not isinstance(if_st, IfFlowStatement):
                raise_syntax_error(
                    "Expected an if statement before the else statement", t0
                )
                return False
            if_st.elseBody = stats
            index[0] += 1
            return True

        if not isinstance(t1, GroupToken):
            return False  # for the linter

        statement = IfFlowStatement(
            code=t0.code,
            start=t0.start,
            end=end_ind,
            condition=t1.children,
            body=stats,
            else_body=None,
        )
        statements.append(statement)
        return True

    if t0.value == "define":
        # define <type> <name>
        si = index[0]
        expr_ind = read_until_types(tokens, index[0], ENDERS)
        if expr_ind is None:
            raise_syntax_error("Unfinished define statement", t0)
        expr = tokens[si + 1:expr_ind]

        if len(expr) < 2:
            raise_syntax_error("Unfinished define statement", t0)
            return False
        if not cpl_def_from_tokens(class_names, expr[:-1]):
            raise_syntax_error("Invalid type for the define statement", t0)
            return False
        name = expr[-1]
        if (
                name.type != TokenType.IDENTIFIER
                and name.type != TokenType.SELECTOR_IDENTIFIER
        ):
            raise_syntax_error(
                "Expected a valid variable name for the define statement", name
            )
            return False
        statement = IntroduceVariableStatement(
            code=t0.code, start=t0.start, end=name.end, name=name, var_type=expr[:-1]
        )
        statements.append(statement)
        index[0] = expr_ind
        return True

    if t0.value == "fn":
        # fn <name>( <arguments> ) { <body> }
        # fn <name> { <body> }
        # fn <name>( <arguments> ): <returnType> { <body> }
        # fn <name>: <returnType> { <body> }
        t1 = next_token(tokens, index)  # function name and arguments
        t2 = next_token(tokens, index)  # function body or colon
        return_type = "auto"
        if t1 is None or (
                t1.type != TokenType.FUNCTION_CALL and t1.type != TokenType.IDENTIFIER
        ):
            raise_syntax_error(
                "Expected a function name for the function definition",
                t0,
            )
            return False
        if isinstance(t1, GroupToken) and t1.func and t1.func.value == "tick":
            raise_syntax_error(
                "Tick function does not support arguments, remove the parentheses",
                t1,
            )
            return False
        if t2 is None:
            raise_syntax_error("Expected a function body for the function", t1)
            return False
        if t2.value == ":":
            ind = read_until_curly(tokens, index[0])
            if ind is None:
                raise_syntax_error("Expected a function body for the function", t1)
                return False
            t3 = next_token(tokens, index)
            if t3 and t3.value in {"void", "auto"}:
                return_type = t3.value
                t2 = next_token(tokens, index)
            else:
                return_type = tokens[index[0]: ind]
                if not cpl_def_from_tokens(class_names, return_type):
                    raise_syntax_error(
                        "Expected a valid return type for the function", t3
                    )
                    return False
                index[0] = ind - 1
                t2 = next_token(tokens, index)

        if not isinstance(t2, GroupToken) or t2.open.value != "{":
            raise_syntax_error("Expected a function body", t2)
            return False

        statement = DefineFunctionStatement(
            code=t1.code,
            start=t0.start,
            end=t2.end,
            name=t1.func if isinstance(t1, GroupToken) and t1.func else t1,
            body=parse(t2.children, macros, class_names),
            arguments=[],
            returns=return_type,
        )
        if isinstance(t1, GroupToken) and t1.func:
            spl = split_tokens(t1.children)
            for s in spl:
                o_chain = chain_tokens(s)
                chain = o_chain
                if len(chain) == 3 and chain[0][0].value == "$":
                    chain = chain[1:]
                if len(chain) != 2:
                    raise_syntax_error("Expected a valid function argument", s[0])
                c_type = chain[0]
                type_def = cpl_def_from_tokens(class_names, c_type)
                if not type_def:
                    raise_syntax_error(
                        "Expected a valid type for the argument", c_type[0]
                    )
                statement.arguments.append(o_chain)

        statements.append(statement)
        return True

    if t0.type == TokenType.KEYWORD and t0.value == "return":
        # return <expression>
        expr_tokens = []
        ind = index[0] + 1
        if ind <= len(tokens) and tokens[ind].type not in ENDERS:
            (ind, expr_tokens) = read_expression(tokens, ind)
            if len(expr_tokens) == 0:
                raise_syntax_error(
                    "Expected an expression after the return keyword", t0
                )
        statement = ReturnStatement(
            code=t0.code,
            start=t0.start,
            end=t0.end if len(expr_tokens) == 0 else expr_tokens[-1].end,
            keyword=t0,
            expr_tokens=expr_tokens,
        )
        statements.append(statement)
        index[0] = ind
        return True

    if t0.type == TokenType.KEYWORD and (t0.value == "break" or t0.value == "continue"):
        # break
        # continue
        statement = (BreakStatement if t0.value == "break" else ContinueStatement)(
            code=t0.code, start=t0.start, end=t0.end, keyword=t0
        )
        statements.append(statement)
        return True

    if t0.value in EXECUTE_MACROS:
        # as @a at @s ... { <body> }
        got_tokens = [t0]
        body_g: GroupToken
        while True:
            t = next_token(tokens, index)
            if t is None:
                raise_syntax_error("Unexpected end of file", got_tokens[-1])
                raise SyntaxError("")
            if isinstance(t, GroupToken) and t.open.value == "{":
                body_g = t
                break
            got_tokens.append(t)

        statement = ExecuteMacroStatement(
            code=t0.code,
            start=t0.start,
            end=got_tokens[-1].end,
            command=" ".join(t.value for t in got_tokens),
            body=parse(body_g.children, macros, class_names),
        )
        statements.append(statement)
        return True

    (ind, expr_tokens) = read_expression(tokens, index[0])
    if ind is None:
        raise_syntax_error("Unexpected token", t0)
    statement = InlineStatement(
        code=t0.code, start=t0.start, end=expr_tokens[-1].end, expr_tokens=expr_tokens
    )
    statements.append(statement)
    index[0] = ind
    return True


def parse(
        tokens: List[Token], macros: List, class_names: List[str] = None
):
    if class_names is None:
        class_names = []
    statements: List[Statement] = []
    index = [-1]

    while parse_iterate(statements, tokens, index, macros, class_names):
        pass
    return statements
