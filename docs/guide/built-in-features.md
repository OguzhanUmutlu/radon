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

## raycast(callback on_hit_entity = null, callback on_hit_block = null, callback on_step = null, callback on_fail = null)

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

## Math

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
