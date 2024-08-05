# Python API

Radon stores every kind of value in a class called `CompileTimeValue`.

## Values

The classes that extend `CompileTimeValue` are:

- CplInt: A literal int value that is known in compile time
- CplFloat: A literal float value that is known in compile time
- CplString: A literal string value that is known in compile time
- CplArray: A literal array value that is known in compile time
- CplObject: A literal object value that is known in compile time
- CplTuple: A tuple is like an array but it has a fixed size and its elements' type are known in compile time
- CplScore: A scoreboard pseudo player that has a location, a score location looks like this: `int_5 __temp__`
- CplSelector: A selector that is known in compile time
- CplNBT: An NBT that has a location, an NBT location looks like this: `storage temp _0`
- CplIntNBT: This extends CplNBT and denotes that its location is holding an int
- CplFloatNBT: This extends CplNBT and denotes that its location is holding a float
- CplStringNBT: This extends CplNBT and denotes that its location is holding a string
- CplArrayNBT: This extends CplNBT and denotes that its location is holding an array
- CplObjectNBT: This extends CplNBT and denotes that its location is holding an object

They get a token as the first argument which can be set to None. A simple example:

```python
from radon.cpl.int import CplInt, CplFloat

my_variable = CplInt(None, 123)
```

```js
import "./my_python_file.py"

a = my_variable // a = 123
```

## Functions

You can make a Radon function inside python by giving in `ctx` and `args` arguments. Ctx refers to context and args
refers to arguments.

Here's a simple example:

```python
def my_func(ctx, args, token):
    if len(args) < 1:
        raise_syntax_error("Expected 1 argument for my_func()", token)
    return args[0]
```

```js
import "./my_python_file.py"

a = my_func(123)
```