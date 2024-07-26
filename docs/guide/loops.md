# Loops

There are 6 types of loops: `loop`, `while`, `until`, `do-while`, `do-until`, `for`.

You can break out of the current loop using the `break` keyword. You can also continue the loop in the next iteration
using the `continue` keyword.

You can give a timer to the loop by putting a minecraft timestamp after the loop's keyword. Like
this: `loop 1t { code }` (1t standing for 1 tick)

## Infinite loop

The `loop` loop is an infinite loop.

```js
loop {
  print("Hello, world!")
}
```

## While loop

The `while` loop executes a block of code as long as a condition is not equal to 0.

The following example will print the numbers from 1 to 10:

```js
a = 10
while (a) {
  print("A: ", a)
  a--
}
```

## Do-while loop

The `do-while` loop executes a block of code and after the first iteration the block of code is executed if the
condition is not equal to 0.

The following example will print the numbers from 1 to 10:

```js
a = 10
do {
  print("A: ", a)
  a--
} while (a)
```

## Until loop

The `until` loop executes a block of code until a condition is not equal to 0.

The following example will print the numbers from 1 to 10:

```js
a = 10
until (a == 0) {
  print("A: ", a)
}
```

## Do-until loop

The `do-until` loop executes a block of code and after the first iteration the block of code is executed until the
condition is not equal to 0.

The following example will print the numbers from 1 to 10:

```js
a = 10
do {
  print("A: ", a)
} until (a == 0)
```

## For loop

The `for` loop executes an initial block of code, then executes a block of code if the condition is not equal to 0, and
finally executes another block of code.

The following example will print the numbers from 1 to 10:

```js
for (a = 1; a <= 10; a++) {
  print("A: ", a)
}
```

