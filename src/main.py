#! /usr/bin/env python3
# vim:fenc=utf-8

"""
Create an argument parser from a toml file.
"""

import builtins
import importlib
import os
import tomllib
from argparse import ArgumentParser
from ast import literal_eval
from importlib.resources import as_file, files
from importlib.resources.abc import Traversable
from pathlib import Path
from types import SimpleNamespace
from typing import Optional, Tuple, Union

import __main__

TPath = Union[Traversable, Path]
TOML_PATH: TPath
try:
    get_ipython
    IPYTHON = True
except:
    IPYTHON = False


class Struct:
    def __init__(self, **entries):
        self.__dict__.update(entries)

    def __repr__(self):
        return "<%s>" % str(
            "\n ".join("%s : %s" % (k, repr(v)) for (k, v) in self.__dict__.items())
        )


def string_to_path(string: str, prefix: Path) -> Union[Path, str]:
    """
    Convert a string to a Path object.
    """
    if string == "~":
        return Path.home()

    elif string == ".":
        return prefix

    elif string == "..":
        return prefix.parent

    elif len(string) > 0 and string[0] == "/":
        return Path(string)

    elif len(string) > 1 and string[0:2] == "~/":
        return Path.home() / string[2:]

    elif len(string) > 1 and string[0:2] == "./":
        return prefix / string[2:]

    elif len(string) > 2 and string[0:3] == "../":
        return prefix.parent / string[3:]

    else:
        return string


def locate_toml_path(file_name: Path, parent_dir: bool) -> Tuple[TPath, TPath]:
    """
    Locate the toml file in the current directory.
    """
    # Have toml_dir be the package dir if argtoml is called from a package.
    if __main__.__package__:
        toml_dir = files(__main__.__package__)
        if parent_dir:
            toml_dir = toml_dir.joinpath(Path(".."))
        return toml_dir.joinpath(file_name), toml_dir

    # Use the folder of the main file as toml_dir.
    elif "__file__" in dir(__main__):
        toml_dir = Path(__main__.__file__).parent
        if parent_dir:
            toml_dir = toml_dir.parent
        return toml_dir / file_name, toml_dir

    # Find the path of the ipython notebook.
    elif IPYTHON:
        try:
            import ipynbname

            toml_dir = ipynbname.path().parent
            if parent_dir:
                toml_dir = toml_dir.parent
            return toml_dir / file_name, toml_dir

        except IndexError:
            toml_dir = Path(os.path.abspath("."))
            return toml_dir / file_name, toml_dir

    raise NotImplementedError


def add_toml_args(parser, toml, prefix=""):
    """
    Add the content of a toml file as argument with default values
    to an ArgumentParser object.
    """
    for key, value in toml.items():
        type_ = type(value)
        if type_ == dict:
            parser.add_argument(
                f"--{prefix}{key}", required=False, type=str, help=f"map"
            )
            add_toml_args(parser, value, key + ".")
        elif type_ == list:
            parser.add_argument(
                f"--{prefix}{key}", required=False, type=str, help=f"list"
            )
        elif type_ == bool:
            parser.add_argument(
                f"--{prefix}{key}", required=False, action="store_const", const=True
            )
            parser.add_argument(
                f"--{prefix}no-{key}", required=False, action="store_const", const=True
            )
        else:
            parser.add_argument(
                f"--{prefix}{key}",
                required=False,
                type=type_,
                help=f"defaults to {value}",
            )


def fill_toml_args(args, toml, prefix="", filled=False, path: Optional[Path] = None):
    namespace = SimpleNamespace()
    for raw_key, value in toml.items():
        # Check if the user provided the same key but with dashes instead of underscores.
        key = raw_key.replace("-", "_")
        key_str = prefix + "." + key if prefix else key
        # Boolean variables have 2 arguments.
        alt_key_str = prefix + ".no_" + key if prefix else "no_" + key
        if namespace.__dict__.get(key) is not None:
            dash_key = prefix + "." + raw_key if prefix else raw_key
            raise KeyError(
                f"Because '-' is converted to '_', you cannot both have --{key_str} and --{dash_key} in {TOML_PATH}."
            )

        arg_value = args[key_str] if key_str in args else None

        # Fill in the default value from the toml file.
        if arg_value is None:
            if type(value) == dict:
                setattr(
                    namespace, key, fill_toml_args(args, value, key, filled, path=path)
                )
            # Check whether both boolean arguments are empty before filling in the default.
            elif type(value) == bool:
                if args[alt_key_str] is None:
                    setattr(namespace, key, value)  # Fill in the default.
                else:
                    setattr(namespace, key, False)  # The anti-argument was called.
                    del args[alt_key_str]

            elif path is not None and type(value) == str:
                setattr(namespace, key, string_to_path(value, path))

            else:
                setattr(namespace, key, value)

        # Fill in the value from the command line.
        else:
            if filled:
                raise Exception(
                    f"Argument {key_str} is filled twice. Don't use the argument of a parent and it's child."
                )

            try:
                match type(value):
                    case builtins.list:
                        arg_value = literal_eval(arg_value)
                        assert type(arg_value) == list
                        for i, arg in enumerate(arg_value):
                            if type(arg) == dict:
                                # TODO; I might need to check for whether any values are filled twice.
                                arg_value[i] = fill_toml_args(
                                    args, arg, key, filled, path=path
                                )

                    case builtins.dict:
                        # Check if values are not filled twice.
                        fill_toml_args(args, value, key, True, path=path)
                        arg_value = literal_eval(arg_value)
                        assert type(arg_value) == dict
                        arg_value = fill_toml_args(
                            args, arg_value, key, filled, path=path
                        )

                    case builtins.bool:
                        assert type(arg_value) == bool
                        if args[alt_key_str] is not None:
                            raise ValueError(
                                f"Do not call --{key_str} and --{alt_key_str} simultaneously."
                            )
                    case builtins.str:
                        assert type(arg_value) == str
                        arg_value = (
                            string_to_path(arg_value, path)
                            if path is not None
                            else arg_value
                        )

                    case _:
                        assert type(value) == type(arg_value)

            except AssertionError:
                raise TypeError(
                    f"Type mismatch for {key_str}: the type from {TOML_PATH} is {type(value)}, but the CLI got a {type(arg_value)}"
                )

            setattr(namespace, key, arg_value)
            del args[key_str]

    return namespace


def parse_args(
    parser: Optional[ArgumentParser] = None,
    description: str = "",
    toml_path: Path = Path("config.toml"),
    toml_dir: Optional[TPath] = None,
    base_path: Union[Path, bool] = True,
    grandparent: Optional[bool] = None,
) -> SimpleNamespace:
    """
    Add the content of a toml file as argument with default values
    to an ArgumentParser object.

    Args:
        parser: ArgumentParser object that can be pre-filled.
        description: an description if the ArgumentParser is not given.
        toml_path: a relative or absolute path to the toml file.
        toml_dir: the absolute path to the parent directory of the toml file.
        base_path: the prefix to prepend to relative paths from the toml file.
            if False: never interpret toml file string values as paths.
            if True: use the toml_dir as prefix.
        grandparent: use grandparent directory of the file calling argtoml
            instead of parent directory. Defaults to True if argtoml is not called from ipython.
    Out:
        A (nested) SimpleNamespace object filled with cli argument values that defaults
        to values from the toml file.
    """

    global TOML_PATH
    grandparent = grandparent if grandparent is not None else not IPYTHON

    if type(toml_dir) == Path:
        TOML_PATH = Path(toml_dir) / Path(toml_path)
    elif toml_path.is_absolute():
        TOML_PATH = toml_path
        toml_dir = TOML_PATH.parent
    else:
        TOML_PATH, toml_dir = locate_toml_path(toml_path, grandparent)

    with open(TOML_PATH, "rb") as f:
        toml_doc = tomllib.load(f)

    if IPYTHON:
        assert parser is None
        args = dict()
    # Add the keys from the toml file as arguments.
    else:
        if parser is None:
            parser = ArgumentParser(
                description=description
                + f"\nCLI arguments are constructed from {TOML_PATH}. View that file for more documentation"
            )
        add_toml_args(parser, toml_doc)
        args = vars(parser.parse_args())

    if base_path == True:
        base_path = Path(str(toml_dir))

    if base_path:
        namespace = fill_toml_args(args, toml_doc, path=base_path)
    else:
        namespace = fill_toml_args(args, toml_doc)

    for key, value in args.items():
        if value is not None:
            setattr(namespace, key, value)

    return namespace
