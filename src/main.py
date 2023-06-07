#! /usr/bin/env python3
# vim:fenc=utf-8

"""
Create an argument parser from a toml file.
"""

import builtins
import os
import tomllib
from argparse import ArgumentParser
from ast import literal_eval
from pathlib import Path
from types import SimpleNamespace

import __main__

TOML_PATH = ""


class Struct:
    def __init__(self, **entries):
        self.__dict__.update(entries)

    def __repr__(self):
        return "<%s>" % str(
            "\n ".join("%s : %s" % (k, repr(v)) for (k, v) in self.__dict__.items())
        )


def locate_toml():
    """
    Locate the toml file in the current directory.
    """
    # The toml file can be named config.toml or have the same name as the main file..
    main_file = Path(__main__.__file__)
    toml_file_names = ["config.toml"]
    if main_file.name != "main.py":
        toml_file_names.append(main_file.stem + ".toml")

    # The toml file can also be named after the project directory.
    dir = main_file.parent
    if dir.name != "/":
        if dir.name == "src":
            toml_file_names.append(dir.parent.name + ".toml")
        else:
            toml_file_names.append(dir.name + ".toml")

    # Search for the toml file in the current directory.
    for file in os.listdir("."):
        if file in toml_file_names:
            return file

    # Search for the toml file in the project directory or its parents.
    while dir.name != "/":
        for file in os.listdir(dir):
            if file in toml_file_names:
                return os.path.join(dir, file)
        dir = dir.parent

    raise FileNotFoundError("No toml config file found current, or project directory")


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
        else:
            parser.add_argument(
                f"--{prefix}{key}",
                required=False,
                type=type_,
                help=f"defaults to {value}",
            )


def fill_toml_args(args, toml, prefix="", filled=False):
    namespace = SimpleNamespace()
    for raw_key, value in toml.items():
        # Check if the user provided the same key but with dashes instead of underscores.
        key = raw_key.replace("-", "_")
        key_str = prefix + "." + key if prefix else key
        if namespace.__dict__.get(key) is not None:
            dash_key = prefix + "." + raw_key if prefix else raw_key
            raise KeyError(
                f"Because '-' is converted to '_', you cannot both have {key_str} and {dash_key} in {TOML_PATH}."
            )

        arg_value = args[key_str] if key_str in args else None

        # Fill in the default value from the toml file.
        if arg_value is None:
            if type(value) == dict:
                setattr(namespace, key, fill_toml_args(args, value, key, filled))
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
                                arg_value[i] = fill_toml_args(args, arg, key, filled)

                    case builtins.dict:
                        # Check if values are not filled twice.
                        fill_toml_args(args, value, key, True)
                        arg_value = literal_eval(arg_value)
                        assert type(arg_value) == dict
                        arg_value = fill_toml_args(args, arg_value, key, filled)

                    case _:
                        assert type(value) == type(arg_value)

            except AssertionError:
                raise TypeError(
                    f"Type mismatch for {key_str}. The type from {TOML_PATH} is {type(value)}, but the cli got an argument of type {type(arg_value)}"
                )

            setattr(namespace, key, arg_value)
            del args[key_str]

    return namespace


def parse_args(parser=ArgumentParser(), toml=None):
    """
    Add the content of a toml file as argument with default values
    to an ArgumentParser object.
    """

    # Locate the toml file.
    global TOML_PATH
    if toml is None:
        toml = locate_toml()
        TOML_PATH = toml

    # Add the keys from the toml file as arguments.
    with open(toml, "rb") as f:
        toml = tomllib.load(f)
    add_toml_args(parser, toml)
    args = vars(parser.parse_args())

    namespace = fill_toml_args(args, toml)
    for key, value in args.items():
        if value is not None:
            setattr(namespace, key, value)

    return namespace
