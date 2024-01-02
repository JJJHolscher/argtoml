# README

The `argtoml` package wraps around `argparse`.
It adds the content of a toml file to the cli options.
After parsing, it creates a `types.SimpleNameSpace` object.

## install

Argtoml has no mandatory dependencies outside of pythons standard library.
```sh
pip install argtoml
```
You can optionally install `tomli_w` if you want to save your configuration at runtime.
```sh
pip install 'argtoml[save]'
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

## documentation

There is none, the code is not that large, but I expect you to only use:
```python
parse_args(
  # An argparse parser for adding extra arguments not present in the toml.
  parser: Optional[argparse.ArumentParser] = None,
  # An extra help message.
  description: str = "",
  # The location of the toml file.
  toml_path: pathlib.Path = Path("config.toml"),
  # The dictionary in which to look for the toml file.
  toml_dir: Optional[TPath] = None,
  # Whether to try to interpret strings as paths.
  base_path: Union[Path, bool] = True,
  # Whether to look for the toml file in the parent of the toml_dir folder.
  grandparent: bool = True
) -> SimpleNamespace

save(args: Union[SimpleNamespace, dict], path: pathlib.Path):
  with open(path, "wb") as f:
    tomli_w.dump(args, f)
```


## toml file location

You are encouraged to specify the location of the toml file when calling `parse_args` with an absolute path like this:

```python
parse_args(toml_path="/home/user/dir/my_config.toml")
```

If you provide a relative path, `argtoml` will look for `my_config.toml` in the package directory if the main file using `argtoml` is from a package, otherwise `argtoml` will look for `my_config.toml` in the same directory as the main file.
This automatic toml-finding function might change in the future, so probably just provide absolute paths.

### packaging

If you want to ship a toml file with your package, make sure to [add the toml file to your package](https://setuptools.pypa.io/en/latest/userguide/datafiles.html).
You should also call `parse_args` with a relative `toml_path`.

## notes

This is a personal tool thus far, some idiosyncrasies remain:

- Adding dotted arguments not present in the toml might break everything I didn't even test this.
- I don't feel like adding other formats but toml.
- I don't know if, in the above example, the user can do something like `python __main__.py --project {author="jo3"} --project.author jjj`, but it should crash if they do this.
- Interpreting strings as paths _probably_ only works with unix style paths.

## todos

- Add toml comments as argument descriptions.
- Pretty-print the output of parse_args.
- Load and merge multiple toml files
