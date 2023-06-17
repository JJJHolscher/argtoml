# README

The `argtoml` package wraps around `argparse`.
It adds the content of a toml file to the cli options.
After parsing, it creates a `types.SimpleNameSpace` object.

## install

```sh
pip install argtoml
```

## usage

If there's a `src/config.toml`

```toml
debug = true
home = "~"

[project]
author = "Jono"
name = "argconfig"
pyproject = "./pyproject.toml"
```

and a `src/__main__.py`

```python
from argtoml import parse_args  # , ArgumentParser

args = parse_args(path=True)
print(args.debug)
print(args.home)
print(args.project.author)
print(args.project.name)
print(args.project.pyproject)
```

then the shell can look like

```sh
$ pwd
/home/jono/project
$ python src/__main__.py --project.name argtoml --no-debug
False
/home/jono
Jono
argtoml
/home/jono/project/pyproject.toml
```

## packaging

`argtoml` works with a packaged toml file. You can provide it's path like this.

```python
arg_parse(toml="my_config.toml")
```

If you provide a relative path, `argtoml` will look for `my_config.toml` in the package directory if the main file using `argtoml` is from a package, otherwise `argtoml` will look for `my_config.toml` in the same directory as the main file.
If you want to ship a toml file with your package, make sure to [add the toml file to your package](https://setuptools.pypa.io/en/latest/userguide/datafiles.html).

## notes

This is a personal tool thus far, some idiosyncrasies remain:

- Adding dotted arguments not present in the toml might break everything I didn't even test this.
- I didn't test any arrays, they should work?
- I don't feel like adding other formats but toml.
- I don't know if, in the above example, the user can do something like `python __main__.py --project {author="jo3"} --project.author jjj`, but it should crash if they do this.
- Interpreting strings as paths _probably_ only works with unix style paths.

## todos

- Add toml comments as argument descriptions.
- Pretty-print the output of parse_args.
- Load and merge multiple toml files
