from typing import Union, List

from ._base import CompileTimeValue
from .nbt import CplNBT, object_get_index_nbt, val_nbt
from ..error import raise_syntax_error
from ..tokenizer import Token
from ..utils import CplDefObject


class CplObjectNBT(CplNBT):
    def __init__(self, token: Union[Token, None], location: str, type: CplDefObject):
        super().__init__(token, location, type)
        self.unique_type = type

    def _get_index(self, ctx, index: CompileTimeValue):
        if isinstance(index, CplInt) or isinstance(index, CplFloat) or isinstance(index, CplString):
            ind = str(index.value)
            if ind not in self.unique_type.content:
                raise_syntax_error(f"Key '{ind}' is not in the object: {self.unique_type}", index.token)
            return val_nbt(self.token, self.location + "." + ind, self.unique_type.content[ind])
        values = self.unique_type.content.values()
        if len(set(map(str, values))) > 1:
            raise_syntax_error(
                "Cannot index into an object with a non-literal value if it has multiple value types. "
                "This is because for the compiler it's impossible to know what the type of the unknown key "
                "will correspond to. Use the myObject[myKey : valueType] syntax instead",
                self.token
            )
        content_type = list(values)[0]

        return object_get_index_nbt(ctx, content_type, self, index)

    def _get_slice(self, ctx, index1, index2, index3, token):
        pass

    def _call_index(self, ctx, index: str, arguments: List[CompileTimeValue], token):
        if self.unique_type.class_name is None:
            return None
        cls = self.unique_type.class_name
        return ctx.transpiler.run_function_with_cpl(
            ctx=ctx,
            name=cls + "." + index,
            args=arguments,
            base=self.token,
            class_name=cls
        )

    def _add(self, ctx, cpl):
        if self.unique_type.class_name != cpl.unique_type.class_name:
            return None
        if self.unique_type != cpl.unique_type:
            return None
        # TODO: array merging
        return None

    def _and(self, ctx, cpl):
        return cpl

    def _or(self, ctx, cpl):
        return self


from .string import CplString
from .float import CplFloat
from .int import CplInt
