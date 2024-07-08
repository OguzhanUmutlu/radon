# Radon

Radon is a programming language that gets compiled to Minecraft: Java Edition's mcfunction files.

## Usage

Install the repository by clicking `Code` then `Download ZIP` and then extract it. Alternatively you can use `git clone https://github.com/OguzhanUmutlu/radon` command to install it.

Once it's installed you can run the `main.py` command with the path of your file. Example: `python3 main.py /usr/code.radon`

This should create a datapack with a folder name of `build/` in the directory of your radon file.

You can change the name of the folder and datapack like this:

```shell
python3 main.py /usr/code.radon -o=my_folder -n="My Datapack's Name" -d="This is the description of my datapack."
```

## Syntax

```js
a = 10
a += 10
a -= 10
a *= 10
a /= 10
a++
a--

// To run commands just type them:
say hi

// Multi line commands are available, you can break the new line character with backslash:
execute       \
  as @a       \
  at @s       \
  run say hi

define int b // If you don't want to initialize a variable, you can use this

a += c - (b * 10) / (b + 7) // Supports mathematical expressions

a = 10.5
a += 5.23

a:@s = 10 // sets it for @s

a:@s // gets it from @s

function my_func(float x, float y, float z): float {
    tp @a $(x) $(y) $(z)
    return x + y + z
}

my_func(1, 2, 3)

function tick {
    // This will run every tick
}

as @p at @s {
}

if (a == 1) {
} else if (a == 2) {
} else {
}

unless (a == 1) { // This is a shortcut for: if (a == 1) {} else { say hi }
  say hi
}

schedule 1t {
}

loop {
}

for (i = 0; i < 10; i++) {
}

while (a == 1) {
}

until (a == 1) {
}

do {
} while (a == 1)

do {
} until (a == 1)

loop 1t {
}

for 1t (i = 0; i < 10; i++) {
}

while 1t (a == 1) {
}

until 1t (a == 1) {
}

do {
} while 1t (a == 1)

do {
} until 1t (a == 1)

// break and continue can be used in any loop like this:

loop {
    if (a == 1) break // Exits the loop
    if (a == 2) continue // Stops the loop and restarts from the first line of the loop
}
```