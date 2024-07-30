import json
from typing import List

from ..cpl._base import CompileTimeValue
from ..cpl.int import CplInt
from ..cpl.object import CplObject
from ..error import raise_syntax_error
from ..transpiler import add_lib, TranspilerContext
from ..utils import VariableDeclaration, get_expr_id


class RecipeObject(CplObject):
    def _call_index(self, ctx: TranspilerContext, index: str, arguments: List[CompileTimeValue], token):
        tr = ctx.transpiler
        if index == "add":
            if len(arguments) < 1:
                raise_syntax_error("Recipe.table() requires at least 1 argument", token)
            recipe = arguments[0]
            if not isinstance(recipe, CplObject):
                raise_syntax_error("Expected an object for the first argument of Recipe.table()", token)
            recipe = recipe.get_py_value()
            if not recipe:
                raise_syntax_error("Expected the table to be a literal object", token)
            tr.dp_files[f"recipe{tr.s}/recipe_{get_expr_id()}.json"] = json.dumps(recipe, indent=2)
            return CplInt(token, 0)
        return None


add_lib(VariableDeclaration(
    name="Recipe",
    type=RecipeObject(),
    constant=True
))
