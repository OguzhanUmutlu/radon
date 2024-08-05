from ..cpl import CplInt
from ..transpiler import add_lib
from ..utils import VariableDeclaration

add_lib(
    VariableDeclaration(
        name="true",
        type=CplInt(None, 1),
        constant=True
    ),
    VariableDeclaration(
        name="false",
        type=CplInt(None, 0),
        constant=True
    ),
    VariableDeclaration(
        name="null",
        type=CplInt(None, 0),
        constant=True
    ))
