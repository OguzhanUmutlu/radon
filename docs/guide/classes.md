# Classes

Classes in Radon are based on objects. You can overload functions in classes too.

Here's an example that creates a simple class and uses it:

```js
class MyClass {
  myFunction {
    print(@a, "Hello!")
  }
}

myClass = MyClass()
myClass.myFunction()
```

***

You can add attributes to the class like this:

```js
class MyClass {
  myAttribute = 1
}

myClass = MyClass()
print(@a, myClass.myAttribute)
```

***

You can access of the class inside a class method by using the `this` variable like this:

```js
class MyClass {
  myAttribute = 1
  
  increaseMyAttribute() {
    this.myAttribute++
  }
}

myClass = MyClass()
myClass.increaseMyAttribute()
print(@a, myClass.myAttribute)
```

***

You can also run the methods of your class inside a class method using the `this` variable like this:

```js
class MyClass {
  myOtherFunction() {
    print(@a, "Hello!")
  }
  
  myFunction() {
    this.myOtherFunction()
  }
}

myClass = MyClass()
myClass.myFunction()
```

***

An example of overloading functions in classes:

```js
class MyClass {
  myFunction() {
    print(@a, "no arguments!")
  }
  
  myFunction(int arg) {
    print(@a, "argument: ", arg)
  }
}

myClass = MyClass()
myClass.myFunction()
myClass.myFunction(10)
```