# Getting Started

## Overview

Radon is a programming language that aims to provide a faster and leaner development
experience for datapacks.

Radon comes with sensible defaults out of the box. The [Config Section](./config) explains how to configure your
project if needed.

## Scaffolding Your First Radon Project

Before everything make sure that you have a recent version of Python installed.

If you don't have Radon installed, you can install it with `pip install radonmc`.

Now you can just run the command `radon`.

And that's it! This will set up your project for you in the current directory!

Immediately afterward it will build the datapack!

### Specifying Alternative Root

Running `radon` builds the datapack using the current working directory as root. You can specify an alternative
root by changing the `outFolder` in your `radon.json`.

## Viewing/Editing Radon Locally

If you can't wait for a new release to test the latest features, or you want to edit Radon's source code, you will
need to clone the [Radon repo](https://github.com/OguzhanUmutlu/radon) to your local machine and then build and link it
yourself:

```bash
git clone https://github.com/OguzhanUmutlu/radon.git
cd radon
python -m src.radon
```

That's it! This will run your project using the latest(possibly unreleased) version of Radon!

## Community

If you have questions or need help, reach out to the community at [Discord](https://discord.gg/xYjXnDp6h3)
and [GitHub Discussions.](https://github.com/OguzhanUmutlu/radon/discussions)
