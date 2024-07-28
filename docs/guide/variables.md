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
scoreboard players operation int_1 __temp__ = b global
scoreboard players operation int_1 __temp__ *= c global
scoreboard players operation int_2 __temp__ = a global
scoreboard players operation int_2 __temp__ += int_1 __temp__
scoreboard players operation d global = int_2 __temp__
```

:::

You can even store booleans in variables so that Minecraft doesn't have to compute selectors multiple times:

::: code-group

```js [Radon]
myBool = true
myEntityBool = @e[type=zombie] // Sets to true if there is a zombie, false otherwise

if (myEntityBool) {
  print("There's a zombie!")
}

if (myEntityBool or myBool) {
  print("There's a zombie or my bool is true!!")
}
```

```mcfunction [mcfunction]
scoreboard players operation myBool global = true global
scoreboard players set myEntityBool global 0
execute if entity @e[type=zombie] run scoreboard players set myEntityBool global 1
execute unless score myEntityBool global matches 0..0 run function radon:__if__/1
scoreboard players set int_2 __temp__ 0
execute unless score myEntityBool global matches 0..0 run scoreboard players set int_2 __temp__ 1
execute unless score myBool global matches 0..0 run scoreboard players set int_2 __temp__ 1
execute unless score int_2 __temp__ matches 0..0 run function radon:__if__/3
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
scoreboard players operation sqrt_0 __temp__ = a global
scoreboard players operation __sqrt__x __temp__ /= __sqrt__4 __temp__
scoreboard players operation __sqrt__output __temp__ = __sqrt__x __temp__
function namespace_here:__lib__/__sqrt__loop
scoreboard players operation b global = null global
scoreboard players set c global 2374
scoreboard players operation cbrt_0 __temp__ = a global
scoreboard players operation __cbrt__x __temp__ *= __cbrt__4d3 __temp__
scoreboard players operation __cbrt__output __temp__ = __cbrt__x __temp__
function namespace_here:__lib__/__cbrt__loop
scoreboard players operation d global = null global
scoreboard players operation int_1 __temp__ = a global
scoreboard players operation int_1 __temp__ /= FLOAT_PREC __temp__
scoreboard players operation e global = int_1 __temp__
scoreboard players operation f global = a global
data modify storage variables myStr set value "hello"
execute store result score int_2 __temp__ run data get storage variables myStr
scoreboard players operation myStrLen global = int_2 __temp__
data modify storage variables myArr set value [1, 2, 3]
data modify storage variables myArr append value 4
data remove storage variables myArr[-1]
data modify storage variables myArr insert 0 value 5
execute store result score int_5 __temp__ run data get storage variables myArr
scoreboard players operation myArrLen global = int_5 __temp__
```

:::
