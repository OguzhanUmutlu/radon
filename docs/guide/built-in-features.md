# Built-in features

## print(selector, ...any)

<details>
<summary>Click to view</summary>

Prints the given values to the given selector.

</details>

## printTitle(selector, ...any)

<details>
<summary>Click to view</summary>

Prints the given values to the given selector as a title.

</details>

## printSubtitle(selector, ...any)

<details>
<summary>Click to view</summary>

Prints the given values to the given selector as a subtitle.

</details>

## printActionbar(selector, ...any)

<details>
<summary>Click to view</summary>

Prints the given values to the given selector as an actionbar message.

</details>

## Math

<details>
<summary>Click to view</summary>

- Math.sqrt(int | float): float
- Math.isqrt(int | float): int
- Math.cbrt(int | float): float
- Math.exp(int | float): float
- Math.fastexp(int | float): float
- Math.ipow(int | float, int): int | float
- Math.sin(int | float): float
- Math.cos(int | float): float
- Math.tan(int | float): float
- Math.arcsin(int | float): float
- Math.arccos(int | float): float
- Math.arctan(int | float): float
- Math.fastarcsin(int | float): float
- Math.fastarccos(int | float): float
- Math.fastarctan(int | float): float
- Math.factorial(int | float): int
- Math.floor(int | float): int
- Math.ceil(int | float): int
- Math.round(int | float): int
- Math.min(...(int | float)): int | float
- Math.max(...(int | float)): int | float
- Math.random(int min=1, int max=2147483647): int
- Math.frandom(int min=1, int max=2147483647): float

</details>

## Formatting texts

<details>

<summary>Click to view</summary>

In radon, you can print text to the chat using the `print()` function. Formatted texts allow you to make the output
colored, underlined, bold etc. Here's a simple example that prints a red and bold text with the content `Hello, world!`:

::: code-group

```js
print( fmt(red, bold, "Hello, world!") )
```

```mcfunction
tellraw @a {"text":"Hello, world!","color":"red","bold":true}
```

:::

To add text events like `click` or `hover` you can use the `.click` and `.hover` functions attached to the `fmt()`
function call. Here's a simple example that redirects the player to Radon's documentation when they click on the text:

::: code-group

```js
print(
    fmt("Click me to view the Radon documentation!")
        .click("open_url", "https://oguzhanumutlu.github.io/radon")
        .hover("open_url", "https://oguzhanumutlu.github.io/radon")
)
```

```mcfunction
tellraw @a {"text":"Click me to view the Radon documentation!","clickEvent":{"action":"open_url","value":"https://oguzhanumutlu.github.io/radon"},"hoverEvent":{"action":"open_url","contents":"https://oguzhanumutlu.github.io/radon"}}
```

You can also add child text components by using the `.extend` function attached to the `fmt()` function call. Child
components will inherit the style of the parent. Here's a simple example that prints a red `Hello` and a red
bold `world`:

::: code-group

```js
print(
    fmt(red, "Hello, ")
        .extend(
            fmt(bold, "world!")
        )
)
```

```mcfunction
tellraw @a {"text":"Hello, ","color":"red","extra":[{"text":"world!","bold":true}]}
```

:::

Here's an example that includes everything that `fmt()` can offer:

::: code-group

```js
print(
    fmt(red, "Hello, ")
        .extend(
            fmt(bold, "world!")
                .hover("open_url", "https://oguzhanumutlu.github.io/radon")
                .click("open_url", "https://oguzhanumutlu.github.io/radon")
        )
)

// Every style

print(fmt(#123456, "Custom colored text"))
print(fmt(black, "Black text"))
print(fmt(dark_blue, "Dark blue text"))
print(fmt(dark_green, "Dark green text"))
print(fmt(dark_aqua, "Dark aqua text"))
print(fmt(dark_red, "Dark red text"))
print(fmt(dark_purple, "Dark purple text"))
print(fmt(gold, "Gold text"))
print(fmt(gray, "Gray text"))
print(fmt(dark_gray, "Dark gray text"))
print(fmt(blue, "Blue text"))
print(fmt(green, "Green text"))
print(fmt(aqua, "Aqua text"))
print(fmt(red, "Red text"))
print(fmt(light_purple, "Light purple text"))
print(fmt(yellow, "Yellow text"))
print(fmt(white, "White text"))
print(fmt(bold, "Bold text"))
print(fmt(italic, "Italic text"))
print(fmt(underlined, "Underlined text"))
print(fmt(strikethrough, "Strikethrough text"))
print(fmt(obfuscated, "Obfuscated text"))
```

```mcfunction
tellraw @a {"text":"Hello, ","color":"red","extra":[{"text":"world!","bold":true,"hoverEvent":{"action":"open_url","contents":"https://oguzhanumutlu.github.io/radon"},"clickEvent":{"action":"open_url","value":"https://oguzhanumutlu.github.io/radon"}}]}
tellraw @a {"text":"Custom colored text","color":"#123456"}
tellraw @a {"text":"Black text","color":"black"}
tellraw @a {"text":"Dark blue text","color":"dark_blue"}
tellraw @a {"text":"Dark green text","color":"dark_green"}
tellraw @a {"text":"Dark aqua text","color":"dark_aqua"}
tellraw @a {"text":"Dark red text","color":"dark_red"}
tellraw @a {"text":"Dark purple text","color":"dark_purple"}
tellraw @a {"text":"Gold text","color":"gold"}
tellraw @a {"text":"Gray text","color":"gray"}
tellraw @a {"text":"Dark gray text","color":"dark_gray"}
tellraw @a {"text":"Blue text","color":"blue"}
tellraw @a {"text":"Green text","color":"green"}
tellraw @a {"text":"Aqua text","color":"aqua"}
tellraw @a {"text":"Red text","color":"red"}
tellraw @a {"text":"Light purple text","color":"light_purple"}
tellraw @a {"text":"Yellow text","color":"yellow"}
tellraw @a {"text":"White text","color":"white"}
tellraw @a {"text":"Bold text","bold":true}
tellraw @a {"text":"Italic text","italic":true}
tellraw @a {"text":"Underlined text","underlined":true}
tellraw @a {"text":"Strikethrough text","strikethrough":true}
tellraw @a {"text":"Obfuscated text","obfuscated":true}
```

</details>

## Listener.on("firstJoin", callback)

<details>
<summary>Click to view</summary>

Runs the callback when a player joins the world for the first time. Runs at and as the player.

```js
Listener.on("firstJoin", () => {
    print(@s, "Welcome!")
})
```

</details>

## Listener.on("join", callback)

<details>
<summary>Click to view</summary>

Runs the callback when a player joins the world. Runs at and as the player.

```js
Listener.on("join", () => {
    print(@s, "Welcome!")
})
```

</details>

## Listener.on("rejoin", callback)

<details>
<summary>Click to view</summary>

Runs the callback when a player rejoins the world. Runs at and as the player.

```js
Listener.on("rejoin", () => {
    print(@s, "Welcome back!")
})
```

</details>

## Listener.on("die", callback)

<details>
<summary>Click to view</summary>

Runs the callback when a player dies. Runs at and as the player.

```js
Listener.on("die", () => {
    print(@s, "You died!")
})
```

</details>

## Listener.on("respawn", callback)

<details>
<summary>Click to view</summary>

Runs the callback when a player respawns. Runs at and as the player.

```js
Listener.on("respawn", () => {
    print(@s, "You respawned!")
})
```

</details>

## Listener.on("carrot_on_a_stick", callback)

<details>
<summary>Click to view</summary>

Runs when a player right clicks holding a carrot on a stick. Runs at and as the player.

```js
Listener.on("carrot_on_a_stick", () => {
    print(@s, "You clicked!")
})
```

</details>

## Listener.on("warped_fungus_on_a_stick", callback)

<details>
<summary>Click to view</summary>

Runs when a player right clicks holding a warped fungus on a stick. Runs at and as the player.

```js
Listener.on("warped_fungus_on_a_stick", () => {
    print(@s, "You clicked!")
})
```

</details>

## Listener.on("any_scoreboard_event", callback)

<details>
<summary>Click to view</summary>

Runs when any scoreboard event happens. Runs at and as the player.

```js
Listener.on("jump", () => {
    print(@s, "You jumped!")
})
```

</details>

## raycast(callback on_hit_entity = null, callback on_hit_block = null, callback on_step = null, callback on_fail = null)

<details>
<summary>Click to view</summary>

Runs raycast at the current scope's position. Entity callback will be called as the entity. Block callback will be
called positioned at the block.

You can configure the starting position and rotation using the execute macros:

```js
as @p positioned 10 5 4 facing 8 5 2 {
    success = raycast(() => {
        print("Hit an entity with the following uuid: ", @s.UUID)
    }, () => {
        print("Hit a block at the following position: ", getpos())
    }, () => {
        print("Raycaster is stepping...")
    }, () => {
        print("Raycaster didn't hit anything! Infinity and beyond...")
    })
    
    print("Raycaster's succession as a boolean: ", success)
}
```

</details>

## Data.get(type, location)

<details>
<summary>Click to view</summary>

Returns the value at the given location.

Examples:

```js
a = Data.get(int, @s.SelectedItem.count)
```

</details>

## Data.set(location, expression)

<details>
<summary>Click to view</summary>

Sets the value at the given location.

Examples:

```js
a = 5
Data.set(@s.Health, 10 + 5 - a)
```

</details>

## Data.append(location, expression)

<details>
<summary>Click to view</summary>

Appends the value at the given location.

Examples:

```js
a = 5
Data.append(some_storage path, 10 + 5 - a)
```

</details>

## Data.merge(location, expression)

<details>
<summary>Click to view</summary>

Merges the value at the given location.

Examples:

```js
Data.merge(@s, {Health: 10})
Data.merge(@s.attributes, [{"id": "minecraft:generic.movement_speed", "base": 0.1}])
```

</details>

## Recipe.add(object)

<details>
<summary>Click to view</summary>

:::warning
This is a macro function, so it will run in compile time and bypass flow controls.
:::

</details>

## pyeval(pythonCode)

<details>
<summary>Click to view</summary>

Executes the given python expression.

</details>

## pyexec(pythonCode)

<details>
<summary>Click to view</summary>

Executes the given python code.

Adds the given object to the recipes.

</details>

## swap(non-literal, non-literal)

<details>
<summary>Click to view</summary>

Executes the given python code.

Adds the given object to the recipes.

</details>

## success(minecraft command)

<details>
<summary>Click to view</summary>

Returns whether the given minecraft command runs successfully.

</details>

## time(): int

<details>
<summary>Click to view</summary>

Returns the current time in game ticks.

</details>

## ftime(): float

<details>
<summary>Click to view</summary>

Returns the current time in seconds as a float.

</details>

## getpos(): float[]

<details>
<summary>Click to view</summary>

Returns the current position the function is running from. Works by summoning a marker and using its Pos NBT.

</details>

## exit(any)

<details>
<summary>Click to view</summary>

Lets you return in the main scope.

</details>

## true

<details>
<summary>Click to view</summary>

Macro for 1.

</details>

## false

<details>
<summary>Click to view</summary>

Macro for 0.

</details>

## null

<details>
<summary>Click to view</summary>

Macro for 0.

</details>

## vset(expression, value)

<details>
<summary>Click to view</summary>

Sets the value of a variable. Allows macros.

Examples:

```js
a = 10
b = 3
vset(a, $(b + 10)$(b + 5))
```

</details>

## mset(expression, data location)

<details>
<summary>Click to view</summary>

Sets the value of a variable from a data location. Allows macros.

Examples:

```js
a = 10
mset(a, player_storage points."$(@s.UUID)")
```

</details>

## mstr(macro)

<details>
<summary>Click to view</summary>

Gives the result of the given input as a string using vanilla macros.

Examples:

```js
b = 10
c = 20
d = "hello!"

result = mstr(b is: $(b), c is: $(c), d is: $(d))
// result = "b is: 10, c is: 20, d is: hello!"
```

</details>
