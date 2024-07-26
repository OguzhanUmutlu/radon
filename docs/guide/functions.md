# Functions

Functions in Radon can be defined in various ways. Check the [built-in functions](./built-in-functions) page to see the
list and usage of built-in functions.

A simple function that prints `Hello, world!` to the chat:

```js
fn myFunction {
  print("Hello, world!")
}

myFunction()
```

***

Functions can have arguments, which are forced to have types:

```js
fn calcAdd(int a, int b) {
  return a + b
}

c = calcAdd(10, 20)
```

***

Function arguments can be overloaded:

```js
fn myOverloadingFunction(int a, int b) {
  return a
}

fn myOverloadingFunction(float a, float b) {
  return b
}

x = myOverloadingFunction(10, 20) // gives 10
y = myOverloadingFunction(10.0, 20.0) // gives 20.0
```

***

Calculating nth fibonacci number:

```js
fn fibonacci(int n) {
  a = 0
  b = 1
  i = 1
  loop {
    if (i == n) break
    c = a + b
    a = b
    b = c
    i++
  }
  return a
}

10thFibonacci = fibonacci(10)
```