#! /usr/bin/env python3
# vim:fenc=utf-8

from argparse import ArgumentParser
from ast import literal_eval
import copy
from pathlib import Path
import tomllib
from typing import Optional, Union, get_args

Opt = Union[dict, list]


def iter_opt(opt: Opt):
    if type(opt) is list:
        for i, v in enumerate(opt):
            yield i, v
    elif type(opt) is dict:
        for k, v in opt.items():
            yield k, v
    else:
        raise TypeError


def string_to_path(string: str, prefix: Path) -> Union[str, Path]:
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

    return string


def merge_opts(old: Opt, add: Opt, path: Optional[Path]):
    new = copy.deepcopy(old)

    for k, v in iter_opt(add):
        if type(v) is str and path is not None:
            v = string_to_path(v, path)

        if k in old:
            # Check whether identical keys have values of the same type.
            assert type(old[k]) is type(v)
            old_v = old[k]
        else:
            old_v = {}

        if isinstance(v, get_args(Opt)):
            new[k] = merge_opts(old_v, v, path)  #type:ignore
        else:
            new[k] = v

    return new


def opt_to_argument_parser(
    opt: Opt, parser: ArgumentParser, prefix="--"
) -> ArgumentParser:
    """
    Add the content of a toml file as argument with default values
    to an ArgumentParser object.
    """
    for k, v in iter_opt(opt):
        t = type(v)
        # Shorten single-character arguments to have a single dash.
        key_str = prefix + str(k)
        if len(key_str) == 3:
            key_str = key_str[1:]

        if isinstance(v, get_args(Opt)):
            parser.add_argument(
                key_str, required=False, type=str, help=str(t)
            )
            opt_to_argument_parser(v, parser, f"{prefix}{k}.")
        elif t is bool:
            parser.add_argument(
                key_str,
                required=False,
                action="store_const",
                const=True
            )
            parser.add_argument(
                f"{prefix}no-{k}",
                required=False,
                action="store_const",
                const=True
            )
        else:
            parser.add_argument(
                key_str,
                required=False,
                type=t,
                help=f"defaults to {v}",
            )
    return parser


def travel_opt(keys: list, opt: Opt, reference: Opt, value=None):
    """ Recursively apply all keys to the opt and then return or set the value.

    Raises:
        IndexError: The reference variable missed an object that was about to
            be indexed into. This likely means that some value of the opt was
            about to be accessed or edited after it already was edited.
    """
    key = keys[0]
    if len(keys) == 1:
        if value is not None:
            if type(reference[key]) is not type(value):
                raise TypeError(f"""
                    {key} is originally a {type(reference[key])}, but is to
                    become a {type(value)}.
                """)
            print(key, reference[key])
            del reference[key]
            opt[key] = value
        else:
            return opt[key]
    else:
        if key not in reference and value is not None:
            raise KeyError(f"{key} is being edited twice.")
        return travel_opt(keys[1:], opt[key], reference[key], value)


def cli_arguments_to_opt(cli_args, opt: dict) -> dict:
    """ Merge options from arguments with existing options."""
    args = sorted(list(vars(cli_args).items()), key=lambda x: len(x[0]))
    reference = copy.deepcopy(opt)
    for k, v in args:
        if v is None:
            continue

        try:
            v = literal_eval(v)
        except ValueError:
            pass

        k = k.split(".")
        # Boolean arguments have two arguments, the negative starts with 'no-'.
        if len(k[-1]) > 3 and k[-1][:3] == "no-":
            try:
                travel_opt(k, opt, reference, value=v)
            except IndexError:
                k[-1] = k[-1][3:]
                travel_opt(k, opt, reference, value=v)

        else:
            travel_opt(k, opt, reference, value=v)

    return opt


def toml_to_opt(toml_path: Path, opt: Opt, strings_to_paths: bool) -> dict:
    with open(toml_path, 'rb') as toml_file:
        toml_options = tomllib.load(toml_file)
    base_path = Path(toml_path).parent if strings_to_paths else None
    out = merge_opts(opt, toml_options, base_path)
    assert type(out) is dict
    return out
