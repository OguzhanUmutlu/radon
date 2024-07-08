from fileinput import filename
from math import inf
from typing import List, Union
from tokenizer import (
    Token,
    TokenType,
    Tokenizer,
    SET_OP,
    INC_OP,
    CMP_OP,
    CMP_COMBINE_OP,
)
from dp_ast import Statement, StatementType, AST, COMMANDS
from error import raise_syntax_error, raise_syntax_error_t

_expr_id = 0
FLOAT_PREC = 100


def get_expr_id():
    global _expr_id
    _expr_id += 1
    return _expr_id


def _li2lf(a):
    return a * FLOAT_PREC


def _lf2li(a):
    return int(a)


def _int2float(a):
    return [f"scoreboard players operation {a} *= FLOAT_PREC --temp--"]


def _float2int(a):
    return [f"scoreboard players operation {a} /= FLOAT_PREC --temp--"]


# types: i,f,li,lf
def _compute(a, b, typeA, op, typeB):
    if typeA == typeB == "i":
        return [f"scoreboard players operation {a} {op}= {b}"]
    if typeA == typeB == "f":
        l = [f"scoreboard players operation {a} {op}= {b}"]
        if op in list("+-"):
            return l
        return l + [f"scoreboard players operation {a} {op}= FLOAT_PREC --temp--"]
    if typeA == "i" and typeB == "f":
        return _float2int(b) + _compute(a, b, "i", op, "i")
    if typeA == "f" and typeB == "i":
        return _int2float(b) + _compute(a, b, "f", op, "f")

    if typeA == "f" and typeB == "li" and op in list("*/"):
        id = get_expr_id()
        return [
            f"scoreboard players set int_{id} --temp-- {int(b)}",
            f"scoreboard players operation {a} {op}= int_{id} --temp--",
        ]
    if typeA == "f" and (typeB == "lf" or typeB == "li") and op in list("+-"):
        action = "add" if op == "+" else "remove"
        return [
            f"scoreboard players {action} {a} {int(b * FLOAT_PREC)}",
        ]

    targetFunc = _lf2li
    target = "i"
    targetNo = "f"
    targetName = "int"
    if typeA == "f" or typeB == "f":
        target = "f"
        targetNo = "i"
        targetFunc = _li2lf
        targetName = "float"

    if typeA == "l" + targetNo:
        typeA = "l" + target
        a = targetFunc(a)
    elif typeA == "lf":
        a *= FLOAT_PREC
    if typeB == "l" + targetNo:
        typeB = "l" + target
        b = targetFunc(b)
    elif typeB == "lf":
        b *= FLOAT_PREC

    # now they can only be: f,lf | lf,f | i,li | li,i

    if op in list("+-"):  # addition and subtraction is straight forward.
        lit = a if typeA[0] == "l" else b
        id = get_expr_id()
        if typeA[0] == "l":
            a = f"{targetName}_{id} --temp--"
        if typeB[0] == "l":
            b = f"{targetName}_{id} --temp--"
        return [
            f"scoreboard players set {targetName}_{id} --temp-- {int(lit)}",
            f"scoreboard players operation {a} {op}= {b}",
        ]

    # now it's multiplication or division:
    if target == "f":
        id = get_expr_id()
        lit = a if typeA == "lf" else b
        if typeA == "lf":
            a = "float_" + str(id) + " --temp--"
        if typeB == "lf":
            b = "float_" + str(id) + " --temp--"
        return [f"scoreboard players set float_{id} --temp-- {int(lit)}"] + _compute(
            a, b, "f", op, "f"
        )

    # integer multiplication and division is built-in

    return [f"scoreboard players operation {a} {op}= {b}"]


def _get_score_type(score):
    if isinstance(score, int):
        return "int"
    elif isinstance(score, float):
        return "float"
    return "float" if score.startswith("float_") else "int"


# expression tokens: int_literal, float_literal, identifier, selector_identifier


class Transpiler:
    def transpile_str(code: str):
        (statements, macros) = AST.parse_str(code)

        return Transpiler().transpile(statements, macros)

    def __init__(self):
        self.files = dict()
        self.pack_name = "pack"
        self.pack_desc = "This is a datapack!"
        self.pack_format = 10
        self.variables = dict()
        self.functions = dict()
        self.loops = dict()

    def transpile(self, statements: List[Statement], macros: List):
        self.macros = macros
        loadF = [
            "# Setup #",
            "",
            'scoreboard objectives add --temp-- dummy ""',
            "scoreboard players set null --temp-- 0",
            "scoreboard players set FLOAT_PREC --temp-- " + str(FLOAT_PREC),
            'scoreboard objectives add true dummy ""',
            'scoreboard objectives add false dummy ""',
            'scoreboard objectives add null dummy ""',
            'scoreboard objectives add __returned__ dummy ""',
            "scoreboard players set !global true 1",
            "scoreboard players set !global false 0",
            "scoreboard players set !global null 0",
        ]
        self.files["__load__"] = loadF
        self.variables["false"] = {"type": "int", "constant": True}
        self.variables["true"] = {"type": "int", "constant": True}
        self.variables["null"] = {"type": "int", "constant": True}
        mainFile = []
        self.mainFile = mainFile
        self._transpile(statements, mainFile, None, None)
        loadF.append("")
        loadF.append("# Main File #")
        loadF.append("")
        loadF += mainFile
        return self

    def _transpile(self, statements: List[Statement], file, in_fn, in_loop):
        for statement in statements:
            if statement.type == StatementType.SCHEDULE:
                file_name = self._run_safe(
                    "__schedule__", statement.body, in_fn, in_loop
                )
                file.append(
                    f"schedule function $PACK_NAME$:{file_name} {statement.time.value} replace"
                )
                self._return_safe(file, in_fn, in_loop)
                continue
            if statement.type == StatementType.BREAK:
                if not in_loop:
                    raise_syntax_error(
                        "Cannot use break outside of loop", statement.token
                    )
                loop = self.loops[in_loop]
                if file is loop["file"]:
                    file.append("return")
                else:
                    file.append(f"scoreboard players set {in_loop} __break__ 1")
                    file.append(f"return")
                continue
            if statement.type == StatementType.CONTINUE:
                if not in_loop:
                    raise_syntax_error(
                        "Cannot use continue outside of loop", statement.token
                    )
                loop = self.loops[in_loop]
                if file is loop["file"]:
                    file.append(loop["continue"])
                    file.append("return")
                else:
                    file.append(f"scoreboard players set {in_loop} __continue__ 1")
                    file.append(f"return")
                continue
            if statement.type == StatementType.LOOP:
                file_name = self._run_safe("__loop__", statement.body, in_fn, statement)
                file.append(f"function $PACK_NAME$:{file_name}")
                loop_file = self.files[file_name]
                loop_id = int(file_name.split("/")[-1])
                loop_file.insert(0, f"scoreboard players set {loop_id} __break__ 0")
                loop_file.insert(0, f"scoreboard players set {loop_id} __continue__ 0")
                loop = self.loops[loop_id]
                loop_file.append(loop["continue"])
                continue
            if statement.type == StatementType.IF_FLOW:
                has_if = len(statement.body) != 0
                has_else = statement.elseBody != None and len(statement.elseBody) != 0
                if not has_if and not has_else:
                    continue
                (if_cmd, unless_cmd) = self.exec_if(statement.condition, file, in_fn)
                has_one = (has_if or has_else) and (not has_if or not has_else)
                if has_one:
                    one_body = statement.body if has_if else statement.elseBody
                    i_cmd = if_cmd if has_if else unless_cmd
                    if (
                        in_loop
                        and self.loops[in_loop]["file"] is file
                        and len(one_body) == 1
                        and one_body[0].type == StatementType.BREAK
                    ):
                        if not in_loop:
                            raise_syntax_error(
                                "Cannot use break outside of loop", statement.token
                            )
                        file.append(f"{i_cmd}return")
                        continue

                if has_if:
                    length_check = []
                    self._transpile(statement.body, length_check, in_fn, in_loop)
                    if_name = self._run_safe("__if__", statement.body, in_fn, in_loop)
                    file.append(f"{if_cmd}function $PACK_NAME$:{if_name}")
                    if has_else:
                        file.append("scoreboard players set __if__ --temp-- 0")
                        self.files[if_name].insert(
                            0, "scoreboard players set __if__ --temp-- 1"
                        )
                        else_name = self._run_safe(
                            "__else__", statement.elseBody, in_fn, in_loop
                        )
                        file.append(
                            f"execute if score __if__ matches 0..0 run function $PACK_NAME$:{else_name}"
                        )
                else:
                    else_name = self._run_safe(
                        "__else__", statement.elseBody, in_fn, in_loop, unless_cmd
                    )
                    file.append(f"{unless_cmd}function $PACK_NAME$:{else_name}")
                self._return_safe(file, in_fn, in_loop)
                continue
            if statement.type == StatementType.INLINE:
                expr = statement.expr
                ret = self.transpile_expr(expr, file, in_fn)
                if isinstance(ret, str):
                    # Cleaning the return results of the inline expression since they aren't gonna be used
                    cl1 = f"scoreboard players operation {ret} --temp-- = "
                    cl2 = f"execute store result score {ret} --temp-- run "
                    if file[-1].startswith(cl1):
                        file.pop()
                    if file[-1].startswith(cl2):
                        file[-1] = file[-1][len(cl2) :]
                    if len(file) >= 2 and file[-2].startswith(cl1):  # for x++ and x--
                        file.pop(-2)
                continue
            if statement.type == StatementType.DEFINE_FUNCTION:
                if file is not self.mainFile:
                    raise_syntax_error(
                        "Functions should be declared in the main scope",
                        statement.token,
                    )
                fn_name = statement.name.value
                for arg in statement.arguments:
                    arg[2] = get_expr_id()
                self.functions[statement.name.value] = {
                    "file": fn_name,
                    "returns": statement.returns.value,
                    "arguments": statement.arguments,
                    "returnId": statement.returns.value + "_" + str(get_expr_id()),
                }
                self.files[fn_name] = []
                self._transpile(
                    statement.body, self.files[fn_name], statement.name.value, in_loop
                )
                continue
            if statement.type == StatementType.RETURN:
                if not in_fn:
                    raise_syntax_error(
                        "Cannot use return keyword outside functions", statement.token
                    )
                fn = self.functions[in_fn]
                returns = fn["returns"]
                expr = statement.expr
                if returns == "void" and len(expr) != 0:
                    raise_syntax_error(
                        f"Function cannot return a value because it has a void return type",
                        statement.token,
                    )
                if returns != "void":
                    score = self.transpile_expr(expr, file, in_fn)
                    got_returns = _get_score_type(score)
                    if got_returns != returns:
                        raise_syntax_error(
                            f"Function has a return type of {returns}, but a {got_returns} was returned",
                            statement.token,
                        )
                    if isinstance(score, int) or isinstance(score, float):
                        ret = (
                            int(score * FLOAT_PREC)
                            if returns == "float"
                            else int(score)
                        )
                        file.append(
                            f"scoreboard players set {fn['returnId']} --temp-- {score}"
                        )
                    else:
                        file.append(
                            f"scoreboard players operation {fn['returnId']} --temp-- = {score} --temp--"
                        )
                if file is not self.files[in_fn]:
                    file.append(f"scoreboard players set {in_fn} __returned__ 1")
                file.append(f"return")
                continue
            if statement.type == StatementType.INTRODUCE_VARIABLE:
                name = statement.name.value
                type = statement.varType.value
                if name in self.variables:
                    raise_syntax_error(
                        "Variable is already introduced", statement.token
                    )
                self.variables[name] = {
                    "type": type,
                    "constant": False,
                }
                self.files["__load__"].append(f'scoreboard objectives add {name} dummy ""')
                self.files["__load__"].append(
                    f"scoreboard objectives enable !global {name}"
                )
                continue
            if statement.type == StatementType.EXECUTE_MACRO:
                exec_name = self._run_safe(
                    "__execute__", statement.body, in_fn, in_loop
                )
                file.append(
                    f"execute {statement.command} run function $PACK_NAME$:{exec_name}"
                )
                self._return_safe(file, in_fn, in_loop)
                continue
            raise_syntax_error("Invalid statement", statement.token)

    def _run_safe(self, folder_name, statements, in_fn, in_loop):
        id = get_expr_id()
        file_name = f"{folder_name}/{id}"
        new_file = []
        if isinstance(in_loop, Statement):
            cont = f"function $PACK_NAME$:{file_name}"
            stat = in_loop
            if stat.time:
                cont = f"schedule function $PACK_NAME$:{file_name} {stat.time.value} replace"
            self.loops[id] = {
                "file": new_file,
                "file_path": file_name,
                "continue": cont,
            }
            in_loop = id
        self.files[file_name] = new_file
        self._transpile(statements, new_file, in_fn, in_loop)
        return file_name

    def _return_safe(self, file, in_fn, in_loop):
        if in_fn:
            file.append(
                f"execute if score {in_fn} __returned__ matches 1..1 run return"
            )
        if in_loop:
            loop = self.loops[in_loop]
            if file is loop["file"]:
                file.append(
                    f"execute if score {in_loop} __break__ matches 1..1 run return"
                )
                file.append(
                    f"execute if score {in_loop} __continue__ matches 1..1 run return run {loop['continue']}"
                )
            else:
                file.append(
                    f"execute if score {in_loop} __break__ matches 1..1 run return"
                )
                file.append(
                    f"execute if score {in_loop} __continue__ matches 1..1 run return"
                )

    def split_cmp(self, expr: List[Token]):
        spl = []
        spl_ci = 0
        spl.append([[], None, []])
        for t in expr:
            if t.value in CMP_COMBINE_OP:
                spl_ci = False
                spl.append(t)
                spl.append([[], None, []])
            elif t.value in CMP_OP:
                if spl_ci != 0:
                    raise_syntax_error("Unexpected comparison operator", t)
                spl_ci = 2
                spl[-1][1] = t
            else:
                spl[-1][spl_ci].append(t)
        return spl

    def _get_expr_direct(self, tokens: List[Token], file, in_fn):
        if len(tokens) == 1:
            if tokens[0].type == TokenType.INT_LITERAL:
                return int(tokens[0].value)
            if tokens[0].type == TokenType.FLOAT_LITERAL:
                return float(tokens[0].value)
            if (
                tokens[0].type == TokenType.IDENTIFIER
                or tokens[0].type == TokenType.SELECTOR_IDENTIFIER
            ):
                (loc, _) = self.__get_var_loc(tokens[0], in_fn)
                return loc
            raise_syntax_error_t("Invalid expression", tokens, 0, 1)
        r = self.transpile_expr(tokens, file, in_fn)
        if isinstance(r, str):
            return r + " --temp--"
        return r

    def run_cmd(self, cmd: str, file, in_fn):
        cmd_str = ""
        i = 0
        has_repl = False
        repl_i = 0
        cmd = " ".join(s[:-1] if s[-1] == "\\" else s for s in cmd.strip().split("\n"))
        while i < len(cmd):
            if cmd[i : i + 3] == "\\$(":
                cmd_str += "$("
                i += 3
                continue
            if (
                cmd[i : i + 2] == "$("
                or cmd[i : i + 5] == "$get("
                or cmd[i : i + 5] == "$str("
            ):
                si = i
                k = 0
                while i < len(cmd):
                    i += 1
                    c = cmd[i]
                    if c == "(":
                        k += 1
                    if c == ")":
                        k -= 1
                        if k == 0:
                            break
                if cmd[i] != ")":
                    raise_syntax_error_t("Unterminated parentheses", cmd, si, i + 1)
                repl = cmd[si + (2 if cmd[si + 1] == "(" else 5) : i]
                (expr, _) = Tokenizer.tokenize(repl)
                expr = expr[:-1]
                loc = self.get_expr_loc(expr, file, in_fn)

                if cmd[si + 1] == "(":
                    cmd_str += f"$(_{repl_i})"
                    if isinstance(loc, int) or isinstance(loc, float):
                        file.append(
                            f"data modify storage cmd_mem _{repl_i} set value {loc}"
                        )
                    else:
                        if loc.startswith("float_"):
                            precStr = str(1 / FLOAT_PREC)
                            file.append(
                                f"execute store result storage cmd_mem _{repl_i} float {precStr} run scoreboard players get {loc}"
                            )
                        else:
                            file.append(
                                f"execute store result storage cmd_mem _{repl_i} int 1 run scoreboard players get {loc}"
                            )
                    has_repl = True
                    repl_i += 1
                elif cmd[si + 1] == "g":
                    if isinstance(loc, int) or isinstance(loc, float):
                        cmd_str += str(loc)
                    else:
                        if loc.startswith("float_"):
                            raise_syntax_error(
                                "Cannot read float value with a $get() macro", expr[0]
                            )
                        else:
                            cmd_str += f"scoreboard players get {loc}"
                elif cmd[si + 1] == "s":
                    if isinstance(loc, int) or isinstance(loc, float):
                        cmd_str += '"' + str(loc) + '"'
                    else:
                        if loc.startswith("float_"):
                            raise_syntax_error(
                                "Cannot read float value with a $str() macro", expr[0]
                            )
                        else:
                            ls = loc.split(" ")
                            cmd_str += (
                                '{"score":{"name":"'
                                + ls[0]
                                + '","objective":"'
                                + ls[1]
                                + '"}}'
                            )

                i += 1
                continue
            cmd_str += cmd[i]
            i += 1

        eid = "int_" + str(get_expr_id())
        if not has_repl:
            file.append(f"execute store result score {eid} --temp-- run {cmd_str}")
            return eid

        cmd_file = []
        file_name = None
        for i in self.files:
            if "\n".join(self.files[i]) == "\n".join(cmd_file):
                file_name = i
                break
        if file_name == None:
            cmd_id = get_expr_id()
            file_name = f"__cmd__/{cmd_id}"
        self.files[file_name] = cmd_file
        cmd_file.append("$" + cmd_str)
        file.append(
            f"execute store result score {eid} --temp-- run function $PACK_NAME$:{file_name} with storage cmd_mem"
        )
        return eid

    def __get_var_loc(self, t, in_fn):
        if t.type == TokenType.SELECTOR_IDENTIFIER:
            name = t.name.value
            if name not in self.variables:
                raise_syntax_error("Undefined variable", t)
            var_type = self.variables[name]["type"]
            return (f"{t.selector.value} {name}", var_type)
        if t.type == TokenType.IDENTIFIER:
            if t.value not in self.variables:
                if in_fn:
                    found = None
                    for arg in self.functions[in_fn]["arguments"]:
                        if arg[1] == t.value:
                            found = arg
                            break
                    if found:
                        var_type = found[0]
                        return (f"{var_type}_{found[2]} --temp--", var_type)
                raise_syntax_error("Undefined variable", t)

            var_type = self.variables[t.value]["type"]
            return (f"!global {t.value}", var_type)

    def __get_expr_type(self, t, file, in_fn) -> Union[Token, str]:
        if not isinstance(t, Token):
            return t
        if t.type == TokenType.INT_LITERAL:
            return int(t.value)
        if t.type == TokenType.FLOAT_LITERAL:
            return float(t.value)
        if t.type == TokenType.SELECTOR_IDENTIFIER or t.type == TokenType.IDENTIFIER:
            (loc, var_type) = self.__get_var_loc(t, in_fn)
            id = get_expr_id()
            eid = var_type + "_" + str(id)
            file.append(f"scoreboard players operation {eid} --temp-- = {loc}")
            return eid
        if t.type == TokenType.FUNCTION_CALL:
            if t.func.value not in self.functions:
                raise_syntax_error("Undefined function", t)
            separated = Tokenizer.split_tokens(t.children)
            fn = self.functions[t.func.value]
            returns = fn["returns"]
            fn_args = fn["arguments"]
            if len(separated) != len(fn_args):
                raise_syntax_error(
                    "Expected "
                    + str(len(fn_args))
                    + " argument"
                    + ("s" if len(fn_args) > 1 else "")
                    + ", got "
                    + str(len(separated)),
                    t,
                )
            for index, arg in enumerate(separated):
                fn_arg = fn_args[index]
                arg_type = fn_arg[0]
                eid = arg_type + "_" + str(fn_arg[2])

                if len(arg) == 1 and arg[0].type in [
                    TokenType.IDENTIFIER,
                    TokenType.SELECTOR_IDENTIFIER,
                ]:
                    (loc, _) = self.__get_var_loc(arg[0], in_fn)
                    file.append(f"scoreboard players operation {eid} --temp-- = {loc}")
                    continue
                score = self.transpile_expr(arg, file, in_fn)
                score_type = _get_score_type(score)
                if score_type != arg_type:
                    raise_syntax_error(
                        f"Function call's {index+1}. argument was expected to be {arg_type}, got {score_type}",
                        t,
                    )
                if isinstance(score, int) or isinstance(score, float):
                    val = int(score * FLOAT_PREC) if arg_type == "float" else int(score)
                    file.append(f"scoreboard players set {eid} --temp {val}")
                else:
                    file.append(
                        f"scoreboard players operation {eid} --temp-- = {score} --temp--"
                    )
            fn_id = get_expr_id()
            file.append(f"scoreboard players set {t.func.value} __returned__ 0")
            file.append(f"function $PACK_NAME$:{t.func.value}")

            # the line after these comments is for the case where you call the function that is currently running
            # example:
            # function test(): void {
            #   # "scoreboard players set {t.func.value} __returned__ 0" runs:
            #   # test __returned__ = 0
            #   a()
            #   # test __returned__ = 1
            #   # "scoreboard players set {t.func.value} __returned__ 0" runs again and:
            #   # test __returned__ = 0
            #   return
            # }
            # function a(): void {
            #   test()
            #   return
            # }
            file.append(f"scoreboard players set {t.func.value} __returned__ 0")

            if returns != "void":
                returnId = fn["returnId"]
                file.append(
                    f"scoreboard players operation {returns}_{fn_id} --temp-- = {returnId} --temp--"
                )
            return returns + "_" + str(fn_id) if returns != "void" else "null"
        raise_syntax_error("Invalid expression", t)

    def _transpile_expr(
        self, tokens: List[Token], file: List[str], in_fn
    ) -> Union[Token, str]:
        if len(tokens) == 0:
            return "null"
        t0 = tokens[0]
        if len(tokens) == 1:
            if (
                t0.type == TokenType.IDENTIFIER
                or t0.type == TokenType.SELECTOR_IDENTIFIER
                or t0.type == TokenType.FUNCTION_CALL
            ):
                return self.__get_expr_type(t0, file, in_fn)
            if t0.type == TokenType.GROUP:
                return self._transpile_expr(AST.make_expr(t0.children), file, in_fn)
            return t0
        if t0.value in COMMANDS:
            return self.run_cmd(t0.code[t0.start : tokens[-1].end], file, in_fn)
        if tokens[1].value in INC_OP:
            name = t0.value if t0.type == TokenType.IDENTIFIER else t0.name.value
            score_player = (
                "!global" if t0.type == TokenType.IDENTIFIER else t0.selector.value
            )
            if name not in self.variables:
                raise_syntax_error("Undefined variable", t0)

            var_type = self.variables[name]["type"]
            action = "add" if tokens[1].value == "++" else "remove"
            inc = FLOAT_PREC if var_type == "float" else 1
            id = get_expr_id()
            eid = var_type + "_" + str(id)
            file.append(
                f"scoreboard players operation {eid} --temp-- = {score_player} {name}"
            )
            file.append(f"scoreboard players {action} {score_player} {name} {inc}")
            return eid
        if t0.value in SET_OP:
            name = (
                tokens[1].value
                if tokens[1].type == TokenType.IDENTIFIER
                else tokens[1].name.value
            )
            score_player = (
                "!global"
                if tokens[1].type == TokenType.IDENTIFIER
                else tokens[1].selector.value
            )
            expr = tokens[2]
            if t0.value != "=" and name not in self.variables:
                raise_syntax_error("Undefined variable", tokens[1])

            exist_type = (
                None
                if t0.value == "=" and name not in self.variables
                else self.variables[name]["type"]
            )
            if len(expr) == 1 and expr[0].type in [
                TokenType.IDENTIFIER,
                TokenType.SELECTOR_IDENTIFIER,
            ]:
                (loc, var_type) = self.__get_var_loc(expr[0], in_fn)
                if exist_type and exist_type != var_type:
                    raise_syntax_error(
                        f"Variable was defined to be {exist_type}, got {var_type}"
                    )
                file.append(
                    f"scoreboard players operation {score_player} {name} = {loc}"
                )
                id = get_expr_id()
                eid = f"{var_type}_{id}"
                file.append(f"scoreboard players operation {eid} --temp-- = {loc}")
                if name not in self.variables:
                    self.files["__load__"].append(
                        f'scoreboard objectives add {name} dummy ""'
                    )
                    self.variables[name] = {"type": var_type, "constant": False}
                return eid
            score = self.transpile_expr(expr, file, in_fn)
            var_type = _get_score_type(score)
            if exist_type and exist_type != var_type:
                if isinstance(score, int):
                    score = float(score)
                elif isinstance(score, float):
                    score = int(score)
                else:
                    if score.startswith("float_"):
                        file.append(f"scoreboard players operation {score} --temp-- /= FLOAT_PREC --temp--")
                    else:
                        file.append(f"scoreboard players operation {score} --temp-- *= FLOAT_PREC --temp--")

                var_type = exist_type
                        
            action = "add" if t0.value[0] == "+" else "remove"
            if isinstance(score, int):
                if t0.value == "=":
                    file.append(f"scoreboard players set {score_player} {name} {score}")
                else:
                    file.extend(
                        _compute(
                            f"{score_player} {name}",
                            score,
                            exist_type[0],
                            t0.value[0],
                            "li",
                        )
                    )
            elif isinstance(score, float):
                if t0.value == "=":
                    file.append(
                        f"scoreboard players set {score_player} {name} {int(score * FLOAT_PREC)}"
                    )
                else:
                    file.extend(
                        _compute(
                            f"{score_player} {name}",
                            score,
                            exist_type[0],
                            t0.value[0],
                            "lf",
                        )
                    )
                var_type = "float"
            else:
                if score.startswith("float_"):
                    var_type = "float"
                if t0.value == "=":
                    file.append(
                        f"scoreboard players operation {score_player} {name} = {score} --temp--"
                    )
                else:
                    file.extend(
                        _compute(
                            f"{score_player} {name}",
                            f"{score} --temp--",
                            exist_type[0],
                            t0.value[0],
                            var_type[0],
                        )
                    )

            if name not in self.variables:
                self.files["__load__"].append(f'scoreboard objectives add {name} dummy ""')

                self.variables[name] = {"type": var_type, "constant": False}
            return score
        stack = []
        for token in tokens:
            if token.type != TokenType.OPERATOR:
                stack.append(token)
                continue

            right = stack.pop()
            left = stack.pop()

            if isinstance(right, Token) and right.type == TokenType.GROUP:
                right = self._transpile_expr(AST.make_expr(right.children), file, in_fn)
            if isinstance(left, Token) and left.type == TokenType.GROUP:
                left = self._transpile_expr(AST.make_expr(left.children), file, in_fn)

            # right,left = number_literal, identifier, group or a score

            ri = isinstance(right, Token)
            rl = isinstance(left, Token)

            if (
                ri
                and rl
                and (
                    right.type == TokenType.INT_LITERAL
                    or right.type == TokenType.FLOAT_LITERAL
                )
                and (
                    left.type == TokenType.INT_LITERAL
                    or left.type == TokenType.FLOAT_LITERAL
                )
            ):
                n = str(eval(f"{left.value}{token.value}{right.value}"))
                type = (
                    TokenType.FLOAT_LITERAL
                    if right.type == TokenType.FLOAT_LITERAL
                    or left.type == TokenType.FLOAT_LITERAL
                    else TokenType.INT_LITERAL
                )
                stack.append(Token(n, type, 0, len(n)))
                continue

            lt = self.__get_expr_type(left, file, in_fn)
            rt = self.__get_expr_type(right, file, in_fn)

            _lt = lt
            _rt = rt

            lf = "i"
            if isinstance(lt, int):
                lf = "li"
            elif isinstance(lt, float):
                lf = "lf"
            elif lt.startswith("float_"):
                lf = "f"
            if lf[0] != "l":
                _lt += " --temp--"
            rf = "i"
            if isinstance(rt, int):
                rf = "li"
            elif isinstance(rt, float):
                rf = "lf"
            elif lt.startswith("float_"):
                rf = "f"
            if rf[0] != "l":
                _rt += " --temp--"

            file.extend(_compute(_lt, _rt, lf, token.value, rf))

            stack.append(lt)

        return stack[-1]

    def get_expr_loc(self, tokens, file, in_fn):
        is_var = len(tokens) == 1 and tokens[0].type in {
            TokenType.IDENTIFIER,
            TokenType.SELECTOR_IDENTIFIER,
        }
        if is_var:
            return self.__get_var_loc(tokens[0], in_fn)[0]

        r = self.transpile_expr(tokens, file, in_fn)
        if isinstance(r, str):
            return r + " --temp--"
        return r

    def transpile_expr(self, tokens, file, in_fn):
        tokens = AST.make_expr(tokens)
        r = self._transpile_expr(tokens, file, in_fn)
        if isinstance(r, Token):
            if r.type == TokenType.INT_LITERAL:
                return int(r.value)
            if r.type == TokenType.FLOAT_LITERAL:
                return float(r.value)
            return self.transpile_expr(r.children, file, in_fn)
        return r

    def exec_if(self, condition, file, in_fn):
        # [ [ LeftToken[], Operator, RightToken[] ], AndOrOperator, [ LeftToken[], Operator, RightToken[] ], ... ]
        cmp_list = self.split_cmp(condition)
        if len(cmp_list) == 1:
            # compute single comparison
            left = cmp_list[0][0]
            op = cmp_list[0][1].value
            right = cmp_list[0][2]

            lt = self._get_expr_direct(left, file, in_fn)
            rt = self._get_expr_direct(right, file, in_fn)

            lis = isinstance(lt, int) or isinstance(lt, float)
            ris = isinstance(rt, int) or isinstance(rt, float)

            if lis and ris:
                return float(lis) == float(ris)

            if_cmd = ""
            unless_cmd = ""  # opposite of if

            if lis or ris:
                if lis:
                    v = lt
                    lt = rt
                    rt = v
                    v = lis
                    lis = ris
                    ris = v
                if lis and isinstance(lt, float):
                    lt = int(lt * FLOAT_PREC)
                if ris and isinstance(rt, float):
                    rt = int(rt * FLOAT_PREC)
                if op == "==" or op == "is" or op == "!=" or op == "is not":
                    negative = op == "!=" or op == "is not"
                    _if = "unless" if negative else "if"
                    _opp = "if" if negative else "unless"
                    if_cmd = f"execute {_if} score {lt} matches {rt}..{rt} run "
                    unless_cmd = f"execute {_opp} score {lt} matches {rt}..{rt} run "
                else:
                    id = (
                        ("float" if isinstance(rt, float) else "int")
                        + "_"
                        + str(get_expr_id())
                    )
                    file.append(f"scoreboard players set {id} --temp-- {rt}")
                    if_cmd = f"execute if score {lt} {op} {id} --temp-- run "
                    unless_cmd = f"execute unless score {lt} {op} {id} --temp-- run "
            else:
                negative = op == "is not" or op == "!="
                if op == "is" or op == "==" or negative:
                    op = "="
                if_cmd = f"execute if score {lt} {op} {rt} run "
                unless_cmd = f"execute unless score {lt} {op} {rt} run "
                if negative:
                    t = if_cmd
                    if_cmd = unless_cmd
                    unless_cmd = t

            return (if_cmd, unless_cmd)

        raise SyntaxError("Not implemented")  # todo: and/or support
