from ast import If
from enum import Enum
from typing import List

from tokenizer import (
    GroupToken,
    Token,
    TokenType,
    SET_OP,
    INC_OP,
    is_float,
    split_tokens,
    tokenize,
)
from error import raise_syntax_error, show_err
from utils import FunctionArgument, UniversalStrMixin

ENDERS = {
    TokenType.EOL,
    TokenType.EOE,
    TokenType.EOF,
}

VARIABLE_TYPES = ["int", "float"]
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
    "equence",
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
}

EXPR_EXPR = [
    TokenType.FUNCTION_CALL,
    TokenType.GROUP,
    TokenType.INT_LITERAL,
    TokenType.FLOAT_LITERAL,
    TokenType.IDENTIFIER,
    TokenType.SELECTOR_IDENTIFIER,
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


class Statement(UniversalStrMixin):
    def __init__(self, type: StatementType, start: int, end: int):
        self.type = type
        self.start = start
        self.end = end


class ImportStatement(Statement):
    def __init__(self, start: int, end: int, path: Token, _as: Token | None = None):
        super().__init__(StatementType.IMPORT, start, end)
        self.path = path
        self._as = _as


class ScheduleStatement(Statement):
    def __init__(self, start: int, end: int, time: Token, body: List[Statement]):
        super().__init__(StatementType.SCHEDULE, start, end)
        self.time = time
        self.body = body


class IfFlowStatement(Statement):
    def __init__(
        self,
        start: int,
        end: int,
        condition: List[Token],
        body: List[Statement],
        elseBody: List[Statement] | None,
    ):
        super().__init__(StatementType.IF_FLOW, start, end)
        self.condition = condition
        self.body = body
        self.elseBody = elseBody


class LoopStatement(Statement):
    def __init__(self, start: int, end: int, time: Token | None, body: List[Statement]):
        super().__init__(StatementType.LOOP, start, end)
        self.time = time
        self.body = body


class IntroduceVariableStatement(Statement):
    def __init__(self, start: int, end: int, name: Token, varType: Token):
        super().__init__(StatementType.INTRODUCE_VARIABLE, start, end)
        self.name = name
        self.varType = varType


class DefineFunctionStatement(Statement):
    def __init__(
        self,
        start: int,
        end: int,
        name: Token,
        body: List[Statement],
        arguments: List[FunctionArgument],
        returns: Token,
    ):
        super().__init__(StatementType.DEFINE_FUNCTION, start, end)
        self.name = name
        self.body = body
        self.arguments = arguments
        self.returns = returns


class ReturnStatement(Statement):
    def __init__(self, start: int, end: int, keyword: Token, expr: List[Token]):
        super().__init__(StatementType.RETURN, start, end)
        self.keyword = keyword
        self.expr = expr


class BreakStatement(Statement):
    def __init__(self, start: int, end: int, keyword: Token):
        super().__init__(StatementType.BREAK, start, end)
        self.keyword = keyword


class ContinueStatement(Statement):
    def __init__(self, start: int, end: int, keyword: Token):
        super().__init__(StatementType.CONTINUE, start, end)
        self.keyword = keyword


class InlineStatement(Statement):
    def __init__(self, start: int, end: int, expr: List[Token]):
        super().__init__(StatementType.INLINE, start, end)
        self.expr = expr


class ExecuteMacroStatement(Statement):
    def __init__(self, start: int, end: int, command: str, body: List[Statement]):
        super().__init__(StatementType.EXECUTE_MACRO, start, end)
        self.command = command
        self.body = body


def read_until_curly(tokens: List[Token], start_index: int):
    length = len(tokens)
    index = start_index
    while index < length:
        t = tokens[index]
        if isinstance(t, GroupToken) and t.open.value == "{":
            return index
        index += 1
    return None


def read_expression(tokens: List[Token], start_index: int):
    length = len(tokens)
    index = start_index
    operator_count = 0
    result = []

    while index < length:
        operator_count += 1
        token = tokens[index]

        if token.type in {TokenType.EOF, TokenType.EOE}:
            break
        elif token.type == TokenType.EOL:
            if operator_count % 2 == 0 and (
                index == 0 or tokens[index - 1].value != "\\"
            ):
                break

        result.append(token)
        index += 1

    return index, result


def make_expr(tokens: List[Token]):
    if len(tokens) == 0:
        return []
    if len(tokens) == 2 and tokens[1].value in INC_OP:
        return tokens
    t0 = tokens[0]
    if t0.value in COMMANDS:
        return tokens
    t1 = tokens[1] if len(tokens) > 1 else None
    if (
        (t0.type == TokenType.IDENTIFIER or t0.type == TokenType.SELECTOR_IDENTIFIER)
        and t1 != None
        and t1.type == TokenType.OPERATOR
        and t1.value in SET_OP
    ):
        (_, expr) = read_expression(tokens, 2)
        if len(expr) == 0:
            raise_syntax_error("Expected an expression for the set operation", t1)
        return [t1, t0] + expr  # [=, var_name, ...expression]
    stack = []
    output = []
    for index, token in enumerate(tokens):
        if index % 2 == 0:
            if token.type not in EXPR_EXPR:
                raise_syntax_error("Expected a non-operator non-symbol token", token)
            output.append(token)
            continue
        if token.type != TokenType.OPERATOR or token.value not in EXPR_OP:
            raise_syntax_error("Expected an operator", token)
        o1 = token
        o2 = None
        while True:
            o2 = stack[-1] if len(stack) > 0 else None
            if o2 == None or (
                operators[o2.value]["p"] <= operators[o1.value]["p"]
                and (
                    operators[o2.value]["p"] != operators[o1.value]["p"]
                    or operators[o1.value]["a"] != "left"
                )
            ):
                break
            output.append(stack.pop())
        stack.append(o1)

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
    return (parse(tokens, macros), macros)


def parse_iterate(
    statements: List[Statement], tokens: List[Token], index: List[int], macros: List
):
    t0 = next_token(tokens, index)
    if t0 == None:
        return False
    if t0.type == TokenType.EOF:
        return False
    if t0.type == TokenType.EOL or t0.type == TokenType.EOE:
        return True
    if t0.value == "import":
        t1 = next_token(tokens, index)
        if t1 == None or (
            t1.type != TokenType.IDENTIFIER and t1.type != TokenType.STRING_LITERAL
        ):
            raise_syntax_error("Expected an identifier or a path", t0)
            return False

        _as = None

        if t1.type == TokenType.STRING_LITERAL and t1.value[:-1].endswith(
            ".mcfunction"
        ):
            t2 = next_token(tokens, index)
            if t2 == None or t2.value != "as":
                raise_syntax_error("Expected an 'as' keyword", t1)

            t3 = next_token(tokens, index)
            if t3 == None or t3.type != TokenType.IDENTIFIER:
                raise_syntax_error("Expected an identifier", t2)

            _as = t3

        statement = ImportStatement(
            start=t0.start, end=(_as or t1).end, path=t1, _as=_as
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
        if t1 == None or not is_time(t1):
            raise_syntax_error("Expected a time", t0)
            return False
        body = next_token(tokens, index)
        if body == None:
            raise_syntax_error("Expected an expression", t0)
            return False
        if not isinstance(body, GroupToken) or body.open.value != "{":
            raise_syntax_error("Expected an expression inside the braces", body)

        statement = ScheduleStatement(start=t0.start, end=body.end, time=t1, body=[])

        statements.append(statement)
        return True
    if t0.value == "for":
        # for <time> (<init>; <condition>; <iterator>) { <body> }
        # for (<init>; <condition>; <iterator>) { <body> }
        t1 = next_token(tokens, index)
        if t1 == None:
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
        init = parse(spl[0], macros)
        if len(init) != 1:
            raise_syntax_error("Expected an expression in the initializer", t0)
        init = init[0]

        iter = parse(spl[2], macros)
        if len(iter) != 1:
            raise_syntax_error("Expected an expression in the iterator", t0)
        iter = iter[0]

        statements.append(init)

        ifSt = IfFlowStatement(
            start=t1.start,
            end=t1.end,
            condition=spl[1],
            body=[],
            elseBody=parse_str("break")[0],
        )

        loopSt = LoopStatement(
            start=t0.start,
            end=body.end,
            time=tim,
            body=[ifSt] + parse(body.children, macros) + [iter],
        )

        statements.append(loopSt)
        return True
    if t0.value == "do":
        # do { <body> } while <time> (<condition>)
        # do { <body> } until <time> (<condition>)
        # do { <body> } while(<condition>)
        # do { <body> } until(<condition>)
        body = next_token(tokens, index)
        if body == None:
            raise_syntax_error("Expected an expression", t0)
            return False
        if not isinstance(body, GroupToken) or body.open.value != "{":
            raise_syntax_error("Expected an expression inside the braces", body)
            return False
        tW = next_token(tokens, index)
        if tW == None or (tW.value != "while" and tW.value != "until"):
            raise_syntax_error("Expected 'while' or 'until'", tW)
            return False
        tim = None
        condition = next_token(tokens, index)
        if condition == None:
            raise_syntax_error("Expected an expression", tW)
            return False
        if is_time(condition):
            tim = condition
            condition = next_token(tokens, index)
        if not isinstance(condition, GroupToken) or condition.open.value != "(":
            raise_syntax_error(
                "Expected an expression inside the parentheses", condition
            )
            return False

        ifSt = IfFlowStatement(
            start=condition.start,
            end=condition.end,
            condition=condition.children,
            body=[],
            elseBody=None,
        )

        if tW.value == "while":
            ifSt.body = []
            ifSt.elseBody = parse_str("break")[0]
        else:
            ifSt.body = parse_str("break")[0]
            ifSt.elseBody = None

        loopSt = LoopStatement(
            start=t0.start,
            end=condition.end,
            time=tim,
            body=parse(body.children, macros) + [ifSt],
        )

        statements.append(loopSt)

        return True
    if t0.value == "while" or t0.value == "until":
        # while <time> (<condition>) { <body> }
        # until <time> (<condition>) { <body> }
        # while (<condition>) { <body> }
        # until (<condition>) { <body> }
        t1 = next_token(tokens, index)
        if t1 == None:
            raise_syntax_error("Expected an expression", t0)
            return False
        tim = None
        if is_time(t1):
            tim = t1
            t1 = next_token(tokens, index)
        if t1 == None:
            raise_syntax_error("Expected an expression", tim or t0)
            return False
        if not isinstance(t1, GroupToken) or t1.open.value != "(":
            raise_syntax_error("Expected a condition inside the parentheses", t1 or t0)
            return False
        body = next_token(tokens, index)
        if body == None:
            raise_syntax_error("Expected an expression", t1)
            return False
        if not isinstance(body, GroupToken) or body.open.value != "{":
            raise_syntax_error("Expected an expression inside the parentheses", body)
            return False

        ifSt = IfFlowStatement(
            start=t1.start, end=t1.end, condition=t1.children, body=[], elseBody=None
        )
        if t0.value == "while":
            ifSt.elseBody = parse_str("break")[0]
        else:
            ifSt.body = parse_str("break")[0]

        loopSt = LoopStatement(
            start=t0.start,
            end=body.end,
            time=tim,
            body=[ifSt] + parse(body.children, macros),
        )

        statements.append(loopSt)
        return True
    if t0.value == "loop":
        # loop <time> { <body> }
        # loop { <body> }
        body = next_token(tokens, index)
        if body == None:
            raise_syntax_error("Expected an expression", t0)
            return False
        tim = None
        if is_time(body):
            tim = body
            body = next_token(tokens, index)
        if body == None:
            raise_syntax_error("Expected an expression", tim or t0)
            return False
        if not isinstance(body, GroupToken) or body.open.value != "{":
            raise_syntax_error("Expected an expression inside the parentheses", body)
            return False
        statement = LoopStatement(
            start=t0.start, end=body.end, time=tim, body=parse(body.children, macros)
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
        end_ind = 0
        if t1 == None or t2 == None:
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
        #print("----------------------------------")
        if isinstance(t2, GroupToken) and t2.open.value == "{":
            #show_err("1", t0.code, t0.start, t0.end)
            stats = parse(t2.children, macros)
            end_ind = t2.end
        else:
            if t0.value != "else":
                index[0] -= 1
            parse_iterate(stats, tokens, index, macros)
            #print(tokens[index[0] + 1], stats[0])
            #show_err("2", t0.code, t0.start, t0.end)
            if len(stats) != 1:
                raise_syntax_error("Expected a statement", t1)
            end_ind = stats[0].end
        #print("end", t0.value)
        #print("----------------------------------")
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
            start=t0.start,
            end=end_ind,
            condition=t1.children,
            body=stats,
            elseBody=None,
        )
        statements.append(statement)
        return True

    if t0.value == "define":
        # define <type> <name>
        t1 = next_token(tokens, index)
        t2 = next_token(tokens, index)
        t3 = next_token(tokens, index)
        if t1 == None or t2 == None or t3 == None:
            raise_syntax_error("Unfinished define statement", t0)
            return False
        if t1.value not in VARIABLE_TYPES:
            raise_syntax_error(
                "Expected 'int', 'float' for the variable definition",
                t1,
            )
            return False
        if t2.type != TokenType.IDENTIFIER and t2.type != TokenType.SELECTOR_IDENTIFIER:
            raise_syntax_error(
                "Expected a valid variable name for the define statement", t2
            )
            return False
        if t3.type not in ENDERS:
            raise_syntax_error(
                "Expected an expression terminator after the define statement",
                t3,
            )
            return False
        statement = IntroduceVariableStatement(
            start=t0.start, end=t2.end, name=t2, varType=t1
        )
        statements.append(statement)
        return True

    if t0.value == "function":
        # function <name>( <arguments> ): <type> { <body> }
        t1 = next_token(tokens, index)
        t2 = next_token(tokens, index)
        t3 = next_token(tokens, index)
        t4 = next_token(tokens, index)
        if t1 == None or (
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
        if t2 == None or t3 == None:
            raise_syntax_error("Expected at least two expressions", t1)
            return False
        is_tick = t1.type == TokenType.IDENTIFIER and t1.value == "tick"
        if is_tick:
            t4 = t2
            index[0] -= 2
            pass
        elif t2.value != ":" or (t3.value not in VARIABLE_TYPES and t3.value != "void"):
            raise_syntax_error("Expected a valid return type for the function", t1)
            return False
        if t4 == None or not isinstance(t4, GroupToken) or t4.open.value[0] != "{":
            raise_syntax_error(
                "Expected curly brackets for the function definition", t1
            )
            return False
        statement = DefineFunctionStatement(
            start=t0.start,
            end=t2.end if is_tick else t4.end,
            name=t1.func if isinstance(t1, GroupToken) and t1.func else t1,
            body=parse(t4.children, macros),
            arguments=[],
            returns=Token("void", TokenType.KEYWORD, 0, 4) if is_tick else t3,
        )
        arg_names = []
        if isinstance(t1, GroupToken) and t1.func:
            for arg in split_tokens(t1.children):
                if (
                    len(arg) != 2
                    or arg[0].value not in VARIABLE_TYPES
                    or arg[1].type != TokenType.IDENTIFIER
                ):
                    raise_syntax_error("Invalid argument for a function", arg[0])
                arg_type = arg[0].value
                arg_name = arg[1].value
                if arg_name in arg_names:
                    raise_syntax_error("Argument name is already used", arg)
                statement.arguments.append(FunctionArgument(arg_type, arg_name))
                arg_names.append(arg_name)

        statements.append(statement)
        return True

    if t0.type == TokenType.KEYWORD and t0.value == "return":
        # return <expression>
        expr = []
        ind = index[0] + 1
        if ind <= len(tokens) and tokens[ind].type not in ENDERS:
            (ind, expr) = read_expression(tokens, ind)
            if len(expr) == 0:
                raise_syntax_error(
                    "Expected an expression after the return keyword", t0
                )
        statement = ReturnStatement(
            start=t0.start,
            end=t0.end if len(expr) == 0 else expr[-1].end,
            keyword=t0,
            expr=expr,
        )
        statements.append(statement)
        index[0] = ind
        return True

    if t0.type == TokenType.KEYWORD and (t0.value == "break" or t0.value == "continue"):
        # break
        # continue
        statement = (BreakStatement if t0.value == "break" else ContinueStatement)(
            start=t0.start, end=t0.end, keyword=t0
        )
        statements.append(statement)
        return True

    if t0.value in EXECUTE_MACROS:
        # as @a at @s ... { <body> }
        gotTokens = [t0]
        bodyG: GroupToken
        while True:
            t = next_token(tokens, index)
            if t == None:
                raise_syntax_error("Unexpected end of file", gotTokens[-1])
                break
            if isinstance(t, GroupToken) and t.open.value == "{":
                bodyG = t
                break
            gotTokens.append(t)

        statement = ExecuteMacroStatement(
            start=t0.start,
            end=gotTokens[-1].end,
            command=" ".join(t.value for t in gotTokens),
            body=parse(bodyG.children, macros),
        )
        statements.append(statement)
        return True

    (ind, expr) = read_expression(tokens, index[0])
    if ind == None:
        raise_syntax_error("Unexpected token", t0)
    statement = InlineStatement(start=t0.start, end=expr[-1].end, expr=expr)
    statements.append(statement)
    index[0] = ind
    return True


def parse(tokens: List[Token], macros: List):
    statements: List[Statement] = []
    index = [-1]

    while parse_iterate(statements, tokens, index, macros):
        pass
    return statements
