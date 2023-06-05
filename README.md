---
created_datetime: 2023-06-05T21:51:00
---

# README

The `argtoml` package wraps around `argparse`.
It adds the content of a toml file to the cli options.
After parsing, it creates a `types.SimpleNameSpace` object.

## usage

Use `argtoml` the same as you would use `argparse`.
If you don't provide the location for the toml file, it will search for one in the current directory or any parent directory of the main file (in)directly importing `argtoml`.

```python
from argtoml import ArgumentParser, arg_parse

parser = ArgumentParser()
parser.add_argument("--path", default="./")
parser.add_argument("--project.name", default="argtoml")
args = arg_parse(parser)
```

If we, for example have the following config.toml in the same directory as the above script

```toml
[project]
author = "Jono"
name = "argconfig"
```

then args is an object with the following entries.

```python
assert args.path == "./"
assert args.project.author == "Jono"
assert args.project.name == "argtoml"
```

## notes

This is a personal tool thus far, some idiosyncrasies remain:

- Adding dotted arguments not present in the toml might break everything I didn't even test this.
- I didn't test any arrays, they should work?
- I don't feel like adding other formats but toml.
- I don't know if, in the above example, the user can do something like `main.py --project {author=jo3} --project.author jjj`, but it should crash if they do this.

