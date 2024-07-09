from utils import FunctionArgument, FunctionDeclaration


LIB = {
    "functions": [
        FunctionDeclaration(
            type="mcfunction",
            name="sqrt",
            file_name="__lib__/isqrt",
            returns="int",
            returnId="__isqrt__output",
            arguments=[FunctionArgument("int", "x", "__isqrt__x")],
            direct=True,
            libs=["isqrt", "isqrt_loop"],
            initLibs=["sqrt_setup"],
        ),
        FunctionDeclaration(
            type="mcfunction",
            name="sqrt",
            file_name="__lib__/fsqrt",
            returns="float",
            returnId="__fsqrt__output",
            arguments=[FunctionArgument("float", "x", "__fsqrt__x")],
            direct=True,
            libs=["fsqrt", "fsqrt_loop"],
            initLibs=["sqrt_setup"],
        ),
    ]
}
