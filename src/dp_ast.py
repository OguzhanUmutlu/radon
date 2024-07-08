from typing import List
from tokenizer import Token, TokenType, Tokenizer, SET_OP, INC_OP, is_float
from error import raise_syntax_error
from utils import UniversalStrMixin

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


class StatementType:
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


class Statement(UniversalStrMixin):
    def __init__(self, type: StatementType):
        self.type = type


class AST:
    def read_until_curly(tokens: List[Token], start_index: int):
        length = len(tokens)
        index = start_index
        while index < length:
            if (
                tokens[index].type == TokenType.GROUP
                and tokens[index].open.value == "{"
            ):
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
            (
                t0.type == TokenType.IDENTIFIER
                or t0.type == TokenType.SELECTOR_IDENTIFIER
            )
            and t1 != None
            and t1.type == TokenType.OPERATOR
            and t1.value in SET_OP
        ):
            (_, expr) = AST.read_expression(tokens, 2)
            if len(expr) == 0:
                raise_syntax_error("Expected an expression for the set operation", t1)
            return [t1, t0, expr]  # [=, var_name, [...expression]]
        stack = []
        output = []
        for index, token in enumerate(tokens):
            if index % 2 == 0:
                if token.type not in EXPR_EXPR:
                    raise_syntax_error(
                        "Expected a non-operator non-symbol token", token
                    )
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
        (tokens, macros) = Tokenizer.tokenize(code)
        return (AST.parse(tokens, macros), macros)

    def parse_iterate(
        statements: List[Statement], tokens: List[Token], index: List[int], macros: List
    ):
        t0 = AST.next_token(tokens, index)
        if t0 == None:
            return False
        if t0.type == TokenType.EOF:
            return False
        if t0.type == TokenType.EOL or t0.type == TokenType.EOE:
            return True
        if (
            t0.value == "schedule"
            and index[0] + 1 < len(tokens)
            and is_time(tokens[index[0] + 1])
        ):
            # schedule 1t { <body> }
            t1 = AST.next_token(tokens, index)
            body = AST.next_token(tokens, index)
            if body == None:
                raise_syntax_error("Expected an expression", t0)
            if body.type != TokenType.GROUP or body.open.value != "{":
                raise_syntax_error("Expected an expression inside the braces", body)

            statement = Statement(StatementType.SCHEDULE)
            statement.time = t1
            statement.body = AST.parse(body.children, macros)
            statement.token = Token(t0.code, TokenType.POINTER, t0.start, body.end)

            statements.append(statement)
            return True
        if t0.value == "for":
            # for <time> (<init>; <condition>; <iterator>) { <body> }
            # for (<init>; <condition>; <iterator>) { <body> }
            t1 = AST.next_token(tokens, index)
            if t1 == None:
                raise_syntax_error("Expected an expression", t0)
            tim = None
            if is_time(t1):
                tim = t1
                t1 = AST.next_token(tokens, index)
            if t1.type != TokenType.GROUP or t1.open.value != "(":
                raise_syntax_error(
                    "Expected an initializer, condition, and iterator inside the parentheses",
                    t1 or t0,
                )
            spl = Tokenizer.split_tokens(t1.children, ";")
            body = AST.next_token(tokens, index)
            if body.type != TokenType.GROUP or body.open.value != "{":
                raise_syntax_error(
                    "Expected an expression inside the parentheses", body
                )
            init = AST.parse(spl[0], macros)
            if len(init) != 1:
                raise_syntax_error("Expected an expression in the initializer", t0)
            init = init[0]

            iter = AST.parse(spl[2], macros)
            if len(iter) != 1:
                raise_syntax_error("Expected an expression in the iterator", t0)
            iter = iter[0]

            statements.append(init)

            ifSt = Statement(StatementType.IF_FLOW)
            ifSt.condition = spl[1]
            ifSt.body = []
            ifSt.elseBody = AST.parse_str("break")[0]
            ifSt.token = Token(t1.code, TokenType.POINTER, t1.start, t1.end)

            loopSt = Statement(StatementType.LOOP)
            loopSt.time = tim
            loopSt.body = [ifSt] + AST.parse(body.children, macros) + [iter]
            loopSt.token = Token(t0.code, TokenType.POINTER, t0.start, body.end)

            statements.append(loopSt)
            return True
        if t0.value == "do":
            # do { <body> } while <time> (<condition>)
            # do { <body> } until <time> (<condition>)
            # do { <body> } while(<condition>)
            # do { <body> } until(<condition>)
            body = AST.next_token(tokens, index)
            if body == None:
                raise_syntax_error("Expected an expression", t0)
            if body.type != TokenType.GROUP or body.open.value != "{":
                raise_syntax_error("Expected an expression inside the braces", body)
            tW = AST.next_token(tokens, index)
            if tW == None or (tW.value != "while" and tW.value != "until"):
                raise_syntax_error("Expected 'while' or 'until'", tW)
            tim = None
            condition = AST.next_token(tokens, index)
            if is_time(condition):
                tim = condition
                condition = AST.next_token(tokens, index)
            if condition.type != TokenType.GROUP or condition.open.value != "(":
                raise_syntax_error(
                    "Expected an expression inside the parentheses", condition
                )

            ifSt = Statement(StatementType.IF_FLOW)
            ifSt.condition = condition.children
            if tW.value == "while":
                ifSt.body = []
                ifSt.elseBody = AST.parse_str("break")[0]
            else:
                ifSt.body = AST.parse_str("break")[0]
                ifSt.elseBody = None
            ifSt.token = Token(
                condition.code, TokenType.POINTER, condition.start, condition.end
            )

            loopSt = Statement(StatementType.LOOP)
            loopSt.time = tim
            loopSt.body = AST.parse(body.children, macros) + [ifSt]
            loopSt.token = Token(t0.code, TokenType.POINTER, t0.start, condition.end)

            statements.append(loopSt)

            return True
        if t0.value == "while" or t0.value == "until":
            # while <time> (<condition>) { <body> }
            # until <time> (<condition>) { <body> }
            # while (<condition>) { <body> }
            # until (<condition>) { <body> }
            t1 = AST.next_token(tokens, index)
            if t1 == None:
                raise_syntax_error("Expected an expression", t0)
            tim = None
            if is_time(t1):
                tim = t1
                t1 = AST.next_token(tokens, index)
            if t1 == None:
                raise_syntax_error("Expected an expression", tim or t0)
            if t1.type != TokenType.GROUP or t1.open.value != "(":
                raise_syntax_error(
                    "Expected a condition inside the parentheses", t1 or t0
                )
            body = AST.next_token(tokens, index)
            if body == None:
                raise_syntax_error("Expected an expression", t1)
            if body.type != TokenType.GROUP or body.open.value != "{":
                raise_syntax_error(
                    "Expected an expression inside the parentheses", body
                )

            ifSt = Statement(StatementType.IF_FLOW)
            ifSt.condition = t1.children
            if t0.value == "while":
                ifSt.body = []
                ifSt.elseBody = AST.parse_str("break")[0]
            else:
                ifSt.body = AST.parse_str("break")[0]
                ifSt.elseBody = None
            ifSt.token = Token(t1.code, TokenType.POINTER, t1.start, t1.end)

            loopSt = Statement(StatementType.LOOP)
            loopSt.time = tim
            loopSt.body = [ifSt] + AST.parse(body.children, macros)
            loopSt.token = Token(t0.code, TokenType.POINTER, t0.start, body.end)

            statements.append(loopSt)
            return True
        if t0.value == "loop":
            # loop <time> { <body> }
            # loop { <body> }
            body = AST.next_token(tokens, index)
            if body == None:
                raise_syntax_error("Expected an expression", t0)
            tim = None
            if is_time(body):
                tim = body
                body = AST.next_token(tokens, index)
            if body == None:
                raise_syntax_error("Expected an expression", tim or t0)
            if body.type != TokenType.GROUP or body.open.value != "{":
                raise_syntax_error(
                    "Expected an expression inside the parentheses", body
                )
            statement = Statement(StatementType.LOOP)
            statement.time = tim
            statement.token = Token(t0.code, TokenType.POINTER, t0.start, body.end)
            statement.body = AST.parse(body.children, macros)
            statements.append(statement)
            return True
        if (
            (t0.value == "if" or t0.value == "unless" or t0.value == "else")
            and index[0] < len(tokens) - 2
            and (t0.value == "else" or tokens[index[0] + 1].type == TokenType.GROUP)
        ):
            # if ( <condition> ) { <body> } else { <body> }
            # unless ( <condition> ) { <body> } else { <body> }
            t1 = AST.next_token(tokens, index)  # for else this is {} or statement start
            t2 = AST.next_token(tokens, index) if t0.value != "else" else t1
            if t1 == None or t2 == None:
                raise_syntax_error("Expected an expression", t0)
            if t0.value != "else" and t1.open.value != "(":
                raise_syntax_error("Expected an expression inside the parentheses", t1)
            stats = []
            end_ind = 0
            if t0.value == "else":
                if len(statements) == 0 or statements[-1].type != StatementType.IF_FLOW:
                    raise_syntax_error(
                        "Expected an if statement before the else statement", t0
                    )
                t1 = t0
                index[0] -= 1
            if t2.type == TokenType.GROUP and t2.open.value == "{":
                stats = AST.parse(t2.children, macros)
                end_ind = t2.end
            else:
                if t0.value == "if":
                    index[0] -= 1
                AST.parse_iterate(stats, tokens, index, macros)
                if len(stats) != 1:
                    raise_syntax_error("Expected a statement", t1)
                end_ind = stats[0].token.end
            if t0.value == "else":
                if_st = statements[-1]
                if_st.elseBody = stats
                index[0] += 1
                return True

            statement = Statement(StatementType.IF_FLOW)
            statement.condition = t1.children
            statement.body = stats
            statement.elseBody = None
            statement.token = Token(t0.code, TokenType.POINTER, t0.start, end_ind)
            statements.append(statement)
            return True

        if t0.value == "define":
            # define <type> <name>
            t1 = AST.next_token(tokens, index)
            t2 = AST.next_token(tokens, index)
            t3 = AST.next_token(tokens, index)
            if t1 == None or t2 == None or t3 == None:
                raise_syntax_error("Unfinished define statement", t0)
            if t1.value not in VARIABLE_TYPES:
                raise_syntax_error(
                    "Expected 'int', 'float' for the variable definition",
                    t1,
                )
            if (
                t2.type != TokenType.IDENTIFIER
                and t2.type != TokenType.SELECTOR_IDENTIFIER
            ):
                raise_syntax_error(
                    "Expected a valid variable name for the define statement", t2
                )
            if t3.type not in ENDERS:
                raise_syntax_error(
                    "Expected an expression terminator after the define statement",
                    t3,
                )
            statement = Statement(StatementType.INTRODUCE_VARIABLE)
            statement.name = t2
            statement.varType = t1
            statement.token = Token(t0.code, TokenType.POINTER, t0.start, t2.end)
            statements.append(statement)
            return True

        if t0.value == "function":
            # function <name>( <arguments> ): <type> { <body> }
            t1 = AST.next_token(tokens, index)
            t2 = AST.next_token(tokens, index)
            t3 = AST.next_token(tokens, index)
            t4 = AST.next_token(tokens, index)
            if t1 == None or (
                t1.type != TokenType.FUNCTION_CALL and t1.type != TokenType.IDENTIFIER
            ):
                raise_syntax_error(
                    "Expected a function name for the function definition",
                    t0,
                )
            if t1.type == TokenType.FUNCTION_CALL and t1.func.value == "tick":
                raise_syntax_error(
                    "Tick function does not support arguments, remove the parentheses",
                    t1,
                )
            is_tick = t1.type == TokenType.IDENTIFIER and t1.value == "tick"
            if is_tick:
                t4 = t2
                index[0] -= 2
                pass
            elif (
                t2 == None
                or t2.value != ":"
                or t3 == None
                or (t3.value not in VARIABLE_TYPES and t3.value != "void")
            ):
                raise_syntax_error("Expected a valid return type for the function", t1)
            if t4 == None or t4.type != TokenType.GROUP or t4.open.value[0] != "{":
                raise_syntax_error(
                    "Expected curly brackets for the function definition", t1
                )
            statement = Statement(StatementType.DEFINE_FUNCTION)
            statement.name = t1 if t1.type == TokenType.IDENTIFIER else t1.func
            statement.body = AST.parse(t4.children, macros)
            statement.arguments = []
            statement.token = Token(
                t0.code, TokenType.POINTER, t0.start, t2.end if is_tick else t4.end
            )
            statement.returns = (
                Token("void", TokenType.KEYWORD, 0, 4) if is_tick else t3
            )
            arg_names = []
            if t1.type == TokenType.FUNCTION_CALL:
                for arg in Tokenizer.split_tokens(t1.children):
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
                    statement.arguments.append([arg_type, arg_name, 0])
                    arg_names.append(arg_name)

            statements.append(statement)
            return True

        if t0.type == TokenType.KEYWORD and t0.value == "return":
            # return <expression>
            expr = []
            ind = index[0] + 1
            if ind <= len(tokens) and tokens[ind].type not in ENDERS:
                (ind, expr) = AST.read_expression(tokens, ind)
                if len(expr) == 0:
                    raise_syntax_error(
                        "Expected an expression after the return keyword", t0
                    )
            statement = Statement(StatementType.RETURN)
            statement.keyword = t0
            statement.expr = expr
            statement.token = Token(
                t0.code,
                TokenType.POINTER,
                t0.start,
                t0.end if len(expr) == 0 else expr[-1].end,
            )
            statements.append(statement)
            index[0] = ind
            return True

        if t0.type == TokenType.KEYWORD and (
            t0.value == "break" or t0.value == "continue"
        ):
            # break
            # continue
            statement = Statement(
                StatementType.BREAK if t0.value == "break" else StatementType.CONTINUE
            )
            statement.keyword = t0
            statement.token = Token(t0.code, TokenType.POINTER, t0.start, t0.end)
            statements.append(statement)
            return True

        (ind, expr) = AST.read_expression(tokens, index[0])
        if ind == None:
            raise_syntax_error("Unexpected token", t0)
        statement = Statement(StatementType.INLINE)
        statement.expr = expr
        statement.token = Token(t0.code, TokenType.POINTER, t0.start, expr[-1].end)
        statements.append(statement)
        index[0] = ind
        return True

    def parse(tokens: List[Token], macros: List):
        statements: List[Statement] = []
        index = [-1]

        while AST.parse_iterate(statements, tokens, index, macros):
            pass
        return statements
