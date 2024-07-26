# Conditionals

Radon supports if else statements in the form `if (condition) { code } else { code }`.

Examples:

```js
if (a > b) {
    print('a is greater than b')
}
```

```js
if (a > b) {
    print('a is greater than b')
} else if (a < b) {
    print('a is less than b')
} else {
    print('a is equal to b')
}
```

```js
if (a > b) print('a is greater than b')
else if (a < b) print('a is less than b')
else print('a is equal to b')
```