#! /usr/bin/env python3
# vim:fenc=utf-8

from argparse import ArgumentParser
from pathlib import Path
import tomllib
from typing import Optional, Union, List

from .locate import TPath, locate_toml_path
from .opt import merge_opts, opt_to_argument_parser, cli_arguments_to_opt


def parse_args(
    toml_path: Union[Path, List[Path]] = Path("config.toml"),
    parser: Optional[ArgumentParser] = None,
    description: str = "",
    toml_dir: Optional[TPath] = None,
    base_path: Optional[Union[TPath, bool]] = True,
    grandparent: Optional[bool] = None,
) -> dict:
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
    if type(toml_path) is not list:
        toml_path = [toml_path]

    # Create toml paths depending on the context in which this is called.
    locations = []
    for path in toml_path:
        location, possible_base_path = locate_toml_path(
            path, toml_dir, grandparent
        )
        locations.append(location)

        if base_path is True:
            base_path = possible_base_path
    base_path = base_path if base_path else None

    # Merge all the toml files into a single dictionary.
    options = {}
    for location in locations:
        with open(location, 'rb') as toml_file:
            toml_options = tomllib.load(toml_file)
        options = merge_opts(options, toml_options, base_path)
    # Translate that dictionary into command line arguments.
    if parser is None:
        parser = ArgumentParser()
    parser = opt_to_argument_parser(options, parser)

    # Merge the user-supplied command line arguments with the toml options.
    args = parser.parse_args()
    options = cli_arguments_to_opt(args, options)
    return options


if __name__ == "__main__":
    print(parse_args())
