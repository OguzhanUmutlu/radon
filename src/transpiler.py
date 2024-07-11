from typing import Dict, List, Union
import os
import sys
from tokenizer import (
    GroupToken,
    SelectorIdentifierToken,
    Token,
    SET_OP,
    INC_OP,
    CMP_OP,
    CMP_COMBINE_OP,
    split_tokens,
    tokenize,
)
from dp_ast import ContinueStatement, DefineFunctionStatement, ExecuteMacroStatement, IfFlowStatement, ImportStatement, InlineStatement, IntroduceVariableStatement, LoopStatement, ReturnStatement, ScheduleStatement, Statement, StatementType, COMMANDS, make_expr, parse_str
from error import raise_syntax_error, raise_syntax_error_t
from builtin.sqrt import LIB as LIB_SQRT
from utils import FunctionDeclaration, TranspilerContext, VariableDeclaration, TokenType

cwd = os.path.dirname(os.path.abspath(sys.argv[0]))
if sys.argv[0] == "":
    cwd = "/home/pyodide"


builtin = {
    "sqrt": LIB_SQRT
}

_expr_id = 0

def reset_expr_id():
    global _expr_id
    _expr_id = 0

FLOAT_PREC = 1000

def get_lib_contents(path: str):
    with open(cwd + "/" + path, "r") as f:
        return f.read()

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
        opN = "/" if op == "*" else "*"
        l2 = [f"scoreboard players operation {a} {opN}= FLOAT_PREC --temp--"]

        # Multiplication should be done to not lose precision
        return (l + l2) if op == "*" else (l2 + l)
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
    if typeA == "f" or typeB == "f":
        target = "f"
        targetNo = "i"
        targetFunc = _li2lf

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
        opN = "add" if op == "+" else "remove"
        target_id = b if typeA[0] == "l" else a
        return [
            f"scoreboard players {opN} {target_id} {int(lit)}",
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

def transpile_str(code: str):
    (statements, macros) = parse_str(code)

    return Transpiler().transpile(statements, macros)

class Transpiler:
    def __init__(self):
        self.files = dict()
        self.pack_name = "pack"
        self.pack_desc = "This is a datapack!"
        self.pack_format = 10
        self.variables: Dict[str, VariableDeclaration] = dict()
        self.functions: List[FunctionDeclaration] = []
        self.loops = dict()
        self.init_libs = []

    def transpile(self, statements: List[Statement], macros: List):
        self.macros = macros
        loadF = [
            "# Setup #",
            "",
            'scoreboard objectives add --temp-- dummy ""',
            'scoreboard objectives add global dummy ""',
            'scoreboard objectives add __break__ dummy ""',
            'scoreboard objectives add __continue__ dummy ""',
            "scoreboard players set null --temp-- 0",
            "scoreboard players set FLOAT_PREC --temp-- " + str(FLOAT_PREC),
            'scoreboard objectives add true dummy ""',
            'scoreboard objectives add false dummy ""',
            'scoreboard objectives add null dummy ""',
            "scoreboard players set !global true 1",
            "scoreboard players set !global false 0",
            "scoreboard players set !global null 0",
        ]
        self.files["__load__"] = loadF
        self.variables["false"] = VariableDeclaration("int", True)
        self.variables["true"] = VariableDeclaration("int", True)
        self.variables["null"] = VariableDeclaration("int", True)
        mainFile = []
        self.mainFile = mainFile
        self._transpile(statements, TranspilerContext(self, "__main__", mainFile, None, None))
        loadF.append("")
        loadF.append("# Main File #")
        loadF.append("")
        loadF += mainFile
        return self

    def _transpile(self, statements: List[Statement], ctx: TranspilerContext):
        file = ctx.file
        function = ctx.function
        loop = ctx.loop
        for statement in statements:
            if isinstance(statement, ImportStatement):
                if statement._as == None:
                    pass
                else:
                    save = str(get_expr_id())
                    path = statement.path.value[1:-1]
                    self.add_mcfunction_file(save,path)
                    self.functions.append(
                        FunctionDeclaration(
                            type="mcfunction",
                            name=statement._as.value,
                            file_name=save,
                            returns="int",
                            returnId="",
                            arguments=[]
                        )
                    )
                continue
            if isinstance(statement, ScheduleStatement):
                file_name = self._run_safe(
                    "__schedule__", statement.body, ctx
                )
                file.append(
                    f"schedule function $PACK_NAME$:{file_name} {statement.time.value} replace"
                )
                self._return_safe(ctx)
                continue
            if statement.type == StatementType.BREAK:
                if not loop:
                    raise_syntax_error(
                        "Cannot use break outside of loop", statement
                    )
                if file is loop["file"]:
                    file.append("return")
                else:
                    file.append(f"scoreboard players set {loop["id"]} __break__ 1")
                    file.append(f"return")
                continue
            if isinstance(statement, ContinueStatement):
                if not loop:
                    raise_syntax_error(
                        "Cannot use continue outside of loop", statement
                    )
                if file is loop["file"]:
                    file.append(loop["continue"])
                    file.append("return")
                else:
                    file.append(f"scoreboard players set {loop["id"]} __continue__ 1")
                    file.append(f"return")
                continue
            if isinstance(statement, LoopStatement):
                file_name = self._run_safe("__loop__", statement.body, TranspilerContext(self, ctx.file_name, file, function,statement))
                file.append(f"function $PACK_NAME$:{file_name}")
                loop_file = self.files[file_name]
                loop_id = int(file_name.split("/")[-1])
                loop_file.insert(0, f"scoreboard players set {loop_id} __break__ 0")
                loop_file.insert(0, f"scoreboard players set {loop_id} __continue__ 0")
                loop = self.loops[loop_id]
                loop_file.append(loop["continue"])
                continue
            if isinstance(statement, IfFlowStatement):
                has_if = len(statement.body) != 0
                has_else = statement.elseBody != None and len(statement.elseBody) != 0
                if not has_if and not has_else:
                    continue
                resp = self.exec_if(statement.condition, ctx)
                if isinstance(resp,bool):
                    if resp:
                        if not has_if:
                            continue
                        self._transpile(statement.body, ctx)
                    elif has_else and statement.elseBody: # I know this is bad, but the linter wants it
                        self._transpile(statement.elseBody, ctx)
                    continue
                (if_cmd, unless_cmd) = resp
                has_one = (has_if or has_else) and (not has_if or not has_else)
                if has_one:
                    one_body = statement.body if has_if else statement.elseBody
                    i_cmd = if_cmd if has_if else unless_cmd
                    if (
                        loop
                        and one_body
                        and loop["file"] is file
                        and len(one_body) == 1
                        and one_body[0].type == StatementType.BREAK
                    ):
                        if not loop:
                            raise_syntax_error(
                                "Cannot use break outside of loop", statement
                            )
                        file.append(f"{i_cmd}return")
                        continue

                if has_if:
                    if_name = self._run_safe("__if__", statement.body, ctx)
                    file.append(f"{if_cmd}function $PACK_NAME$:{if_name}")
                    if has_else:
                        file.append("scoreboard players set __if__ --temp-- 0")
                        self.files[if_name].insert(
                            0, "scoreboard players set __if__ --temp-- 1"
                        )
                        else_name = self._run_safe(
                            "__else__", statement.elseBody, ctx
                        )
                        file.append(
                            f"execute if score __if__ matches 0..0 run function $PACK_NAME$:{else_name}"
                        )
                else:
                    else_name = self._run_safe(
                        "__else__", statement.elseBody, ctx
                    )
                    file.append(f"{unless_cmd}function $PACK_NAME$:{else_name}")
                self._return_safe(ctx)
                continue
            if isinstance(statement, InlineStatement):
                expr = statement.expr
                ret = self.transpile_expr(expr, ctx)
                if isinstance(ret, str):
                    # Cleaning the return results of the inline expression since they aren't gonna be used
                    cl1 = f"scoreboard players operation {ret} --temp-- = "
                    cl2 = f"execute store result score {ret} --temp-- run "
                    if file[-1].startswith(cl1):
                        file.pop()
                    if file[-1].startswith(cl2):
                        file[-1] = file[-1][len(cl2) :]
                    #if len(file) >= 2 and file[-2].startswith(cl1):  # for x++ and x--, commented it for library functions
                        #file.pop(-2)
                continue
            if isinstance(statement, DefineFunctionStatement):
                if function or loop:
                    raise_syntax_error(
                        "Functions should be declared in the main scope",
                        statement
                    )
                fn_name = statement.name.value
                for arg in statement.arguments:
                    arg.id = arg.type + "_" + str(get_expr_id())
                types = ",".join(arg.type for arg in statement.arguments)
                count = 0
                for fn in self.functions:
                    fn_types = ",".join(arg.type for arg in fn.arguments)
                    if fn_name == fn.name:
                        count += 1
                        if types == fn_types:
                            raise_syntax_error(
                                "Function with same name and arguments already exists",
                                statement
                            )
                file_name = fn_name + ("" if count == 0 else str(count))
                fn = FunctionDeclaration(
                    type="radon",
                    name=fn_name,
                    file_name=file_name,
                    returns=statement.returns.value,
                    returnId=statement.returns.value + "_" + str(get_expr_id()),
                    arguments=statement.arguments
                )
                self.functions.append(fn)
                self.files[file_name] = []
                self._transpile(
                    statement.body, TranspilerContext(self, file_name, self.files[file_name], fn, loop)
                )
                continue
            if isinstance(statement, ReturnStatement):
                if not function:
                    raise_syntax_error(
                        "Cannot use return keyword outside functions", statement
                    )
                    continue
                returns = function.returns
                expr = statement.expr
                if returns == "void" and len(expr) != 0:
                    raise_syntax_error(
                        f"Function cannot return a value because it has a void return type",
                        statement
                    )
                if returns != "void":
                    score = self.transpile_expr(expr, ctx)
                    got_returns = _get_score_type(score)
                    if got_returns != returns:
                        raise_syntax_error(
                            f"Function has a return type of {returns}, but a {got_returns} was returned",
                            statement
                        )
                    if isinstance(score, int) or isinstance(score, float):
                        ret = (
                            int(score * FLOAT_PREC)
                            if returns == "float"
                            else int(score)
                        )
                        file.append(
                            f"scoreboard players set {function.returnId} --temp-- {score}"
                        )
                    else:
                        file.append(
                            f"scoreboard players operation {function.returnId} --temp-- = {score} --temp--"
                        )
                if file is not self.files[function.file_name]:
                    file.append(f"scoreboard players set __returned__ --temp-- 1")
                file.append(f"return")
                continue
            if isinstance(statement, IntroduceVariableStatement):
                name = statement.name.value
                type = statement.varType.value
                if name in self.variables:
                    raise_syntax_error(
                        "Variable is already introduced", statement
                    )
                self.variables[name] = VariableDeclaration(type,False)
                self.files["__load__"].append(
                    f'scoreboard objectives add {name} dummy ""'
                )
                self.files["__load__"].append(
                    f"scoreboard objectives enable {name} global"
                )
                continue
            if isinstance(statement, ExecuteMacroStatement):
                exec_name = self._run_safe(
                    "__execute__", statement.body, ctx
                )
                file.append(
                    f"execute {statement.command} run function $PACK_NAME$:{exec_name}"
                )
                self._return_safe(ctx)
                continue
            raise_syntax_error("Invalid statement", statement)

    def _run_safe(self, folder_name, statements, ctx: TranspilerContext):
        loop = ctx.loop
        id = get_expr_id()
        file_name = f"{folder_name}/{id}"
        new_file = []
        if isinstance(loop, LoopStatement):
            cont = f"function $PACK_NAME$:{file_name}"
            stat = loop
            if stat.time:
                cont = f"schedule function $PACK_NAME$:{file_name} {stat.time.value} replace"
            loop = {
                "id": id,
                "file": new_file,
                "file_path": file_name,
                "continue": cont,
            }
            self.loops[id] = loop
        self.files[file_name] = new_file
        self._transpile(statements, TranspilerContext(self, file_name, new_file, ctx.function, loop))
        return file_name

    def _return_safe(self, ctx: TranspilerContext):
        file = ctx.file
        function = ctx.function
        loop = ctx.loop
        if function:
            file.append(
                f"execute if score __returned__ --temp-- matches 1..1 run return"
            )
        if loop:
            if file is loop["file"]:
                file.append(
                    f"execute if score {loop['id']} __break__ matches 1..1 run return"
                )
                file.append(
                    f"execute if score {loop['id']} __continue__ matches 1..1 run return run {loop['continue']}"
                )
            else:
                file.append(
                    f"execute if score {loop['id']} __break__ matches 1..1 run return"
                )
                file.append(
                    f"execute if score {loop['id']} __continue__ matches 1..1 run return"
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

    def _get_expr_direct(self, tokens: List[Token], ctx: TranspilerContext):
        if len(tokens) == 1:
            if tokens[0].type == TokenType.INT_LITERAL:
                return int(tokens[0].value)
            if tokens[0].type == TokenType.FLOAT_LITERAL:
                return float(tokens[0].value)
            if (
                tokens[0].type == TokenType.IDENTIFIER
                or tokens[0].type == TokenType.SELECTOR_IDENTIFIER
            ):
                (loc, _) = self.__get_var_loc(tokens[0], ctx)
                return loc
            raise_syntax_error_t("Invalid expression", tokens, 0, 1)
        r = self.transpile_expr(tokens, ctx)
        if isinstance(r, str):
            return r + " --temp--"
        return r

    def run_cmd(self, cmd: str, ctx: TranspilerContext):
        file = ctx.file
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
                (expr, _) = tokenize(repl)
                expr = expr[:-1]
                (loc, loc_type) = self.get_expr_loc(expr, ctx)

                if cmd[si + 1] == "(":
                    cmd_str += f"$(_{repl_i})"
                    if isinstance(loc, int) or isinstance(loc, float):
                        file.append(
                            f"data modify storage cmd_mem _{repl_i} set value {loc}"
                        )
                    else:
                        if loc_type == "float":
                            precStr = "{:.7f}".format(1 / FLOAT_PREC)
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

    def __get_var_loc(self, t, ctx: TranspilerContext) -> tuple[str, str]:
        if t.type == TokenType.SELECTOR_IDENTIFIER:
            name = t.name.value
            if name not in self.variables:
                raise_syntax_error("Undefined variable", t)
            var_type = self.variables[name].type
            return (f"{t.selector.value} {name}", var_type)
        if t.type == TokenType.IDENTIFIER:
            if t.value not in self.variables:
                if ctx.function:
                    fn = ctx.function
                    found = None
                    for arg in fn.arguments:
                        if arg.name == t.value:
                            found = arg
                            break
                    if found:
                        var_type = found.type
                        id = found.id
                        return (id + " --temp--", var_type)
                raise_syntax_error("Undefined variable", t)

            var_type = self.variables[t.value].type
            return (f"{t.value} global", var_type)
        raise SyntaxError("")

    def __get_expr_type(self, t, ctx: TranspilerContext):
        file = ctx.file
        if not isinstance(t, Token):
            return t
        if t.type == TokenType.INT_LITERAL:
            return int(t.value)
        if t.type == TokenType.FLOAT_LITERAL:
            return float(t.value)
        if t.type == TokenType.SELECTOR_IDENTIFIER or t.type == TokenType.IDENTIFIER:
            (loc, var_type) = self.__get_var_loc(t, ctx)
            id = get_expr_id()
            eid = var_type + "_" + str(id)
            file.append(f"scoreboard players operation {eid} --temp-- = {loc}")
            return eid
        if isinstance(t,GroupToken) and t.func:
            fnFound = False
            for f in self.functions:
                if f.file_name == t.func.value:
                    fnFound = True
                    break
            if not fnFound and t.func.value not in builtin:
                raise_syntax_error("Undefined function", t)
            if not fnFound and t.func.value in builtin:
                self.functions += builtin[t.func.value]["functions"]
            separated = split_tokens(t.children)
            given_args_types = []
            given_args_locations = []
            for index, arg in enumerate(separated):
                if len(arg) == 1 and arg[0].type in [
                    TokenType.IDENTIFIER,
                    TokenType.SELECTOR_IDENTIFIER,
                ]:
                    (loc, var_type) = self.__get_var_loc(arg[0], ctx)
                    given_args_types.append(var_type)
                    given_args_locations.append(loc)
                    continue
                score = self.transpile_expr(arg, ctx)
                score_type = _get_score_type(score)
                if isinstance(score, int) or isinstance(score, float):
                    given_args_locations.append(score)
                else:
                    given_args_locations.append(score + " --temp--")
                given_args_types.append(score_type)

            given_types = ",".join(given_args_types)

            fn = None
            for f in self.functions:
                fn_arg_types = ",".join(arg.type for arg in f.arguments)
                if fn_arg_types == given_types:
                    fn = f
                    break
            if fn == None:
                raise_syntax_error("Invalid arguments", t)
                raise SyntaxError("")

            returns = fn.returns
            fn_args = fn.arguments

            for lib in fn.libs:
                self.add_lib_file(lib)
            for lib in fn.initLibs:
                self.init_lib_file(lib)

            for index, arg in enumerate(fn_args):
                eid = arg.id
                loc = given_args_locations[index]
                if isinstance(loc, int) or isinstance(loc, float):
                    val = (
                        int(score * FLOAT_PREC) if score_type == "float" else int(score)
                    )
                    file.append(f"scoreboard players set {eid} --temp-- {val}")
                else:
                    file.append(f"scoreboard players operation {eid} --temp-- = {loc}")
            
            if fn.type == "mcfunction":
                file.append(f"function $PACK_NAME$:{fn.file_name}")
            
            fn_id = get_expr_id()
            if fn.returnId != "" and fn.type == "radon":
                file.append(f"scoreboard players set __returned__ --temp-- 0")
                file.append(f"function $PACK_NAME$:{fn.file_name}")

                # the line after these comments is for the case where you call a function inside a function
                # example:
                # function test(): void {
                #   # "scoreboard players set __returned__ --temp-- 0" runs:
                #   # __returned__ = 0
                #   a()
                #   # __returned__ = 1
                #   # "scoreboard players set __returned__ --temp-- 0" runs again and:
                #   # __returned__ = 0
                #   return
                # }
                # function a(): void {
                #   test()
                #   return
                # }
                if ctx.function:
                    file.append(f"scoreboard players set __returned__ --temp-- 0")
            
            if fn.returnId == "":
                file.append(f"execute store score {returns}_{fn_id} --temp-- run function $PACK_NAME$:{fn.file_name}")
            elif returns != "void":
                file.append(
                    f"scoreboard players operation {returns}_{fn_id} --temp-- = {fn.returnId} --temp--"
                )
            return returns + "_" + str(fn_id) if returns != "void" else "null"
        raise_syntax_error("Invalid expression", t)
        raise SyntaxError("")

    def _transpile_expr(
        self, tokens: List[Token], ctx:TranspilerContext
    ) -> Union[Token, str, int, float]:
        if len(tokens) == 0:
            return "null"
        file = ctx.file
        t0 = tokens[0]
        if len(tokens) == 1:
            if (
                t0.type == TokenType.IDENTIFIER
                or t0.type == TokenType.SELECTOR_IDENTIFIER
                or t0.type == TokenType.FUNCTION_CALL
            ):
                return self.__get_expr_type(t0, ctx)
            if isinstance(t0,GroupToken):
                return self._transpile_expr(make_expr(t0.children), ctx)
            return t0
        if t0.value in COMMANDS:
            return self.run_cmd(t0.code[t0.start : tokens[-1].end], ctx)
        if tokens[1].value in INC_OP:
            name = t0.name.value if isinstance(t0,SelectorIdentifierToken) else t0.value
            score = f"{t0.selector.value} {name}" if isinstance(t0, SelectorIdentifierToken) else name+  " global"
            if name not in self.variables:
                raise_syntax_error("Undefined variable", t0)

            var_type = self.variables[name].type
            action = "add" if tokens[1].value == "++" else "remove"
            inc = FLOAT_PREC if var_type == "float" else 1
            id = get_expr_id()
            eid = var_type + "_" + str(id)
            file.append(
                f"scoreboard players operation {eid} --temp-- = {score}"
            )
            file.append(f"scoreboard players {action} {score} {inc}")
            return eid
        if t0.value in SET_OP:
            t1 = tokens[1]
            name = (
                t1.name.value
                if isinstance(t1, SelectorIdentifierToken)
                else t1.value
            )
            target_score = (
                f"{t1.selector.value} {name}"
                if isinstance(t1, SelectorIdentifierToken)
                else f"{name} global"
            )
            expr = tokens[2:]
            if t0.value != "=" and name not in self.variables:
                raise_syntax_error("Undefined variable", tokens[1])

            exist_type = (
                None
                if t0.value == "=" and name not in self.variables
                else self.variables[name].type
            )
            if len(expr) == 1 and expr[0].type in [
                TokenType.IDENTIFIER,
                TokenType.SELECTOR_IDENTIFIER,
            ]:
                (loc, var_type) = self.__get_var_loc(expr[0], ctx)
                if exist_type and exist_type != var_type:
                    raise_syntax_error(
                        f"Variable was defined to be {exist_type}, got {var_type}",t1
                    )
                file.append(
                    f"scoreboard players operation {target_score} = {loc}"
                )
                id = get_expr_id()
                eid = f"{var_type}_{id}"
                file.append(f"scoreboard players operation {eid} --temp-- = {loc}")
                if name not in self.variables:
                    self.files["__load__"].append(
                        f'scoreboard objectives add {name} dummy ""'
                    )
                    self.variables[name] = VariableDeclaration(var_type,False)
                return eid
            score = self.transpile_expr(expr, ctx)
            var_type = _get_score_type(score)
            if exist_type and exist_type != var_type:
                if isinstance(score, int):
                    score = float(score)
                elif isinstance(score, float):
                    score = int(score)
                else:
                    if score.startswith("float_"):
                        file.append(
                            f"scoreboard players operation {score} --temp-- /= FLOAT_PREC --temp--"
                        )
                    else:
                        file.append(
                            f"scoreboard players operation {score} --temp-- *= FLOAT_PREC --temp--"
                        )

                var_type = exist_type

            action = "add" if t0.value[0] == "+" else "remove"
            if isinstance(score, int):
                if t0.value == "=":
                    file.append(f"scoreboard players set {target_score} {score}")
                elif exist_type: # linter wants this
                    file.extend(
                        _compute(
                            target_score,
                            score,
                            exist_type[0],
                            t0.value[0],
                            "li",
                        )
                    )
            elif isinstance(score, float):
                if t0.value == "=":
                    file.append(
                        f"scoreboard players set {target_score} {int(score * FLOAT_PREC)}"
                    )
                elif exist_type: # linter wants this
                    file.extend(
                        _compute(
                            target_score,
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
                        f"scoreboard players operation {target_score} = {score} --temp--"
                    )
                elif exist_type: # linter wants this
                    file.extend(
                        _compute(
                            target_score,
                            f"{score} --temp--",
                            exist_type[0],
                            t0.value[0],
                            var_type[0],
                        )
                    )

            if name not in self.variables:
                self.files["__load__"].append(
                    f'scoreboard objectives add {name} dummy ""'
                )

                self.variables[name] = VariableDeclaration(var_type, False)
            return score
        stack = []
        for token in tokens:
            if token.type != TokenType.OPERATOR:
                stack.append(token)
                continue

            right = stack.pop()
            left = stack.pop()

            if isinstance(right, GroupToken) and right.type == TokenType.GROUP:
                right = self._transpile_expr(make_expr(right.children), ctx)
            if isinstance(left, GroupToken) and left.type == TokenType.GROUP:
                left = self._transpile_expr(make_expr(left.children), ctx)

            # right,left = number_literal, identifier, group or a score

            ri = isinstance(right, Token)
            rl = isinstance(left, Token)

            if (
                ri
                and rl
                and (
                    right.type == TokenType.INT_LITERAL # type: ignore
                    or right.type == TokenType.FLOAT_LITERAL # type: ignore
                )
                and (
                    left.type == TokenType.INT_LITERAL # type: ignore
                    or left.type == TokenType.FLOAT_LITERAL # type: ignore
                )
            ):
                n = str(eval(f"{left.value}{token.value}{right.value}")) # type: ignore
                type = (
                    TokenType.FLOAT_LITERAL
                    if right.type == TokenType.FLOAT_LITERAL # type: ignore
                    or left.type == TokenType.FLOAT_LITERAL # type: ignore
                    else TokenType.INT_LITERAL
                )
                stack.append(Token(n, type, 0, len(n)))
                continue

            lt = self.__get_expr_type(left, ctx)
            rt = self.__get_expr_type(right, ctx)

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
                _lt += " --temp--" # type: ignore
            rf = "i"
            if isinstance(rt, int):
                rf = "li"
            elif isinstance(rt, float):
                rf = "lf"
            elif rt.startswith("float_"):
                rf = "f"
            if rf[0] != "l":
                _rt += " --temp--" # type: ignore

            file.extend(_compute(_lt, _rt, lf, token.value, rf))

            stack.append(lt if rf[0] == "l" else rt)

        return stack[-1]

    def get_expr_loc(self, tokens, ctx: TranspilerContext):
        is_var = len(tokens) == 1 and tokens[0].type in {
            TokenType.IDENTIFIER,
            TokenType.SELECTOR_IDENTIFIER,
        }
        if is_var:
            return self.__get_var_loc(tokens[0], ctx)

        r = self.transpile_expr(tokens, ctx)
        if isinstance(r, str):
            return (r + " --temp--", "float" if r.startswith("float_") else "int")
        return (r, "float" if isinstance(r, float) else "int")

    def transpile_expr(self, tokens: List[Token], ctx: TranspilerContext):
        tokens = make_expr(tokens)
        r = self._transpile_expr(tokens, ctx)
        if isinstance(r, Token):
            if r.type == TokenType.INT_LITERAL:
                return int(r.value)
            if r.type == TokenType.FLOAT_LITERAL:
                return float(r.value)
            if not isinstance(r, GroupToken):
                raise ValueError("Invalid expression")
            return self.transpile_expr(r.children, ctx)
        return r

    def exec_if(self, condition, ctx:TranspilerContext):
        file = ctx.file
        function = ctx.function
        # [ [ LeftToken[], Operator, RightToken[] ], AndOrOperator, [ LeftToken[], Operator, RightToken[] ], ... ]
        cmp_list = self.split_cmp(condition)
        if len(cmp_list) == 1:
            # compute single comparison
            left = cmp_list[0][0]
            op = cmp_list[0][1].value
            right = cmp_list[0][2]

            lt = self._get_expr_direct(left, ctx)
            rt = self._get_expr_direct(right, ctx)

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

    def add_lib_file(self, path: str):
        self.add_mcfunction_file("__lib__/" + path, f"builtin/{path}.mcfunction")

    def add_mcfunction_file(self, save: str, path: str):
        self.files[save] = get_lib_contents(path).split("\n")
    
    def init_lib_file(self,path:str):
        if path not in self.init_libs:
            self.add_lib_file(path)
            self.init_libs.append(path)
            self.mainFile.append(f"function $PACK_NAME$:{path}")
