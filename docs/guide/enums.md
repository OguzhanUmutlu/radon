# Enums

Enums in Radon are basically a list of constant values. You can use enums in your code with the `enum` keyword. Here's
an all-in-one example:

```js
enum MyEnum {
  A,           // A = 0
  B(10),       // B = 10
  C,           // C = 11
  D(string),   // D = "D"
  E,           // E = "E"
  F(10, 5),    // F = 10
  G,           // G = 15
  H("hello"),  // H = "hello"
  I(1.5),      // I = 1.5
  J,           // J = 20
  K            // K = 25
}
```
