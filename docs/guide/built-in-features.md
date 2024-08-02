# Built-in features

## Listener.on("firstJoin", callback)

Runs the callback when a player joins the world for the first time. Runs at and as the player.

```js
Listener.on("firstJoin", () => {
    print(@s, "Welcome!")
})
```

## Listener.on("join", callback)

Runs the callback when a player joins the world. Runs at and as the player.

```js
Listener.on("join", () => {
    print(@s, "Welcome!")
})
```

## Listener.on("rejoin", callback)

Runs the callback when a player rejoins the world. Runs at and as the player.

```js
Listener.on("rejoin", () => {
    print(@s, "Welcome back!")
})
```

## Listener.on("die", callback)

Runs the callback when a player dies. Runs at and as the player.

```js
Listener.on("die", () => {
    print(@s, "You died!")
})
```

## Listener.on("respawn", callback)

Runs the callback when a player respawns. Runs at and as the player.

```js
Listener.on("respawn", () => {
    print(@s, "You respawned!")
})
```

## Listener.on("carrot_on_a_stick", callback)

Runs when a player right clicks holding a carrot on a stick. Runs at and as the player.

```js
Listener.on("carrot_on_a_stick", () => {
    print(@s, "You clicked!")
})
```

## Listener.on("warped_fungus_on_a_stick", callback)

Runs when a player right clicks holding a warped fungus on a stick. Runs at and as the player.

```js
Listener.on("warped_fungus_on_a_stick", () => {
    print(@s, "You clicked!")
})
```

## Listener.on("any_scoreboard_event", callback)

Runs when any scoreboard event happens. Runs at and as the player.

```js
Listener.on("jump", () => {
    print(@s, "You jumped!")
})
```

## raycast(callback on_hit_entity = false, callback on_hit_block = false, callback on_fail = false)

Runs raycast at the current scope's position. Entity callback will be called as the entity. Block callback will be
called positioned at the block.

You can configure the starting position and rotation using the execute macros:

```js
as @p positioned 10 5 4 facing 8 5 2 {
    raycast(() => {
        print("uuid of the entity hit: ", UUID:@s)
    })
}
```

## Math.sqrt(int | float): float

Returns the square root of an int or float.

## Math.isqrt(int | float): int

Returns the integer square root of an int or float.

## Math.cbrt(int | float): float

Returns the cubic root of an int or float.

## Math.floor(int | float): int

Returns the floor of an int or float.

## Math.ceil(int | float): int

Returns the ceiling of an int or float.

## Math.round(int | float): int

Returns the round of an int or float.

## Math.min(...(int | float)): int | float

Returns the minimum of multiple ints or floats.

Return type is float if one of the arguments is a float, otherwise it is int.

## Math.max(...(int | float)): int | float

Returns the maximum of multiple ints or floats.

Return type is float if one of the arguments is a float, otherwise it is int.

## Math.random(int min=1, int max=2147483647): int

Returns a random int in the range [min, max].

## Recipe.add(object)

:::warning
This is a macro function, so it will run in compile time and bypass flow controls.
:::

## print(selector, ...any)

Prints the given values to the given selector.

## printTitle(selector, ...any)

Prints the given values to the given selector as a title.

## printSubtitle(selector, ...any)

Prints the given values to the given selector as a subtitle.

## printActionbar(selector, ...any)

Prints the given values to the given selector as an actionbar message.

## pyeval(pythonCode)

Executes the given python expression.

## pyexec(pythonCode)

Executes the given python code.

Adds the given object to the recipes.

## swap(non-literal, non-literal)

Executes the given python code.

Adds the given object to the recipes.

## success(minecraft command)

Returns whether the given minecraft command runs successfully.

## time(): int

Returns the current time in game ticks.

## ftime(): float

Returns the current time in seconds as a float.

## getpos(): float[]

Returns the current position the function is running from. Works by summoning a marker and using its Pos NBT.

## exit(any)

Lets you return in the main scope.

## true

Macro for 1.

## false

Macro for 0.

## null

Macro for 0.
