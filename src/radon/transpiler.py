import json
import os
import sys
from typing import Any, Dict, List, Union, Literal

from .dp_ast import (
    ENDERS,
    ContinueStatement,
    DefineClassStatement,
    DefineFunctionStatement,
    ExecuteMacroStatement,
    IfFlowStatement,
    ImportStatement,
    InlineStatement,
    IntroduceVariableStatement,
    LoopStatement,
    ReturnStatement,
    ScheduleStatement,
    Statement,
    StatementType,
    COMMANDS,
    chain_tokens,
    make_expr,
    parse_str, parse
)
from .error import raise_syntax_error, raise_syntax_error_t, show_warning
from .tokenizer import (
    BlockIdentifierToken,
    GroupToken,
    SelectorIdentifierToken,
    Token,
    SET_OP,
    INC_OP,
    CMP_OP,
    CMP_COMBINE_OP,
    cpl_def_from_tokens,
    split_tokens,
    tokenize
)
from .utils import (
    INT_TYPE,
    CplDef,
    VariableDeclaration,
    TokenType,
    FLOAT_PREC,
    get_expr_id,
    INT_LIMIT,
    FLOAT_LIMIT, CplDefArray, reset_expr_id
)

cwd = os.path.dirname(os.path.abspath(sys.argv[0]))
if sys.argv[0] == "":
    cwd = "/home/pyodide"


def get_lib_contents(path: str):
    with open(cwd + "/" + path, "r") as f:
        return f.read()


def _get_score_type(score):
    if isinstance(score, int):
        return "int"
    elif isinstance(score, float):
        return "float"
    return "float" if score.startswith("float_") else "int"


def transpile_str(code: str):
    (statements, macros) = parse_str(code)

    return Transpiler(statements, macros)


def split_cmp(expr: List[Token]):
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
            sn1 = spl[-1]
            if isinstance(sn1, list):
                sn1[1] = t
        else:
            spl[-1][spl_ci].append(t)
    return spl


class FunctionArgument:
    def __init__(self, name, store, store_via):
        # type: (str, CplScore | CplNBT, str) -> None
        self.name = name
        self.unique_type = store.unique_type.content if store_via in {"stack", "macro"} else store.unique_type
        self.store = store
        self.store_via = store_via  # set, stack, macro


class LoopDeclaration:
    def __init__(self, eid: str, file: List[str], file_path: str, continue_: str):
        self.eid = eid
        self.file = file
        self.file_path = file_path
        self.continue_ = continue_


def args_to_str(arguments):
    arg_s = []
    for arg in arguments:
        arg_s.append(str(arg.unique_type))
    return ", ".join(arg_s)


class FunctionDeclaration:
    def __init__(
            self,
            type: Literal["radon", "mcfunction", "python", "python-cpl", "python-raw"],
            name: str,
            returns="void",  # type: CplScore | CplNBT | str
            arguments: List[FunctionArgument] = None,
            function: Any = None,
            file_name: str = "",
            class_name: str | None = None
    ):
        if arguments is None:
            arguments = []
        self.type = type
        self.name = name
        self.file_name = file_name
        self.returns = returns
        self.arguments: List[FunctionArgument] = arguments
        self.argumentsStr = args_to_str(arguments)
        self.function = function
        self.class_name = class_name


class ClassDeclaration:
    def __init__(
            self,
            name: str,
            attributes,  # type: CplObject
            methods: List[FunctionDeclaration],
            sample  # type: CplObjectNBT
    ):
        self.id = get_expr_id()
        self.name = name
        self.attributes = attributes
        self.methods = methods
        self.sample = sample


class TranspilerContext:
    def __init__(
            self,
            transpiler,  # type: Transpiler
            file_name: str,
            file: List[str],
            function: FunctionDeclaration | None = None,
            loop: LoopDeclaration | Any | None = None,
            class_name: str | None = None
    ):
        self.transpiler = transpiler
        self.file_name = file_name
        self.file = file
        self.function = function
        self.loop = loop
        self.class_name = class_name


from .cpl.base import CompileTimeValue
from .cpl.int import CplInt
from .cpl.float import CplFloat
from .cpl.string import CplString
from .cpl.array import CplArray
from .cpl.tuple import CplTuple
from .cpl.object import CplObject
from .cpl.score import CplScore
from .cpl.selector import CplSelector
from .cpl.nbt import CplNBT, val_nbt
from .cpl.nbtobject import CplObjectNBT


def _type_to_cpl(
        token: Token, type: CplDef, score_loc: str, nbt_loc: str, force_nbt: bool = False
) -> Union[CplScore, CplNBT]:
    if force_nbt or type.type in {"string", "array", "object"}:
        return val_nbt(token, nbt_loc, type)
    return CplScore(token, score_loc, type.type)


TRUE_VALUE = CplScore(Token("true", TokenType.IDENTIFIER, 0, 4), "true global", "int")
FALSE_VALUE = CplScore(
    Token("false", TokenType.IDENTIFIER, 0, 5), "false global", "int"
)
NULL_VALUE = CplScore(Token("null", TokenType.IDENTIFIER, 0, 4), "null global", "int")

builtin: Dict[str, List[FunctionDeclaration]] = {}


def add_lib(lib):
    if lib.name in builtin:
        builtin[lib.name].append(lib)
    else:
        builtin[lib.name] = [lib]


from .builtin.math import _ as ___0
from .builtin.print import _ as ___1
from .builtin.pyeval import _ as ___2
from .builtin.time import _ as ___3
from .builtin.swap import _ as ___4

# IF YOU HATE PYTHON AND YOU KNOW IT CLAP YOUR HANDS! 👏 👏 👏
____ = ___0 + ___1 + ___2 + ___3 + ___4


class Transpiler:
    def __init__(self, statements: List[Statement], macros: List[Statement], pack_namespace: str = "mypack",
                 pack_description: str = "", pack_format: int = 48, main_dir: str = "./") -> None:
        reset_expr_id()
        self.files = dict()
        self.pack_namespace = pack_namespace
        self.pack_description = pack_description
        self.pack_format = pack_format
        self.main_dir = main_dir
        self.variables: Dict[str, VariableDeclaration] = dict()
        self.functions: List[FunctionDeclaration] = []
        self.classes: Dict[str, ClassDeclaration] = dict()
        self.loops: Dict[Any, LoopDeclaration] = dict()
        self.init_libs = []
        self.data = dict()
        self.main_file = []
        self.tempFiles: Dict[str, str] = dict()

        if len(statements) == 0:
            self.files = {}
            return
        self.macros = macros
        load_file = [
            "# Setup #",
            "",
            'scoreboard objectives add __temp__ dummy "__temp__"',
            'scoreboard objectives add global dummy "global"',
            'scoreboard objectives add __break__ dummy "__break__"',
            'scoreboard objectives add __continue__ dummy "__continue__"',
            "scoreboard players set null __temp__ 0",
            "scoreboard players set FLOAT_PREC __temp__ " + str(FLOAT_PREC),
            "scoreboard players set true global 1",
            "scoreboard players set false global 0",
            "scoreboard players set null global 0",
        ]
        self.files["__load__"] = load_file
        self.load_file = load_file
        self.variables["false"] = VariableDeclaration(INT_TYPE, False)
        self.variables["true"] = VariableDeclaration(INT_TYPE, False)
        self.variables["null"] = VariableDeclaration(INT_TYPE, False)
        main_file = []
        self.main_file = main_file
        self._transpile(
            TranspilerContext(
                transpiler=self,
                file_name="__main__",
                file=main_file,
                function=None,
                loop=None),
            statements
        )
        load_file.append("")
        load_file.append("# Main File #")
        load_file.append("")
        load_file += main_file

        # remove the lines after immediate returns
        for file in self.files:
            if not file.endswith(".mcfunction"):
                continue
            lines = self.files[file]
            if len(lines) == 0:
                continue
            index = 0
            for index, line in enumerate(lines):
                if line.startswith("return"):
                    break
            self.files[file] = lines[: index + 1]

    def get_datapack_files(self):
        fn_folder = "function" if self.pack_format >= 48 else "functions"
        dp_files = dict()
        for file in self.files:
            dp_files[f"data/{self.pack_namespace}/{fn_folder}/{file}.mcfunction"] = "\n".join(self.files[file])
        dp_files["pack.mcmeta"] = json.dumps({
            "pack": {
                "pack_format": self.pack_format,
                "description": self.pack_description,
            }
        }, indent=2)
        dp_files[f"data/minecraft/tags/{fn_folder}/load.json"] = json.dumps(
            {
                "values": [f"{self.pack_namespace}:__load__"]
            }, indent=2)
        if "tick" in self.files:
            with open(
                    f"data/minecraft/tags/{fn_folder}/tick.json", "w"
            ) as file:
                file.write(
                    json.dumps(
                        {"values": [f"{self.pack_namespace}:tick"]}, indent=2
                    )
                )
        return dp_files

    def get_temp_file_name(self, content: str | List[str]):
        if isinstance(content, list):
            content = "\n".join(content)
        if content in self.tempFiles:
            return self.tempFiles[content]
        file_name = f"__temp__/{get_expr_id()}"
        self.tempFiles[content] = file_name
        self.files[file_name] = content.split("\n")
        return file_name

    def _transpile(self, ctx: TranspilerContext, statements: List[Statement]):
        for statement in statements:
            if isinstance(statement, DefineClassStatement):
                if ctx.function or ctx.loop:
                    raise_syntax_error(
                        "Classes should be declared in the main scope", statement
                    )
                name = statement.name.value
                if name in self.classes or name in self.functions:
                    raise_syntax_error(f"Class {name} is already defined", statement)
                base_object = CplObject(statement.name, dict(), name)
                for (attr_name, attr_expr) in statement.attributes:
                    cpl = self.tokens_to_cpl(ctx, attr_expr)
                    base_object.value[attr_name] = cpl
                    base_object.unique_type.content[attr_name] = cpl.unique_type
                sample: CplObjectNBT = base_object.cache(ctx, nbt_loc=f"storage class_sample {name}",  # type: ignore
                                                         force="nbt")

                class_ctx = TranspilerContext(
                    transpiler=self,
                    file_name=ctx.file_name,
                    file=ctx.file,
                    function=None,
                    loop=None,
                    class_name=name
                )

                methods = []
                has_init = False
                cls = ClassDeclaration(name, base_object, methods, sample)
                self.classes[name] = cls
                for mt in statement.methods:
                    if mt.name.value == name:
                        has_init = True
                    args = self._chains_to_args(mt.arguments)
                    fn_dec = FunctionDeclaration(
                        type="radon",
                        name=name + "." + mt.name.value,
                        returns="auto",
                        arguments=args,
                        file_name=statement.name.value,
                        function="replace me"
                    )
                    self.functions.append(fn_dec)
                    methods.append(fn_dec)

                new_methods = []

                for mt in statement.methods:
                    self._transpile(class_ctx, [mt])
                    new_methods.append(self.functions[-1])
                cls.methods = new_methods

                if not has_init:
                    self._transpile(class_ctx, parse(
                        tokenize("fn " + name + "() {}")[0],
                        [], list(self.classes.keys())))
                    methods.append(self.functions[-1])
                continue
            if isinstance(statement, ImportStatement):
                raise_syntax_error("Imports are not yet implemented.", statement)
                if statement.as_ is None:
                    pass
                else:
                    # TODO: add imports
                    """save = str(get_expr_id())
                    path = statement.path.value[1:-1]
                    
                    self.add_mcfunction_file(save, path)
                    self.functions.append(
                        FunctionDeclaration(
                            type="mcfunction",
                            name=statement._as.value,
                            file_name=save,
                            returns="int",
                            arguments=[],
                        )
                    )"""
                continue
            if isinstance(statement, ScheduleStatement):
                file_name = self._run_safe("__schedule__", statement.body, ctx)
                ctx.file.append(
                    f"schedule function {self.pack_namespace}:{file_name} {statement.time.value} replace"
                )
                _return_safe(ctx)
                continue
            if statement.type == StatementType.BREAK:
                if not ctx.loop:
                    raise_syntax_error("Cannot use break outside of loop", statement)
                if ctx.file is ctx.loop.file:
                    ctx.file.append("return 0")
                else:
                    loop_id = ctx.loop.eid
                    ctx.file.append(f"scoreboard players set {loop_id} __break__ 1")
                    ctx.file.append(f"return 0")
                continue
            if isinstance(statement, ContinueStatement):
                if not ctx.loop:
                    raise_syntax_error("Cannot use continue outside of loop", statement)
                if ctx.file is ctx.loop.file:
                    ctx.file.append(ctx.loop.continue_)
                    ctx.file.append("return 0")
                else:
                    loop_id = ctx.loop.eid
                    ctx.file.append(f"scoreboard players set {loop_id} __continue__ 1")
                    ctx.file.append(f"return 0")
                continue
            if isinstance(statement, LoopStatement):
                file_name = self._run_safe(
                    "__loop__",
                    statement.body,
                    TranspilerContext(
                        transpiler=self,
                        file_name=ctx.file_name,
                        file=ctx.file,
                        function=ctx.function,
                        loop=statement)
                )
                ctx.file.append(f"function {self.pack_namespace}:{file_name}")
                loop_file = self.files[file_name]
                loop_id = int(file_name.split("/")[-1])
                loop_file.insert(0, f"scoreboard players set {loop_id} __break__ 0")
                loop_file.insert(0, f"scoreboard players set {loop_id} __continue__ 0")
                loop_c = self.loops[loop_id]
                loop_file.append(loop_c.continue_)
                continue
            if isinstance(statement, IfFlowStatement):
                has_if = len(statement.body) != 0
                has_else = statement.elseBody and len(statement.elseBody) != 0
                if not has_if and not has_else:
                    continue
                resp = self.tokens_to_cpl(ctx, statement.condition)
                if (
                        isinstance(resp, CplInt)
                        or isinstance(resp, CplFloat)
                        or (resp.unique_type.type not in {"int", "float"} and not isinstance(resp, CplSelector))):
                    is_true = (not isinstance(resp, CplInt) and not isinstance(resp, CplFloat)) or resp.value != 0
                    if is_true:
                        if not has_if:
                            continue
                        self._transpile(ctx, statement.body)
                    elif (
                            has_else and statement.elseBody
                    ):  # I know this is bad, but the linter wants it (statement.elseBody)
                        self._transpile(ctx, statement.elseBody)
                    continue
                if isinstance(resp, CplNBT):
                    resp = resp.cache(ctx, force="score")
                if isinstance(resp, CplScore):
                    if_cmd = f"execute unless score {resp.location} matches 0..0 run "
                    unless_cmd = f"execute if score {resp.location} matches 0..0 run "
                elif isinstance(resp, CplSelector):
                    if_cmd = f"execute if entity {resp.value} run "
                    unless_cmd = f"execute unless entity {resp.value} run "
                else:
                    raise SyntaxError("Invalid condition")
                has_one = (has_if or has_else) and (not has_if or not has_else)
                if has_one:
                    one_body = statement.body if has_if else statement.elseBody
                    i_cmd = if_cmd if has_if else unless_cmd
                    if (
                            ctx.loop
                            and one_body
                            and ctx.loop.file is ctx.file
                            and len(one_body) == 1
                            and one_body[0].type == StatementType.BREAK
                    ):
                        ctx.file.append(f"{i_cmd}return 0")
                        continue

                if has_if:
                    if_name = self._run_safe("__if__", statement.body, ctx)
                    ctx.file.append(f"{if_cmd}function {self.pack_namespace}:{if_name}")
                if has_else:
                    else_name = self._run_safe("__else__", statement.elseBody, ctx)
                    ctx.file.append(f"{unless_cmd}function {self.pack_namespace}:{else_name}")
                _return_safe(ctx)
                continue
            if isinstance(statement, InlineStatement):
                expr_tokens = statement.exprTokens
                ret = self.tokens_to_cpl(ctx, expr_tokens)
                if isinstance(ret, CplScore):
                    # Cleaning the return results of the inline expression since they aren't going to be used
                    cl1 = f"scoreboard players operation {ret.location} = "
                    cl2 = f"execute store result score {ret.location} run "
                    cl3 = f"execute store result score {ret.location} run data get"
                    cl4 = f"execute store result score {ret.location} run scoreboard players get"
                    if len(ctx.file) > 0 and (
                            ctx.file[-1].startswith(cl1)
                            or ctx.file[-1].startswith(cl3)
                            or ctx.file[-1].startswith(cl4)
                    ):
                        ctx.file.pop()
                        continue
                    if len(ctx.file) > 0 and ctx.file[-1].startswith(cl2):
                        ctx.file[-1] = ctx.file[-1][len(cl2):]
                if isinstance(ret, CplNBT) and ret.location.startswith("storage temp "):
                    # Cleaning the return results of the inline expression since they aren't going to be used
                    cl1 = f"data modify {ret.location} set from"
                    if len(ctx.file) > 0 and ctx.file[-1].startswith(cl1):
                        ctx.file.pop()
                        continue
                    if len(ctx.file) > 1 and ctx.file[-2].startswith(cl1) and ret.location not in ctx.file[-1]:
                        ctx.file.pop(-2)
                        continue
                continue
            if isinstance(statement, DefineFunctionStatement):
                if ctx.function or ctx.loop:
                    raise_syntax_error(
                        "Functions should be declared in the main scope", statement
                    )
                fn_name = statement.name.value
                if ctx.class_name is not None and fn_name != ctx.class_name:
                    fn_name = f"{ctx.class_name}.{fn_name}"
                arguments: List[FunctionArgument] = self._chains_to_args(statement.arguments)
                ret = (
                    cpl_def_from_tokens(self.classes, statement.returns)
                    if not isinstance(statement.returns, str)
                    else statement.returns
                )
                if ret is None:
                    raise_syntax_error("Invalid return type for a function", statement)
                    raise SyntaxError("")
                ret_loc = ret
                if isinstance(ret_loc, CplDef):
                    assert isinstance(statement.returns, list)
                    assert isinstance(ret, CplDef)
                    eid = get_expr_id()
                    ret_loc = _type_to_cpl(
                        statement.returns[0],
                        ret,
                        score_loc=f"fn_return_{eid} __temp__",
                        nbt_loc=f"storage fn_return _{eid}",
                    )
                is_class_init = fn_name == ctx.class_name
                if is_class_init:
                    if isinstance(statement.returns, list) and len(statement.returns) > 0:
                        raise_syntax_error("Class initializers cannot have return types", statement.returns[0])
                    cls = self.classes[fn_name]
                    ret_loc = CplObjectNBT(statement.name, f"storage fn_return _{get_expr_id()}",
                                           cls.attributes.unique_type)
                types = args_to_str(arguments)
                count = 0
                new_functions = []
                for f in self.functions:
                    if fn_name == f.name:
                        count += 1
                        if types == f.argumentsStr:
                            if f.function == "replace me":
                                count -= 1
                                continue
                            raise_syntax_error(
                                "Function with the same name and arguments already exists",
                                statement.name
                            )
                    new_functions.append(f)
                self.functions.clear()
                self.functions.extend(new_functions)
                file_name = statement.name.value.lower()
                if ctx.class_name is not None:
                    cls = self.classes[ctx.class_name]
                    file_name = "__class__/" + cls.name.lower() + "_" + file_name
                base_file_name = file_name
                file_name_counter = 0
                while file_name in self.files:
                    file_name_counter += 1
                    file_name = base_file_name + str(file_name_counter)
                f = FunctionDeclaration(
                    type="radon",
                    name=fn_name,
                    returns=ret_loc,
                    arguments=arguments,
                    file_name=file_name,
                    class_name=ctx.class_name
                )

                self.functions.append(f)
                fn_file = []
                self.files[file_name] = fn_file
                for index, arg in enumerate(arguments):
                    if arg.store_via == "macro":
                        t = arg.store.unique_type.content  # type: CplDef
                        macro = f"$({arg.store.location.split(' ')[-1]})"
                        if t.type == "string":
                            macro = f'"{macro}"'
                        fn_file.append(f"$data modify {arg.store.location} append value {macro}")
                self._transpile(
                    TranspilerContext(
                        transpiler=self,
                        file_name=file_name,
                        file=fn_file,
                        function=f,
                        loop=ctx.loop,
                        class_name=ctx.class_name),
                    statement.body
                )
                if f.returns == "auto":
                    f.returns = "void"
                if f.returns != "void":
                    fn_file.insert(0, f"scoreboard players set __returned__ __temp__ 0")
                continue
            if isinstance(statement, ReturnStatement):
                if not ctx.function:
                    raise_syntax_error(
                        "Cannot use return keyword outside functions", statement
                    )
                    continue
                expr_tokens = statement.exprTokens
                if ctx.function.returns == "void" and len(expr_tokens) != 0:
                    raise_syntax_error(
                        f"Function cannot return a value because it has a void return type",
                        statement,
                    )
                if ctx.function.returns != "void":
                    cpl = self.tokens_to_cpl(ctx, expr_tokens)
                    if ctx.function.returns == "auto":
                        if not isinstance(cpl, CplScore) and not isinstance(cpl, CplNBT):
                            cpl = cpl.cache(ctx)
                        ctx.function.returns = cpl
                    elif not isinstance(ctx.function.returns, str):
                        if cpl.unique_type != ctx.function.returns.unique_type:
                            raise_syntax_error(
                                f"Function has a return type of {ctx.function.returns.unique_type}, "
                                f"but a {cpl.unique_type} was returned",
                                statement
                            )
                        ctx.function.returns._set(ctx, cpl)

                if ctx.file is not self.files[ctx.function.file_name]:
                    ctx.file.append(f"scoreboard players set __returned__ __temp__ 1")
                ctx.file.append(f"return 0")
                if ctx.file is self.files[ctx.function.file_name]:
                    return
            if isinstance(statement, IntroduceVariableStatement):
                name = statement.name.value
                if name in self.variables:
                    raise_syntax_error("Variable is already introduced", statement)
                type_v = cpl_def_from_tokens(self.classes, statement.varType)
                if not type_v:
                    raise_syntax_error(f"Invalid type", statement)
                    raise SyntaxError("")
                self.variables[name] = VariableDeclaration(type_v, False)
                self.load_file.append(
                    f'scoreboard objectives add {name} dummy "{name}"'
                )
                self.load_file.append(
                    f"scoreboard players enable {name} global"
                )
                continue
            if isinstance(statement, ExecuteMacroStatement):
                exec_name = self._run_safe("__execute__", statement.body, ctx)
                ctx.file.append(
                    f"execute {statement.command} run function {self.pack_namespace}:{exec_name}"
                )
                _return_safe(ctx)
                continue
            raise_syntax_error("Invalid statement", statement)

    def _run_safe(self, folder_name, statements, ctx: TranspilerContext):
        eid = get_expr_id()
        file_name = f"{folder_name}/{eid}"
        new_file = []
        loop = ctx.loop
        if isinstance(loop, LoopStatement):
            continue_ = f"function {self.pack_namespace}:{file_name}"
            if loop.time:
                continue_ = f"schedule function {self.pack_namespace}:{file_name} {loop.time.value} replace"
            loop = LoopDeclaration(
                eid=eid,
                file=new_file,
                file_path=file_name,
                continue_=continue_
            )
            self.loops[eid] = loop
        self.files[file_name] = new_file
        self._transpile(
            TranspilerContext(
                transpiler=self,
                file_name=file_name,
                file=new_file,
                function=ctx.function,
                loop=loop), statements
        )
        return file_name

    def _chains_to_args(self, chains: List[List[List[Token]]]):
        arg_names = []
        arguments = []
        for arg in chains:
            store_via = "stack"
            if len(arg) > 0 and arg[0][0].value == "$":
                store_via = "macro"
                arg = arg[1:]
            if len(arg) != 2 or arg[1][0].type != TokenType.IDENTIFIER:
                raise_syntax_error("Invalid argument for a function", arg[0][0])
            arg_type_parsed = cpl_def_from_tokens(self.classes, arg[0])
            if arg_type_parsed is None:
                raise_syntax_error("Invalid argument type for a function", arg[0][0])
                raise SyntaxError("")
            arg_name = arg[1][0].value
            if arg_name in arg_names:
                raise_syntax_error("Argument name is already used", arg[1][0])
            eid = get_expr_id()
            arguments.append(
                FunctionArgument(
                    arg_name,
                    _type_to_cpl(
                        arg[0][0],
                        CplDefArray(arg_type_parsed) if store_via in {"stack", "macro"} else arg_type_parsed,
                        score_loc="",
                        nbt_loc=f"storage fn_args {arg_name}",
                        force_nbt=True
                    ),
                    store_via=store_via
                )
            )
        return arguments

    def run_cmd(self, pointer: Token, ctx: TranspilerContext) -> CompileTimeValue:
        file = ctx.file
        cmd = pointer.value
        cmd_str = ""
        i = 0
        has_repl = False
        repl_i = 0
        cmd = " ".join(s[:-1] if s[-1] == "\\" else s for s in cmd.strip().split("\n"))
        while i < len(cmd):
            if cmd[i: i + 3] == "\\$(":
                if self.pack_format < 18:
                    raise_syntax_error_t(
                        f"Macros are not supported in the pack format {self.pack_format}. "
                        f"Consider using a version > (17 or 1.20.1 or 23w35a)",
                        cmd,
                        i,
                        i + 3,
                    )
                cmd_str += "$("
                i += 3
                continue
            if (
                    cmd[i: i + 2] == "$("
                    or cmd[i: i + 5] == "$str("
                    or cmd[i: i + 5] == "$jstr("
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
                repl = cmd[si + (2 if cmd[si + 1] == "(" else 5): i]
                (expr_tokens, _) = tokenize(repl)
                expr_tokens = expr_tokens[:-1]
                val = self.tokens_to_cpl(ctx, expr_tokens)

                if cmd[si + 1] == "(":
                    cmd_str += f"$(_{repl_i})"
                    val.cache(
                        ctx, nbt_loc=f"storage cmd_mem _{repl_i}", force="nbt"
                    )

                    has_repl = True
                    repl_i += 1

                elif cmd[si + 1] == "s":
                    cmd_str += val.tellraw_object(ctx)
                elif cmd[si + 1] == "j":
                    cmd_str += json.dumps(val.tellraw_object(ctx))

                i += 1
                continue
            cmd_str += cmd[i]
            i += 1

        eid = ("int_" + str(get_expr_id()) + " __temp__")  # TODO: Does it have to be an int? Can I allow floats?
        eid_val = CplScore(pointer, eid, "int")

        if not has_repl:
            file.append(f"execute store result score {eid} run {cmd_str}")
            return eid_val

        cmd_file = []
        file_name = None
        for i in self.files:
            if "\n".join(self.files[i]) == "\n".join(cmd_file):
                file_name = i
                break
        if file_name is None:
            cmd_id = get_expr_id()
            file_name = f"__cmd__/{cmd_id}"
        self.files[file_name] = cmd_file
        cmd_file.append("$" + cmd_str)
        file.append(
            f"execute store result score {eid} run function {self.pack_namespace}:{file_name} with storage cmd_mem"
        )
        return eid_val

    def _nbt_var_loc(self, ctx: TranspilerContext, token: Token) -> str:
        if isinstance(token, SelectorIdentifierToken):
            return f"entity {token.selector.value} {token.name.value}"
        if isinstance(token, BlockIdentifierToken):
            spl = split_tokens(token.block.children, ",")
            if len(spl) != 3:
                raise_syntax_error("Invalid block identifier", token)
                raise ValueError("")
            pos: List[str] = []
            for s in spl:
                sym = ""
                if s[0].value in {"~", "^"}:
                    sym = s[0].value
                    s = s[1:]
                cpl = self.tokens_to_cpl(ctx, s)
                if not isinstance(cpl, CplInt) and not isinstance(cpl, CplFloat):
                    raise_syntax_error(
                        f"Block identifier's position has to have 3 literal numbers", token
                    )
                    raise SyntaxError("")
                pos.append(sym + str(cpl.value))
            return f"block {' '.join(pos)} {token.name.value}"
        raise ValueError("Invalid token")

    def _var_to_cpl_or_none(
            self, ctx: TranspilerContext, t: Token
    ) -> Union[CplScore, CplNBT, None]:
        if isinstance(t, SelectorIdentifierToken):
            name = t.name.value
            if name not in self.variables:
                return None
            var = self.variables[name]
            var_type = var.type
            return _type_to_cpl(
                t,
                var_type,
                score_loc=f"",
                nbt_loc=self._nbt_var_loc(ctx, t),
                force_nbt=True  # for now
            )
        if isinstance(t, BlockIdentifierToken):
            name = t.name.value
            if name not in self.variables:
                return None
            var = self.variables[name]
            var_type = var.type
            val = _type_to_cpl(
                t,
                var_type,
                score_loc="",
                nbt_loc=self._nbt_var_loc(ctx, t),
                force_nbt=True
            )
            return val
        if t.type == TokenType.IDENTIFIER:
            name = t.value
            if name not in self.variables:
                if ctx.function and ctx.class_name is not None and name == "this":
                    return CplObjectNBT(t, f"storage class this[-1]",
                                        self.classes[ctx.class_name].sample.unique_type)
                if ctx.function:
                    fn = ctx.function
                    found = None
                    for arg in fn.arguments:
                        if arg.name == name:
                            found = arg
                            break
                    if found:
                        if found.store_via in {"stack", "macro"}:
                            return val_nbt(found.store.token, found.store.location + "[-1]",
                                           found.store.unique_type.content)
                        return found.store
                return None

            var = self.variables[name]
            var_type = var.type
            if var.constant:
                return var.value
            return _type_to_cpl(
                t,
                var_type,
                score_loc=f"{name} global",
                nbt_loc=f"storage variables {name}",
            )
        raise SyntaxError("")

    def variable_token_to_cpl(
            self, ctx: TranspilerContext, t: Token
    ) -> Union[CplScore, CplNBT]:
        res = self._var_to_cpl_or_none(ctx, t)
        if res is None:
            raise_syntax_error("Variable not found", t)
            raise SyntaxError("")
        return res

    def chain_to_cpl(self, ctx: TranspilerContext, t: List[Token]):
        cpl = self.token_to_cpl(ctx, t[0])
        for token in t[1:]:
            if token.type == TokenType.IDENTIFIER:
                cpl = cpl.get_index(ctx, CplString(token, token.value))
                continue
            if token.type == TokenType.INT_LITERAL:
                cpl = cpl.get_index(ctx, CplInt(token, token.value))
                continue
            if isinstance(token, GroupToken):
                if token.open.value == "[":
                    if len(token.children) == 0:
                        raise_syntax_error("A bracket index has to include an expression inside.", token)
                        assert False
                    spl = list(map(lambda x: self.tokens_to_cpl(ctx, x) if len(x) > 0 else None,
                                   split_tokens(token.children, ":", comma_errors=False)))
                    if len(spl) == 1:
                        cpl = cpl.get_index(ctx, spl[0])
                        continue
                    if len(spl) > 3:
                        raise_syntax_error("A slice can only include two colons.", token)
                        assert False
                    while len(spl) < 3:
                        spl.append(None)
                    if spl[0] is None:
                        spl[0] = CplInt(token, 0)
                    if spl[1] is None:
                        spl[1] = CplInt(token, -1)
                    if spl[2] is None:
                        spl[2] = CplInt(token, 1)

                    cpl = cpl.get_slice(ctx, spl[0], spl[1], spl[2])
                    continue
                if token.func:
                    args = list(map(lambda x: self.tokens_to_cpl(ctx, x), split_tokens(token.children, ",")))
                    cpl = cpl.call_index(ctx, token.func.value, args)
                    continue
            raise_syntax_error(f"Cannot index with the token", token)
        return cpl

    def token_to_cpl(self, ctx: TranspilerContext, t: Token):
        if t.type == TokenType.INT_LITERAL:
            if abs(int(t.value)) > INT_LIMIT:
                raise_syntax_error(
                    f"An integer literal cannot be larger than {INT_LIMIT}", t
                )
            return CplInt(t, t.value)
        if t.type == TokenType.FLOAT_LITERAL:
            if abs(float(t.value)) > FLOAT_LIMIT:
                raise_syntax_error(
                    f"A float literal cannot be larger than {FLOAT_LIMIT}", t
                )
            return CplFloat(t, t.value)
        if t.type == TokenType.STRING_LITERAL:
            return CplString(t, t.value[1:-1])
        if t.type == TokenType.SELECTOR:
            return CplSelector(t, t.value)
        if (
                t.type == TokenType.SELECTOR_IDENTIFIER
                or t.type == TokenType.BLOCK_IDENTIFIER
                or t.type == TokenType.IDENTIFIER
        ):
            return self.variable_token_to_cpl(ctx, t)
        if isinstance(t, GroupToken) and t.func:
            return self.run_function(ctx, t)
        if isinstance(t, GroupToken) and t.open.value == "(":
            return self.tokens_to_cpl(ctx, t.children)
        if isinstance(t, GroupToken) and t.open.value == "[":
            if len(t.children) == 0:
                return CplTuple(t, [])
            cpl_list = list(map(
                lambda tk_list: self.tokens_to_cpl(ctx, tk_list), split_tokens(t.children)
            ))
            for cpl in cpl_list:
                if cpl.get_py_value() is None:
                    break
                if cpl.unique_type != cpl_list[0].unique_type:
                    return CplTuple(t, cpl_list)
            return CplArray(t, cpl_list)
        if isinstance(t, GroupToken) and t.open.value == "{":
            d = dict()

            for tl in split_tokens(list(filter(lambda x: x.type not in ENDERS, t.children))):
                if len(tl) < 3:
                    raise_syntax_error("Invalid object", t)
                key_token = tl[0]
                colon_token = tl[1]
                if colon_token.value != ":":
                    raise_syntax_error("Expected a colon", colon_token)
                expr = tl[2:]
                if key_token.type not in {TokenType.STRING_LITERAL, TokenType.IDENTIFIER}:
                    raise_syntax_error("Expected an object key", key_token)
                    return NULL_VALUE
                k = key_token.value
                if key_token.type == TokenType.STRING_LITERAL:
                    k = k[1:-1]
                d[k] = self.tokens_to_cpl(ctx, expr)

            return CplObject(t, d, class_name=None)
        raise_syntax_error("Invalid expression", t)
        raise ValueError("")

    def chains_to_cpl(
            self, ctx: TranspilerContext, chains: List[List[Token]]
    ) -> CompileTimeValue:
        if len(chains) == 0:
            return NULL_VALUE
        if len(chains) == 1:
            return self.chain_to_cpl(ctx, chains[0])
        t0 = chains[0]
        t1 = chains[1]
        if t0[0].value in COMMANDS:
            # TODO: use tokens
            return self.run_cmd(
                Token(t0[0].code, TokenType.POINTER, t0[0].start, chains[-1][-1].end),
                ctx,
            )
        if t1[0].value in INC_OP:
            variable_cpl = self.chain_to_cpl(ctx, t0)  # type: CplScore | CplNBT

            variable_cpl.compute(ctx, t1[0].value[0] + "=", CplInt(None, 1))

            return variable_cpl
        constant_keyword = False
        if t0[0].value == "const":
            constant_keyword = True
            t0 = t1
            if len(chains) < 3:
                raise_syntax_error("Expected an expression for the assignment", t1[0])
            t1 = chains[2]
            chains = chains[1:]

        front_type = cpl_def_from_tokens(self.classes, t0)
        if front_type is not None:
            t0 = t1
            if len(chains) < 3:
                raise_syntax_error("Expected an expression for the assignment", t1[0])
            t1 = chains[2]
            chains = chains[1:]

        if t1[0].value in SET_OP:
            is_constant = constant_keyword
            # TODO: [a, b, c] = [1, 2, 3] syntax and also for objects
            if (
                    t0[0].type != TokenType.IDENTIFIER
                    and t0[0].type != TokenType.SELECTOR_IDENTIFIER
                    and t0[0].type != TokenType.BLOCK_IDENTIFIER
            ):
                raise_syntax_error("Invalid variable name", t0[0])
                raise ValueError("")
            if len(chains) < 3:
                raise_syntax_error("Expected an expression for the assignment", t1[0])
            cpl = self.chains_to_cpl(ctx, chains[2:])
            variable = self._var_to_cpl_or_none(ctx, t0[0])

            var_name_token = t0[0]
            var_name = var_name_token.value
            if isinstance(var_name_token, SelectorIdentifierToken) or isinstance(var_name_token, BlockIdentifierToken):
                var_name = var_name_token.name.value

            is_init = variable is None

            if is_init:
                if t1[0].value != "=" or len(t0) != 1:
                    raise_syntax_error("Variable not found", t0[0])

                if cpl.unique_type.type in {"int", "float"}:
                    self.files["__load__"].append(
                        f'scoreboard objectives add {var_name} dummy "{var_name}"'
                    )
                if isinstance(cpl, CplTuple) and (not front_type or len(cpl.value) > 0):
                    if len(cpl.value) == 0:
                        show_warning(f"Did you mean to initialize an array instead of a tuple? "
                                     f"Use this syntax: int[] <variable_name> = []", t1[0])
                    is_constant = True
                last_var_type = cpl
                if front_type and front_type != cpl.unique_type:
                    if isinstance(front_type, CplDefArray) and isinstance(cpl, CplTuple) and len(cpl.value) == 0:
                        last_var_type = _type_to_cpl(t0[0], front_type, "", f"storage variables {var_name}")
                    else:
                        raise_syntax_error(f"Variable was defined as a {front_type} but got a {cpl.unique_type}", t0[0])
                if isinstance(cpl, CplSelector):
                    last_var_type = INT_TYPE
                self.variables[var_name] = VariableDeclaration(last_var_type, is_constant)
                if is_constant:
                    if (isinstance(var_name_token, SelectorIdentifierToken)
                            or isinstance(var_name_token, BlockIdentifierToken)):
                        nbt_loc = self._nbt_var_loc(ctx, var_name_token)
                        ctx.file.append(f"data modify {nbt_loc} set value {json.dumps(cpl.get_py_value())}")
                        del self.variables[var_name]
                    return cpl
            else:
                if front_type:
                    raise_syntax_error("Already defined variables cannot be assigned to a type", t1[0])
                if var_name in self.variables and self.variables[var_name].constant:
                    raise_syntax_error("Variable is constant", t0[0])
                    raise ValueError("")
                if is_constant:
                    raise_syntax_error("Already defined variables cannot be assigned with the 'const' keyword", t0[0])

            variable_cpl = self.chain_to_cpl(ctx, t0)  # type: CplScore | CplNBT

            if variable_cpl.unique_type.type in {"int", "float"} and isinstance(cpl, CplSelector):
                variable_cpl._set(ctx, CplInt(t0[0], 0))
                if isinstance(variable_cpl, CplScore):
                    set_1 = f"scoreboard players set {variable_cpl.location} 1"
                elif isinstance(variable_cpl, CplNBT):
                    set_1 = f"data modify storage variables {variable_cpl.location} set value 1"
                else:
                    raise ValueError("")
                ctx.file.append(f"execute if entity {cpl.value} run {set_1}")
                return variable_cpl

            if variable_cpl.unique_type == "int" and cpl.unique_type == "float":
                show_warning("Losing float precision by assigning a float to an int.", t1[0])

            variable_cpl.compute(ctx, t1[0].value, cpl)

            return cpl

        expr = make_expr(chains)

        stack: List[CompileTimeValue] = []

        for chain in expr:
            if chain[0].type != TokenType.OPERATOR:
                stack.append(self.chain_to_cpl(ctx, chain))
                continue

            right = stack.pop()
            left = stack.pop()

            score = left.compute(ctx, chain[0].value, right)

            stack.append(score)

        return stack[-1]

    def tokens_to_cpl(
            self, ctx: TranspilerContext, tokens: List[Token]
    ) -> CompileTimeValue:
        if len(tokens) == 0:
            return NULL_VALUE
        chains = chain_tokens(tokens)
        return self.chains_to_cpl(ctx, chains)

    def run_function_with_cpl(
            self,
            ctx: TranspilerContext,
            name: str,
            args: List[CompileTimeValue],
            base: Union[Token, None] = None,
            class_name: str | None = None,
            store_class: CplObjectNBT | None = None
    ) -> Union[CplScore, CplNBT]:
        found_fn_name: FunctionDeclaration | None = None
        for f in self.functions:
            if f.name == name:
                found_fn_name = f
                break

        if not found_fn_name and name not in builtin:
            raise_syntax_error("Undefined function", base)
            return NULL_VALUE

        if name not in self.classes and not found_fn_name and name in builtin:
            built = builtin[name]
            if len(built) == 1 and built[0].type == "python-raw":
                if not base:
                    raise_syntax_error("Cannot run a raw function without tokens", base)
                return built[0].function(ctx, base)
            if len(built) == 1 and built[0].type == "python-cpl":
                return built[0].function(ctx, args, base)
            self.functions += built

        if name in self.classes:
            cls = self.classes[name]
            class_name = cls.name
            ctx.file.append(f"data modify storage class this append {cls.sample.get_data_str(ctx)}")

        given_types = ", ".join([str(arg.unique_type) for arg in args])

        found_fn = None
        available = []
        for f in self.functions:
            if f.name == name:
                available.append(f"{f.name}({', '.join(str(arg.unique_type) + ' ' + arg.name for arg in f.arguments)})")
            if f.name == name and f.argumentsStr == given_types:
                found_fn = f
                break
        if found_fn is None:
            raise_syntax_error(f"Invalid arguments. Available usages:\n{'\n'.join(available)}", base)
            raise SyntaxError("")

        returns = found_fn.returns
        fn_args = found_fn.arguments

        if found_fn.type == "python-cpl":
            return found_fn.function(ctx, args, base)

        has_any_macro_argument = False

        for index, arg in enumerate(fn_args):
            store_at = arg.store
            val = args[index]
            if arg.store_via == "stack":
                if isinstance(val, CplScore):
                    ctx.file.append(
                        f"data modify {store_at.location} append value {store_at.unique_type.get_sample_value()}")
                    val.cache(ctx, f"{store_at.location}[-1]")
                else:
                    ctx.file.append(f"data modify {store_at.location} append {val.get_data_str(ctx)}")
            elif arg.store_via == "macro":
                val.cache(ctx, nbt_loc=f"storage fn_args_macro {arg.store.location.split(' ')[-1]}", force="nbt")
                has_any_macro_argument = True
            else:
                store_at._set(ctx, val)

        if found_fn.type == "mcfunction":
            ctx.file.append(f"function {self.pack_namespace}:{found_fn.file_name} with storage fn_mem")

        if found_fn.type == "python":
            found_fn.function(ctx, found_fn, base)

        actually_returning = NULL_VALUE

        if found_fn.type == "radon":
            ctx.file.append(f"function {self.pack_namespace}:{found_fn.file_name}" + (
                f" with storage fn_args_macro" if has_any_macro_argument else ""
            ))
            for index, arg in enumerate(fn_args):
                if arg.store_via == "stack":
                    ctx.file.append(f"data remove {arg.store.location}[-1]")

            # the line after these comments is for the case where you call a function inside a function
            # example:
            # function test(): void {
            #   # "scoreboard players set __returned__ __temp__ 0" runs:
            #   # __returned__ = 0
            #   a()
            #   # __returned__ = 1
            #   # "scoreboard players set __returned__ __temp__ 0" runs again and:
            #   # __returned__ = 0
            #   return
            # }
            # function a(): void {
            #   test()
            #   return
            # }
            if ctx.function and returns != "void":
                ctx.file.append(f"scoreboard players set __returned__ __temp__ 0")
            if isinstance(returns, str):
                if returns == "auto":
                    raise_syntax_error(
                        "Function's return type hasn't been determined yet", base
                    )
            else:
                actually_returning = returns

        if class_name is not None:
            cls = self.classes[class_name]
            if store_class is not None:
                ctx.file.append(f"data modify {store_class.location} set from storage class this[-1]")
            if name == class_name:
                ctx.file.append("data modify storage class return set from storage class this[-1]")
            ctx.file.append("data remove storage class this[-1]")
            if name == class_name:
                actually_returning = CplObjectNBT(base, "storage class return", cls.sample.unique_type)

        return actually_returning

    def run_function(
            self, ctx: TranspilerContext, t: GroupToken
    ) -> Union[CplScore, CplNBT]:
        if not t.func:
            return NULL_VALUE

        separated = split_tokens(t.children, ",")
        arguments: List[CompileTimeValue] = []
        for arg in separated:
            arguments.append(self.tokens_to_cpl(ctx, arg))

        return self.run_function_with_cpl(ctx, t.func.value, arguments, base=t)

    def compute_tokens(self, ctx: TranspilerContext, left: List[Token], op: str, right: List[Token]):
        return self.tokens_to_cpl(ctx, left).compute(ctx, op, self.tokens_to_cpl(ctx, right))

    def _cmp_to_cpl(self, ctx, ls):
        return self.compute_tokens(ctx, ls[0], ls[1].value, ls[2])


def _return_safe(ctx: TranspilerContext):
    if ctx.function:
        ctx.file.append(
            f"execute if score __returned__ __temp__ matches 1..1 run return 0"
        )
    if ctx.loop:
        if ctx.file is ctx.loop.file:
            ctx.file.append(
                f"execute if score {ctx.loop.eid} __break__ matches 1..1 run return 0"
            )
            ctx.file.append(
                f"execute if score {ctx.loop.eid} __continue__ matches 1..1 run return run {ctx.loop.continue_}"
            )
        else:
            ctx.file.append(
                f"execute if score {ctx.loop.eid} __break__ matches 1..1 run return 0"
            )
            ctx.file.append(
                f"execute if score {ctx.loop.eid} __continue__ matches 1..1 run return 0"
            )
