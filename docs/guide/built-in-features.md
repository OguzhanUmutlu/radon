# Built-in features

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
- Math.floor(int | float): int
- Math.ceil(int | float): int
- Math.round(int | float): int
- Math.min(...(int | float)): int | float
- Math.max(...(int | float)): int | float
- Math.random(int min=1, int max=2147483647): int
- Math.frandom(int min=1, int max=2147483647): float

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

## Recipe.add(object)

<details>
<summary>Click to view</summary>

:::warning
This is a macro function, so it will run in compile time and bypass flow controls.
:::

</details>

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
