#! /usr/bin/env python3
# vim:fenc=utf-8

"""
Create an argument parser from a toml file.
"""

import os
import tomllib
from argparse import ArgumentParser
from pathlib import Path
from types import SimpleNamespace

import __main__


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
            parser.add_argument(f"--{prefix}{key}", required=False, type=type_, help=f"map of {key}")
            add_toml_args(parser, value, key + ".")
        else:
            parser.add_argument(f"--{prefix}{key}", required=False, type=type_, help=f"defaults to {value}")


def fill_toml_args(args, toml, prefix='', filled=False):
    namespace = SimpleNamespace()
    for key, value in toml.items():
        key_str = prefix + '.' + key if prefix else key
        arg_value = args[key_str] if key_str in args else None

        # Error if a nested value would overwrite an already-filled dictionary.
        if filled and arg_value is not None:
            raise Exception("You cannot overwrite a filled argument.")

        # Nest the namespace with a dictioray.
        if type(value) == dict:
            if arg_value is None:
                setattr(namespace, key, fill_toml_args(args, value, key, filled))
            else:
                # Check if values are not filled twice.
                setattr(namespace, key, fill_toml_args(args, arg_value, key, filled))
                fill_toml_args(args, value, key, True)
        # Fill in the default value.
        elif args[key_str] is None:
            setattr(namespace, key, value)
        # Fill in the value from the command line.
        else:
            setattr(namespace, key, arg_value)

        del args[key_str]

    return namespace


def parse_args(parser=ArgumentParser(), toml_path=None):
    """
    Add the content of a toml file as argument with default values
    to an ArgumentParser object.
    """

    if toml_path is None:
        toml_path = locate_toml()
    with open(toml_path, "rb") as f:
        toml = tomllib.load(f)
    add_toml_args(parser, toml)
    args = vars(parser.parse_args())

    namespace = fill_toml_args(args, toml)
    for key, value in args.items():
        setattr(namespace, key, value)

    return namespace
