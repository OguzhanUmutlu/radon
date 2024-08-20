# Classes

Classes in Radon are based on objects. You can overload functions in classes too.

Here's an example that creates a simple class and uses it:

```js
class MyClass {
  myFunction {
    print("Hello!")
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
print(myClass.myAttribute)
```

***

You can access of the class inside a class method by using the `this` and even change the
constructor function like this:

```js
class MyClass {
  myAttribute = 1
  
  MyClass(int myAttribute) {
    this.myAttribute = myAttribute
  }
  
  increaseMyAttribute() {
    this.myAttribute++
  }
}

myClass = MyClass()
myClass.increaseMyAttribute()
print(myClass.myAttribute)
```

***

You can also run the methods of your class inside a class method using the `this` variable like this:

```js
class MyClass {
  myOtherFunction() {
    print("Hello!")
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
    print("no arguments!")
  }
  
  myFunction(int arg) {
    print("argument: ", arg)
  }
}

myClass = MyClass()
myClass.myFunction()
myClass.myFunction(10)
```