import json
import os
import sys
import traceback
from importlib import util
from types import FunctionType
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
from .error import raise_syntax_error, raise_syntax_error_t, show_warning, raise_error
from .nbt_definitions import ENTITIES_OBJ
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
    tokenize, LambdaFunctionToken
)
from .utils import (
    INT_TYPE,
    CplDef,
    VariableDeclaration,
    TokenType,
    get_uuid,
    INT_LIMIT,
    CplDefArray, reset_expr_id, FLOAT_PREC, CplDefFunction, get_float_limit
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


def split_fn_args(tokens: List[Token]):
    return list(map(lambda x: chain_tokens(x), split_tokens(tokens, ",")))


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


class FunctionDeclaration:
    def __init__(
            self,
            type: Literal[
                "radon", "python", "python-cpl", "python-raw", "python-cpl-imported", "mcfunction-imported"],
            name: str,
            returns="void",  # type: CplScore | CplNBT | str
            arguments: List[FunctionArgument] = None,
            function: Any = None,
            file_name: str = "",
            class_name: str | None = None,
            raw_args: List[int] = None
    ):
        if arguments is None:
            arguments = []
        if raw_args is None:
            raw_args = []
        self.type = type
        self.name = name
        self.file_name = file_name
        self.returns = returns
        self.arguments: List[FunctionArgument] = arguments
        self.function = function
        self.class_name = class_name
        self.raw_args = raw_args


class ClassDeclaration:
    def __init__(
            self,
            name: str,
            attributes,  # type: CplObject
            methods: List[FunctionDeclaration],
            sample  # type: CplObjectNBT
    ):
        self.id = get_uuid()
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
            radon_path: str,
            function: FunctionDeclaration | None = None,
            loop: LoopDeclaration | Any | None = None,
            class_name: str | None = None
    ):
        self.transpiler = transpiler
        self.file_name = file_name
        self.file = file
        self.radon_path = radon_path
        self.function = function
        self.loop = loop
        self.class_name = class_name

    def clone(self):
        return TranspilerContext(
            self.transpiler,
            self.file_name,
            self.file,
            self.radon_path,
            self.function,
            self.loop,
            self.class_name
        )

    def clone_at(self, file_name: str):
        new = self.clone()
        new.file_name = file_name
        new.file = self.transpiler.files[file_name]
        return new


from .cpl._base import CompileTimeValue
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


class CustomCplObject(CplObject):
    def __init__(self, obj: Dict[str, CompileTimeValue | Any]):
        super().__init__(None)
        self.obj = obj

    def _call_index(self, ctx, index, arguments, token):
        if index in self.obj:
            fn = self.obj[index]
            if isinstance(fn, FunctionType):
                if fn.__code__.co_argcount == 2:
                    return fn(ctx, arguments)
                return fn(ctx, arguments, token)
        return None

    def _get_index(self, ctx, index: CompileTimeValue):
        if (isinstance(index, CplString)
                and index.value in self.obj
                and isinstance(self.obj[index.value], CompileTimeValue)):
            return self.obj[index.value]
        return None


def _type_to_cpl(
        token: Token, type: CplDef, score_loc: str, nbt_loc: str, force_nbt: bool = False
) -> Union[CplScore, CplNBT]:
    if force_nbt or type.type in {"string", "array", "object"}:
        return val_nbt(token, nbt_loc, type)
    return CplScore(token, score_loc, type.type)


def py_to_cpl(v):
    if isinstance(v, CompileTimeValue):
        return v
    if isinstance(v, str):
        return CplString(None, v)
    if isinstance(v, int):
        return CplInt(None, v)
    if isinstance(v, float):
        return CplFloat(None, v)
    if isinstance(v, bool):
        return CplInt(None, 1 if v else 0)
    return CplInt(None, 0)


builtin_fns: Dict[str, List[FunctionDeclaration]] = {}
builtin_vars: Dict[str, VariableDeclaration] = {}


def add_lib(*libs):
    for lib in libs:
        if isinstance(lib, FunctionDeclaration):
            if lib.name in builtin_fns:
                builtin_fns[lib.name].append(lib)
            else:
                builtin_fns[lib.name] = [lib]
        elif isinstance(lib, VariableDeclaration):
            builtin_vars[lib.name] = lib


radon_module_id = 0


def import_module_from_path(file_path):
    global radon_module_id
    radon_module_id += 1
    module_name = f"radon__{radon_module_id}"
    spec = util.spec_from_file_location(module_name, file_path)
    module = util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def get_module_attr(module):
    d = {}
    for k in module.__dict__:
        if k.startswith("__"):
            continue
        v = module.__dict__[k]
        d[k] = v
    return d


# add lib
from .builtin import lmath, print as _no, pyeval, time, swap, stdvar, listener, exit, recipe, success, raycast, getpos

_ = [lmath, _no, pyeval, time, swap, stdvar, listener, exit, recipe, success, raycast, getpos]


def get_fn_macro_obj(ctx: TranspilerContext):
    if not ctx.function:
        return ""
    d = []
    has_macro = False
    for arg in ctx.function.arguments:
        if arg.store_via == "macro":
            has_macro = True
            d.append(f"'{arg.name}':'$({arg.name})'")
    if not has_macro:
        return ""
    return "{" + ",".join(d) + "}"


def _get_def(v: CompileTimeValue | CplDef):
    return v if isinstance(v, CplDef) else v.unique_type


class Transpiler:
    def __init__(self, statements: List[Statement], macros: List[Statement], pack_namespace: str = "mypack",
                 pack_description: str = "", pack_format: int = 48, main_dir: str = "./",
                 main_file_path: str = "main.rn", debug_mode=False) -> None:
        reset_expr_id()
        self.files = dict()
        self.dp_files = dict()
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
        self.tick_file = []
        self.tempFiles: Dict[str, str] = dict()
        self.builtin_fns = builtin_fns
        self.builtin_vars = builtin_vars
        self.s = "" if self.pack_format >= 48 else "s"
        self.debug_mode = debug_mode

        if len(statements) == 0:
            self.files = {}
            return
        self.macros = macros
        load_file = [
            'scoreboard objectives add __temp__ dummy',
            f'scoreboard players set FLOAT_PREC __temp__ {FLOAT_PREC}'
        ]
        self.files["__load__"] = load_file
        self.load_file = load_file
        main_file = []
        self.main_file = main_file
        self._transpile(
            TranspilerContext(
                transpiler=self,
                file_name="__main__",
                file=main_file,
                radon_path=main_file_path,
                function=None,
                loop=None),
            statements
        )
        load_file.extend(main_file)

        if "tick" not in self.files:
            if self.tick_file:
                self.files["tick"] = self.tick_file
        else:
            self.files["tick"] = self.tick_file + self.files["tick"]

        if len(self.variables.keys()) > 0:
            self.load_file.insert(0, 'scoreboard objectives add global dummy "global"')

        # remove the lines after immediate returns
        for file in self.files:
            lines = self.files[file]
            if len(lines) == 0:
                continue
            index = 0
            for index, line in enumerate(lines):
                if line.startswith("return"):
                    break
            self.files[file] = lines[:index + 1]
        if self.debug_mode:
            for file in self.files:
                lines = self.files[file]
                new_file = []
                for line in lines:
                    new_file.append(line)
                    if line.startswith("scoreboard players "):
                        spl = line.split(" ")
                        new_file.append('tellraw @a ["' + spl[3] + " " + spl[4] + ' = ",{"score":{"name":"' + spl[
                            3] + '","objective":"' + spl[4] + '"}}]')
                self.files[file] = new_file

    def get_datapack_files(self):
        fn_folder = "function" + self.s
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
            dp_files[f"data/minecraft/tags/{fn_folder}/tick.json"] = json.dumps(
                {
                    "values": [f"{self.pack_namespace}:tick"]
                }, indent=2)
        for f in self.dp_files:
            dp_files[f"data/{self.pack_namespace}/{f}"] = self.dp_files[f]
        return dp_files

    def get_temp_file_name(self, content: str | List[str]):
        if isinstance(content, list):
            content = "\n".join(content)
        if content in self.tempFiles:
            return self.tempFiles[content]
        file_name = f"__temp__/{get_uuid()}"
        self.tempFiles[content] = file_name
        self.files[file_name] = content.split("\n")
        return file_name

    def get_all_fn_by_name(self, name):
        ls = []
        for fn in self.functions:
            if fn.name == name:
                ls.append(fn)
        return ls

    def check_args(self, args1, args2, base):
        if len(args1) != len(args2):
            return False
        for index, arg1 in enumerate(args1):
            arg2 = args2[index]
            if isinstance(_get_def(arg2), CplDefFunction) and isinstance(arg1, CplString) and arg1.is_fn_reference:
                temp = arg1
                arg1 = arg2
                arg2 = temp
            t1 = _get_def(arg1)
            t2 = _get_def(arg2)
            if isinstance(t1, CplDefFunction) and isinstance(arg2, CplString) and arg2.is_fn_reference:
                arg_fn = self.get_fn(arg2.value, t1.arguments, base)
                if not arg_fn:
                    return False
                if arg_fn.returns == "auto":
                    raise_syntax_error("Cannot use function as a value before the return type is not determined", base)
                if arg_fn.returns == "void" and t1.returns is None:
                    continue
                if arg_fn.returns.unique_type != t1.returns:
                    continue
                continue
            if t1 != t2:
                return False
        return True

    def assert_args(self, name, args1, args2, base):
        if not self.check_args(args1, args2, base):
            raise_syntax_error(
                f"Invalid arguments. Expected usage: {name}({', '.join(map(str, args1))}), but got: {name}({', '.join(map(str, args2))})",
                base)

    def get_fn(self, name, arguments: List[CompileTimeValue | CplDef], base) -> FunctionDeclaration | None:
        for fn in self.functions:
            if fn.name == name and self.check_args(fn.arguments, arguments, base):
                return fn
        return None

    def fn_exists(self, name):
        for fn in self.functions:
            if fn.name == name:
                return fn
        return None

    def _transpile_statement(self, ctx: TranspilerContext, statement: Statement):
        if isinstance(statement, DefineClassStatement):
            if ctx.function or ctx.loop:
                raise_syntax_error(
                    "Classes should be declared in the main scope", statement
                )
            name = statement.name.value
            if name in self.classes or self.fn_exists(name):
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
                radon_path=ctx.radon_path,
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
                self._transpile_statement(class_ctx, mt)
                fn = self.functions[-1]
                new_methods.append(fn.name)
            cls.methods = new_methods

            if not has_init:
                self._transpile(class_ctx, parse(
                    tokenize("fn " + name + "() {}")[0],
                    [], list(self.classes.keys())))
                fn = self.functions[-1]
                methods.append(fn)
            return
        if isinstance(statement, ImportStatement):
            pt = statement.path.value[1:-1]
            if pt.endswith(".py"):
                bef = os.getcwd()
                os.chdir(os.path.dirname(ctx.radon_path))
                if not os.path.exists(pt) or not os.path.isfile(pt):
                    os.chdir(bef)
                    raise_syntax_error("File not found", statement)
                try:
                    lib_module = import_module_from_path(pt)
                except Exception as e:
                    os.chdir(bef)
                    raise_error("Import error", str(e), statement)
                    raise e
                attrs = get_module_attr(lib_module)
                os.chdir(bef)
                if statement.as_ is not None:
                    name = statement.as_.value
                    if name not in self.variables:
                        self.variables[name] = VariableDeclaration(name, CustomCplObject(attrs), True)
                    return True
                for name in attrs:
                    v: Any = attrs[name]
                    if isinstance(v, FunctionType) and v.__code__.co_argcount in {2, 3}:
                        self.functions.append(FunctionDeclaration(
                            type="python-cpl-imported",
                            name=name,
                            function=v
                        ))
                    elif isinstance(v, CompileTimeValue):
                        if name not in self.variables:
                            self.variables[name] = VariableDeclaration(name, v, True)
                return True
            if pt.endswith(".mcfunction"):
                if statement.as_ is None:
                    raise_syntax_error("Expected 'as' in mcfunction import statement", statement)
                bef = os.getcwd()
                os.chdir(os.path.dirname(ctx.radon_path))
                if not os.path.exists(pt) or not os.path.isfile(pt):
                    os.chdir(bef)
                    raise_syntax_error("File not found", statement)
                content = open(pt, "r", encoding="utf-8").read()
                os.chdir(bef)
                fn_id = get_uuid()
                self.files[f"__imported__/{fn_id}"] = content.split("\n")
                self.functions.append(FunctionDeclaration(
                    type="mcfunction-imported",
                    name=statement.as_.value,
                    file_name=f"__imported__/{fn_id}"
                ))
                return True
            if pt.endswith(".rn"):
                if statement.as_ is not None:
                    raise_syntax_error("Unexpected 'as' in radon file import statement", statement)
                bef = os.getcwd()
                os.chdir(os.path.dirname(ctx.radon_path))
                if not os.path.exists(pt) or not os.path.isfile(pt):
                    os.chdir(bef)
                    raise_syntax_error("File not found", statement)
                content = open(pt, "r", encoding="utf-8").read()
                os.chdir(bef)
                (tokens, macros) = tokenize(content)
                ctx.transpiler._transpile(
                    TranspilerContext(
                        transpiler=ctx.transpiler,
                        file_name="__main__",
                        file=self.main_file,
                        radon_path=pt,
                        function=None,
                        loop=None,
                        class_name=None
                    ), parse(tokens, macros, list(ctx.transpiler.classes.keys()))
                )
                return True
            raise_syntax_error("Invalid import", statement)
        if isinstance(statement, ScheduleStatement):
            file_name = self._run_safe("__schedule__", statement.body, ctx)
            ctx.file.append(
                f"schedule function {self.pack_namespace}:{file_name} {statement.time.value} replace"
            )
            _return_safe(ctx)
            return True
        if statement.type == StatementType.BREAK:
            if not ctx.loop:
                raise_syntax_error("Cannot use break outside of loop", statement)
            if ctx.file is ctx.loop.file:
                ctx.file.append("return 0")
            else:
                loop_id = ctx.loop.eid
                ctx.file.append(f"scoreboard players set __break__{loop_id} __temp__ 1")
                ctx.file.append(f"return 0")
            return True
        if isinstance(statement, ContinueStatement):
            if not ctx.loop:
                raise_syntax_error("Cannot use continue outside of loop", statement)
            if ctx.file is ctx.loop.file:
                ctx.file.append(ctx.loop.continue_)
                ctx.file.append("return 0")
            else:
                loop_id = ctx.loop.eid
                ctx.file.append(f"scoreboard players set __continue__{loop_id} __temp__ 1")
                ctx.file.append(f"return 0")
            return True
        if isinstance(statement, LoopStatement):
            file_name = self._run_safe(
                "__loop__",
                statement.body,
                TranspilerContext(
                    transpiler=self,
                    file_name=ctx.file_name,
                    file=ctx.file,
                    radon_path=ctx.radon_path,
                    function=ctx.function,
                    loop=statement)
            )
            mac = get_fn_macro_obj(ctx)
            ctx.file.append(f"{'$' if mac else ''}function {self.pack_namespace}:{file_name}" + mac)
            loop_file = self.files[file_name]
            loop_id = int(file_name.split("/")[-1])
            loop_file.insert(0, f"scoreboard players set __break__{loop_id} __temp__ 0")
            loop_file.insert(0, f"scoreboard players set __continue__{loop_id} __temp__ 0")
            loop_c = self.loops[loop_id]
            loop_file.append(loop_c.continue_)
            return True
        if isinstance(statement, IfFlowStatement):
            has_if = len(statement.body) != 0
            has_else = statement.elseBody and len(statement.elseBody) != 0
            if not has_if and not has_else:
                return True
            resp = self.tokens_to_cpl(ctx, statement.condition)
            if (
                    isinstance(resp, CplInt)
                    or isinstance(resp, CplFloat)
                    or (resp.unique_type.type not in {"int", "float"} and not isinstance(resp, CplSelector))):
                is_true = (not isinstance(resp, CplInt) and not isinstance(resp, CplFloat)) or resp.value != 0
                if is_true:
                    if not has_if:
                        return True
                    self._transpile(ctx, statement.body)
                elif (
                        has_else and statement.elseBody
                ):  # I know this is bad, but the linter wants it (statement.elseBody)
                    self._transpile(ctx, statement.elseBody)
                return True
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
                    return True

            if has_if:
                if_name = self._run_safe("__if__", statement.body, ctx)
                ctx.file.append(f"{if_cmd}function {self.pack_namespace}:{if_name}")
            if has_else:
                else_name = self._run_safe("__else__", statement.elseBody, ctx)
                ctx.file.append(f"{unless_cmd}function {self.pack_namespace}:{else_name}")
            _return_safe(ctx)
            return True
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
                    return True
                if len(ctx.file) > 0 and ctx.file[-1].startswith(cl2):
                    ctx.file[-1] = ctx.file[-1][len(cl2):]
                if len(ctx.file) > 1 and ret.location not in ctx.file[-1] and ctx.file[-2].startswith(cl1):
                    ctx.file.pop(-2)
            if isinstance(ret, CplNBT) and ret.location.startswith("storage temp "):
                # Cleaning the return results of the inline expression since they aren't going to be used
                cl1 = f"data modify {ret.location} set from"
                if len(ctx.file) > 0 and ctx.file[-1].startswith(cl1):
                    ctx.file.pop()
                    return True
                if len(ctx.file) > 1 and ctx.file[-2].startswith(cl1) and ret.location not in ctx.file[-1]:
                    ctx.file.pop(-2)
                    return True
            return True
        if isinstance(statement, DefineFunctionStatement):
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
            is_class_init = fn_name == ctx.class_name
            ret_loc = ret
            if isinstance(ret_loc, CplDef):
                assert isinstance(statement.returns, list)
                assert isinstance(ret, CplDef)
                ret_loc = _type_to_cpl(
                    statement.returns[0],
                    ret,
                    score_loc=f"fn_return __temp__",
                    nbt_loc=f"storage temp fn_return"
                )
            if is_class_init:
                if isinstance(statement.returns, list) and len(statement.returns) > 0:
                    raise_syntax_error("Class initializers cannot have return types", statement.returns[0])
                cls = self.classes[fn_name]
                ret_loc = CplObjectNBT(statement.name, f"storage variables this[-1]",
                                       cls.attributes.unique_type)
            count = 0
            new_functions = []
            for f in self.functions:
                if fn_name == f.name:
                    count += 1
                    if self.check_args(f.arguments, arguments, statement.name):
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
                    radon_path=ctx.radon_path,
                    function=f,
                    loop=ctx.loop,
                    class_name=ctx.class_name),
                statement.body
            )
            if is_class_init:
                cls = self.classes[ctx.class_name]
                fn_file.insert(0, f"data modify storage variables this append {cls.sample.get_data_str(ctx)}")
            if f.returns == "auto":
                f.returns = "void"
            fn_file.insert(0, f"scoreboard players set __returned__ __temp__ 0")
            return True
        if isinstance(statement, ReturnStatement):
            if not ctx.function:
                raise_syntax_error(
                    "Cannot use return keyword outside functions", statement
                )
                return True
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
            return True
        if isinstance(statement, IntroduceVariableStatement):
            name = statement.name.value
            if name in self.variables:
                raise_syntax_error("Variable is already introduced", statement)
            type_v = cpl_def_from_tokens(self.classes, statement.varType)
            if not type_v:
                raise_syntax_error(f"Invalid type", statement)
                raise SyntaxError("")
            self.variables[name] = VariableDeclaration(name, type_v, False)
            self.load_file.append(
                f'scoreboard objectives add {name} dummy "{name}"'
            )
            self.load_file.append(
                f"scoreboard players enable {name} global"
            )
            return True
        if isinstance(statement, ExecuteMacroStatement):
            exec_name = self._run_safe("__execute__", statement.body, ctx)
            cmd_str, has_repl = self.proc_cmd(ctx, statement.command)
            if has_repl:
                fid = f"__execute__/{get_uuid()}"
                self.files[fid] = [f"$execute {cmd_str} run function {self.pack_namespace}:{exec_name}"]
                ctx.file.append(f"function {self.pack_namespace}:{fid} with storage cmd_mem")
            else:
                ctx.file.append(f"execute {cmd_str} run function {self.pack_namespace}:{exec_name}")
            _return_safe(ctx)
            return True
        raise_syntax_error("Invalid statement", statement)

    def _transpile(self, ctx: TranspilerContext, statements: List[Statement]):
        for statement in statements:
            self._transpile_statement(ctx, statement)

    def _run_safe(self, folder_name, statements, ctx: TranspilerContext):
        eid = get_uuid()
        file_name = f"{folder_name}/{eid}"
        new_file = []
        loop = ctx.loop
        if isinstance(loop, LoopStatement):
            mac = get_fn_macro_obj(ctx)
            continue_ = f"{'$' if mac else ''}function {self.pack_namespace}:{file_name}" + mac
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
                radon_path=ctx.radon_path,
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

    def proc_cmd(self, ctx: TranspilerContext, cmd: str):
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
                    or cmd[i: i + 6] == "$jstr("
                    or cmd[i: i + 6] == "$dstr("
            ):
                si = i
                k = 0
                fp = 0
                while i < len(cmd):
                    i += 1
                    c = cmd[i]
                    if c == "(":
                        if fp == 0:
                            fp = i
                        k += 1
                    if c == ")":
                        k -= 1
                        if k == 0:
                            break
                if cmd[i] != ")":
                    raise_syntax_error_t("Unterminated parentheses", cmd, si, i + 1)
                repl = cmd[fp + 1: i]
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
                elif cmd[si + 1] == "d":
                    py_val = val.get_py_value()
                    if py_val is not None:
                        cmd_str += str(py_val)
                    else:
                        cmd_str += val.tellraw_object(ctx)
                elif cmd[si + 1] == "j":
                    cmd_str += json.dumps(val.tellraw_object(ctx))

                i += 1
                continue
            cmd_str += cmd[i]
            i += 1

        return cmd_str, has_repl

    def run_cmd(self, ctx: TranspilerContext, pointer: Token, score_loc=None, type="result") -> CompileTimeValue:
        file = ctx.file
        cmd = pointer.value
        cmd_str, has_repl = self.proc_cmd(ctx, cmd)

        eid = score_loc or "int_" + str(get_uuid()) + " __temp__"
        eid_val = CplScore(pointer, eid, "int")

        if not has_repl:
            file.append(f"execute store {type} score {eid} run {cmd_str}")
            return eid_val

        cmd_file = []
        file_name = None
        '''for i in self.files:
            if "\n".join(self.files[i]) == "\n".join(cmd_file) and i.startswith("__cmd__/"):
                file_name = i
                break'''
        if file_name is None:
            cmd_id = get_uuid()
            file_name = f"__cmd__/{cmd_id}"
        self.files[file_name] = cmd_file
        cmd_file.append("$" + cmd_str)
        file.append(
            f"execute store {type} score {eid} run function {self.pack_namespace}:{file_name} with storage cmd_mem"
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
    ) -> Union[CompileTimeValue, None]:
        if isinstance(t, SelectorIdentifierToken):
            name = t.name.value
            if name in ENTITIES_OBJ.content:
                return _type_to_cpl(
                    t,
                    ENTITIES_OBJ.content[name],
                    score_loc="",
                    nbt_loc=self._nbt_var_loc(ctx, t),
                    force_nbt=True
                )
            if name not in self.variables:
                return None
            var = self.variables[name]
            var_type = var.type
            return _type_to_cpl(
                t,
                var_type,
                score_loc=f"{t.selector.value} {name}",
                nbt_loc=self._nbt_var_loc(ctx, t),
                force_nbt=False
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
            if name not in self.variables and name not in builtin_vars:
                if self.fn_exists(name):
                    return CplString(t, name, is_fn_reference=True)
                if ctx.function and ctx.class_name is not None and name == "this":
                    return CplObjectNBT(t, f"storage variables this[-1]",
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
            var = self.variables[name] if name in self.variables else builtin_vars[name]
            if var.init_func is not None:
                var.init_func(ctx)
            if var.get_func is not None:
                return var.get_func(ctx)
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
    ) -> CompileTimeValue:
        res = self._var_to_cpl_or_none(ctx, t)
        if res is None:
            raise_syntax_error("Variable not found", t)
            raise SyntaxError("")
        return res

    def chain_to_cpl(self, ctx: TranspilerContext, t: List[Token]) -> CompileTimeValue:
        cpl = self.token_to_cpl(ctx, t[0])
        for token in t[1:]:
            if token.type == TokenType.IDENTIFIER:
                cpl = cpl.get_index(ctx, CplString(token, token.value), token)
                continue
            if token.type == TokenType.INT_LITERAL:
                cpl = cpl.get_index(ctx, CplInt(token, token.value), token)
                continue
            if isinstance(token, GroupToken):
                if token.open.value == "[":
                    if len(token.children) == 0:
                        raise_syntax_error("A bracket index has to include an expression inside.", token)
                        assert False
                    spl = list(map(lambda x: self.tokens_to_cpl(ctx, x) if len(x) > 0 else None,
                                   split_tokens(token.children, ":", comma_errors=False)))
                    if len(spl) == 1:
                        cpl = cpl.get_index(ctx, spl[0], token)
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

                    cpl = cpl.get_slice(ctx, spl[0], spl[1], spl[2], token)
                    continue
                if token.func:
                    cpl = cpl.call_index(ctx, token.func.value, self.arg_tokens_to_cpl(ctx, token.children), token)
                    continue
                if token.open.value == "(":
                    cpl = cpl.call(ctx, self.arg_tokens_to_cpl(ctx, token.children), token)
                    continue
            raise_syntax_error(f"Cannot index with the token", token)
        return cpl

    def arg_tokens_to_cpl(self, ctx: TranspilerContext, tokens: List[Token]):
        return list(map(lambda x: self.chains_to_cpl(ctx, chain_tokens(x)), split_tokens(tokens, ",")))

    def token_to_cpl(self, ctx: TranspilerContext, t: Token):
        if t.type == TokenType.INT_LITERAL:
            if abs(int(t.value)) > INT_LIMIT:
                raise_syntax_error(
                    f"An integer literal cannot be larger than {INT_LIMIT}", t
                )
            return CplInt(t, t.value)
        if t.type == TokenType.FLOAT_LITERAL:
            if abs(float(t.value)) > get_float_limit():
                raise_syntax_error(
                    f"A float literal cannot be larger than {get_float_limit()}", t
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
                if key_token.type != TokenType.STRING_LITERAL:
                    raise_syntax_error("Expected an object key", key_token)
                    return CplInt(t, 0)
                k = key_token.value[1:-1]
                d[k] = self.tokens_to_cpl(ctx, expr)

            return CplObject(t, d, class_name=None)
        if isinstance(t, LambdaFunctionToken):
            name = f"__lambda__/{get_uuid()}"
            self._transpile_statement(ctx, DefineFunctionStatement(
                t.code,
                t.start,
                t.end,
                Token(name, TokenType.IDENTIFIER, 0, len(name)),
                parse(t.body.children, self.macros, list(self.classes.keys())),
                list(map(lambda x: chain_tokens(x), split_tokens(t.arguments.children, ","))),
                "auto"
            ))
            return CplString(t, name, is_fn_reference=True)
        # raise_syntax_error("Invalid expression", t)
        raise ValueError("")

    def chains_to_cpl(
            self, ctx: TranspilerContext, chains: List[List[Token]]
    ) -> CompileTimeValue:
        if len(chains) == 0:
            return CplInt(None, 0)
        if len(chains) == 1:
            return self.chain_to_cpl(ctx, chains[0])
        t0 = chains[0]
        t1 = chains[1]
        if t0[0].value in COMMANDS:
            # TODO: use tokens
            return self.run_cmd(ctx, Token(t0[0].code, TokenType.POINTER, t0[0].start, chains[-1][-1].end))
        if t0[0].value in {"not", "!"}:
            # Basically, 1 - x
            variable_cpl = self.chain_to_cpl(ctx, t1)
            if variable_cpl.unique_type.type not in {"int", "float"}:
                return CplInt(t1[0], 0)
            if isinstance(variable_cpl, CplInt) or isinstance(variable_cpl, CplFloat):
                return CplInt(t1[0], 1 - variable_cpl.value)

            temp_score = CplScore(t1[0], f"int_{get_uuid()}")
            temp_score.compute(ctx, "=", CplInt(None, 1), t1[0])
            variable_cpl.compute(ctx, "-=", temp_score, t1[0])

            return temp_score
        if t0[0].value in INC_OP:
            variable_cpl = self.chain_to_cpl(ctx, t1)

            variable_cpl.compute(ctx, t0[0].value[0] + "=", CplInt(None, 1), t1[0])

            return variable_cpl
        if t1[0].value in INC_OP:
            variable_cpl = self.chain_to_cpl(ctx, t0)

            cached = variable_cpl.cache(ctx)
            variable_cpl.compute(ctx, t1[0].value[0] + "=", CplInt(None, 1), t0[0])

            return cached
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
            if t0[0].value == "this" and not ctx.class_name:
                raise_syntax_error("Cannot access 'this' keyword outside of a class", t0[0])
            variable = self._var_to_cpl_or_none(ctx, t0[0])

            var_name_token = t0[0]
            var_name = var_name_token.value
            if isinstance(var_name_token, SelectorIdentifierToken) or isinstance(var_name_token, BlockIdentifierToken):
                var_name = var_name_token.name.value

            is_init = variable is None

            if is_init:
                if t1[0].value != "=" or len(t0) != 1:
                    raise_syntax_error("Variable not found", t0[0])
                if t0[0] == "this":
                    raise_syntax_error("Cannot assign 'this' keyword to something", t0[0])

                if cpl.unique_type.type in {"int", "float"}:
                    self.load_file.append(
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
                self.variables[var_name] = VariableDeclaration(var_name, last_var_type, is_constant)
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

            variable_cpl = self.chain_to_cpl(ctx, t0)

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

            variable_cpl.compute(ctx, t1[0].value, cpl, t0[0])

            return cpl

        expr = make_expr(chains)

        stack: List[CompileTimeValue] = []

        for chain in expr:
            if chain[0].type != TokenType.OPERATOR:
                stack.append(self.chain_to_cpl(ctx, chain))
                continue

            right = stack.pop()
            left = stack.pop()

            score = left.compute(ctx, chain[0].value, right, t0[0])

            stack.append(score)

        return stack[-1]

    def tokens_to_cpl(
            self, ctx: TranspilerContext, tokens: List[Token]
    ) -> CompileTimeValue:
        if len(tokens) == 0:
            return CplInt(None, 0)
        chains = chain_tokens(tokens)
        return self.chains_to_cpl(ctx, chains)

    def run_function_with_cpl(
            self,
            ctx: TranspilerContext,
            name: str,
            args: List[CompileTimeValue],
            base: Union[Token, None] = None,
            class_name: str | None = None
    ) -> CompileTimeValue:
        exists_fn = self.fn_exists(name)

        if not exists_fn and name not in builtin_fns:
            raise_syntax_error("Undefined function", base)
            return CplInt(base, 0)

        if name not in self.classes and not exists_fn and name in builtin_fns:
            built = builtin_fns[name]
            if len(built) == 1 and built[0].type == "python-raw":
                if not base:
                    raise_syntax_error("Cannot run a raw function without tokens", base)
                return built[0].function(ctx, base) or built[0].returns
            if len(built) == 1 and built[0].type == "python-cpl":
                return built[0].function(ctx, args, base)
            self.functions.extend(built)

        if exists_fn and exists_fn.type == "python-cpl-imported":
            try:
                if exists_fn.function.__code__.co_argcount == 2:
                    return exists_fn.function(ctx, args) or CplInt(base, 0)
                return exists_fn.function(ctx, args, base)
            except Exception as _:
                stack_trace = traceback.format_exc()
                raise SyntaxError(stack_trace)

        found_fn = None
        available = []
        for f in self.functions:
            if f.name == name:
                available.append(f"{f.name}({', '.join(str(arg.unique_type) + ' ' + arg.name for arg in f.arguments)})")
                if self.check_args(f.arguments, args, base):
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

        if found_fn.type == "mcfunction-imported":
            eid = f"int_{get_uuid()} __temp__"
            ctx.file.append(
                f"execute store result score {eid} run function {self.pack_namespace}:{found_fn.file_name} with storage fn_mem")
            return CplScore(base, eid)

        if found_fn.type == "python":
            found_fn.function(ctx, found_fn, base)

        actually_returning = CplInt(base, 0)

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

        if name in self.classes:
            class_name = name

        if class_name is not None and ctx.file is not self.main_file:
            ctx.file.append(f"data modify storage temp class_this set from storage variables this[-1]")
            ctx.file.append(f"data remove storage variables this[-1]")
            actually_returning = CplObjectNBT(base, f"storage temp class_this",
                                              self.classes[class_name].sample.unique_type)

        return actually_returning

    def run_function(
            self, ctx: TranspilerContext, t: GroupToken
    ) -> CompileTimeValue:
        if not t.func:
            return CplInt(t, 0)

        raw_args = []

        if t.func.value in builtin_fns:
            built = builtin_fns[t.func.value]
            if len(built) == 1 and built[0].type == "python-raw":
                return built[0].function(ctx, t) or built[0].returns
            if len(built) == 1 and built[0].type == "python-cpl":
                raw_args = built[0].raw_args

        separated = split_tokens(t.children, ",")
        arguments: List[CompileTimeValue] = []
        for index, arg in enumerate(separated):
            arguments.append(arg if index in raw_args else self.tokens_to_cpl(ctx, arg))

        return self.run_function_with_cpl(ctx, t.func.value, arguments, base=t)

    def compute_tokens(self, ctx: TranspilerContext, left: List[Token], op: str, right: List[Token]):
        return self.tokens_to_cpl(ctx, left).compute(ctx, op, self.tokens_to_cpl(ctx, right), left[0])

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
                f"execute if score __break__{ctx.loop.eid} __temp__ matches 1..1 run return 0"
            )
            ctx.file.append(
                f"execute if score __continue__{ctx.loop.eid} __temp__ matches 1..1 run return run {ctx.loop.continue_}"
            )
        else:
            ctx.file.append(
                f"execute if score __break__{ctx.loop.eid} __temp__ matches 1..1 run return 0"
            )
            ctx.file.append(
                f"execute if score __continue__{ctx.loop.eid} __temp__ matches 1..1 run return 0"
            )
