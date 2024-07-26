# Command Features

You can use variables and expressions inside commands with the $() macro.

Example:

```js
a = 3
say $(a + 5)
```

***

You can convert variables and expressions inside commands to tellraw objects by using the $str() macro.

Example:

```js
a = 3
tellraw @a $str(a + 5)
```

***

You can use multi line commands by using the `\` character. This character is used to terminate the new line character.

Example:

```js
execute as @a   \
           at @s    \
           run      \
           say hi!
```

***

You can also expand `execute` command with execute macros.

Example:

```js
as @a at @s {
    say Hello, world!
    tellraw @a $str(myVariable)
}
```
