# Variables

Variables in Radon can have different types of values: `int`, `float`, `string`, `array`, `tuple` or `object`. Don't
forget that variables are statically typed, so you can't change their types.

You can define or alter variables like this:

::: code-group

```js [Radon]
a = 1
b = 1.248
myStr = "hello"
myArr = [1, 2, 3]
myObj = {"key": myArr, "otherKey": myStr}

const copperItem = {"count": 1, "Slot": 0, "id": "minecraft:copper_ingot"} // Immutable variable
HandItems:@e[type=zombie] = [copperItem, {}]
Items:[0, -63, 0] = [copperItem]

// Don't forget that tuples' length are not mutable.
// If an array has different typed elements, the array will be interpreted as a tuple
// You can't assign a tuple to a non-constant variable because NBTs don't support tuples
// Therefore myTuple variable is automatically determined to be a constant
myTuple = [5, "hello", {"key": "Hi!"}]
```

```mcfunction [mcfunction]
scoreboard players set a global 1
scoreboard players set b global 1248
data modify storage variables myStr set value "hello"
data modify storage variables myArr set value [1, 2, 3]
data modify storage variables myObj set value {"key":[0],"otherKey":''}
data modify storage variables myObj.key set from storage variables myArr
data modify storage variables myObj.otherKey set from storage variables myStr
data modify entity @e[type=zombie] HandItems set value [{"count": 1, "Slot": 0, "id": "minecraft:copper_ingot"}, {}]
data modify block 0 -63 0 Items set value [{"count": 1, "Slot": 0, "id": "minecraft:copper_ingot"}]
```

:::

You can define constants using the keyword `const`, and after the `const` keyword you can optionally put the type:

::: code-group

```js [Radon]
const a = 1 // This is pre-computed
const int b = 1 // Still the same thing

print(a)

// c = [] This would throw an error
int[] c = [] // This is fine because now compiler knows it's values are of type int
```

```mcfunction [mcfunction]
tellraw @a ["1"]
data modify storage variables c set value []
```

:::

You can use mathematical expressions basically everywhere like this:

::: code-group

```js [Radon]
d = a + b * c
```

```mcfunction [mcfunction]
scoreboard players operation int_1 --temp-- = b global
scoreboard players operation int_1 --temp-- *= c global
scoreboard players operation int_2 --temp-- = a global
scoreboard players operation int_2 --temp-- += int_1 --temp--
scoreboard players operation d global = int_2 --temp--
```

:::

There are a couple of methods and attributes assigned to built-in types:

::: code-group

```js [Radon]
a = 5.64
b = a.sqrt()
c = (5.64).sqrt() // This works too
d = a.cbrt()
e = a.int()
f = a.float() // Gives itself

myStr = "hello"
myStrLen = myStr.length

myArr = [1, 2, 3]
myArr.push(4)
myArr.pop()
myArr.insert(0, 5)
myArrLen = myArr.length
```

```mcfunction [mcfunction]
scoreboard players set a global 5640
scoreboard players operation sqrt_0 --temp-- = a global
scoreboard players operation __sqrt__x --temp-- /= __sqrt__4 --temp--
scoreboard players operation __sqrt__output --temp-- = __sqrt__x --temp--
function namespace_here:__lib__/__sqrt__loop
scoreboard players operation b global = null global
scoreboard players set c global 2374
scoreboard players operation cbrt_0 --temp-- = a global
scoreboard players operation __cbrt__x --temp-- *= __cbrt__4d3 --temp--
scoreboard players operation __cbrt__output --temp-- = __cbrt__x --temp--
function namespace_here:__lib__/__cbrt__loop
scoreboard players operation d global = null global
scoreboard players operation int_1 --temp-- = a global
scoreboard players operation int_1 --temp-- /= FLOAT_PREC --temp--
scoreboard players operation e global = int_1 --temp--
scoreboard players operation f global = a global
data modify storage variables myStr set value "hello"
execute store result score int_2 --temp-- run data get storage variables myStr
scoreboard players operation myStrLen global = int_2 --temp--
data modify storage variables myArr set value [1, 2, 3]
data modify storage variables myArr append value 4
data remove storage variables myArr[-1]
data modify storage variables myArr insert 0 value 5
execute store result score int_5 --temp-- run data get storage variables myArr
scoreboard players operation myArrLen global = int_5 --temp--
```

:::
