#! /usr/bin/env python3
# vim:fenc=utf-8

from argparse import ArgumentParser
from pathlib import Path
import tomllib
from typing import Optional, Union, List

from .locate import TPath, locate_toml_path
from .opt import toml_to_opt, opt_to_argument_parser, cli_arguments_to_opt


def parse_args(
    toml_path: List[Path] = [Path("config.toml")],
    parser: Optional[ArgumentParser] = None,
    description: str = "",
    toml_dir: Optional[TPath] = None,
    strings_to_paths: bool = True,
    grandparent: Optional[bool] = None,
) -> dict:
    """ THIS DOCSTRING IS OUTDATED.
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
    # Create toml paths depending on the context in which this is called.
    locations = []
    for path in toml_path:
        location = locate_toml_path(
            path, toml_dir, grandparent
        )
        locations.append(location)

    # Merge all the toml files into a single dictionary.
    options = {}
    for location in locations:
        options = toml_to_opt(location, options, strings_to_paths)

    # Translate that dictionary into command line arguments.
    if parser is None:
        parser = ArgumentParser()
    parser.add_argument("-c", required=False, help="path to an optional extra \
                        toml file for loading configuration from.")
    parser = opt_to_argument_parser(options, parser)

    # Merge the user-supplied command line arguments with the toml options.
    args = parser.parse_args()
    if args.c:
        options = toml_to_opt(Path(args.c), options, strings_to_paths)
        args.c = None
    options = cli_arguments_to_opt(args, options)

    return options


if __name__ == "__main__":
    print(parse_args())
