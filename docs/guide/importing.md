# Importing

In Radon, currently you can only import `radon`, `mcfunction` and `python` files. Importing radon files will be implemented.

## Importing radon files

When radon files are imported, their content will be transpiled from the line that file was imported from.

Example:

```js
// my_file.rn

print("Hello!")
```

```js
// main.rn

print("Importing it!")

import "my_file.rn"

print("The Hello message should be on top of this!")
```

This will be executed like so:

```js
print("Importing it!")
print("Hello!")
print("The Hello message should be on top of this!")
```

## Importing mcfunction files

The imports are relative to the file that it's being imported from. For example if you import `my_func.mcfunction`
from `main.rn` you can use `my_func` in your code.

Here's a simple example:

```js
import "my_func.mcfunction" as my_func

returned_value = my_func()
```

## Importing python files

Before importing a python file, you need to make a python file. So first check out the [Python API](./python_api.md)
page. After creating your python file which might look like this:

```python
import math

from radon.cpl.int import CplInt, CplFloat


def my_func(ctx, args):
    if len(args) < 1:
        raise SyntaxError("Expected 1 argument for my_func()")
    return args[0]


my_variable = CplInt(None, 10)

pi = CplFloat(None, math.pi)
```

You can use the `import` keyword to import everything from the file:

```js
import "my_python_file.py" // Imports everything

a = my_func(50, 100, 200) // The function we defined gives the first value which is 50

b = my_variable // 10

c = pi // 3.141
```

You can also import the file as an object:

```js
import "my_python_file.py" as my_python_file

a = my_python_file.my_func(50, 100, 200) // The function we defined gives the first value which is 50

b = my_python_file.my_variable // 10

c = my_python_file.pi // 3.141
```