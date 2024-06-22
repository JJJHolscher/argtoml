#! /usr/bin/env python3
# vim:fenc=utf-8

from argparse import ArgumentParser
from pathlib import Path
from typing import Optional, Union, List

from .opt import toml_to_opt, opt_to_argument_parser, cli_arguments_to_opt, merge_opts, TomlConfig


StrPath = Union[Path, str]


def parse_args(
    toml_path: Union[List[StrPath], StrPath] = [Path("config.toml")],
    parser: Optional[ArgumentParser] = None,
    description: str = "",
    strings_to_paths: bool = True,
    overwrite: dict = {}
) -> dict:
    """
    Add the content of a toml file as argument with default values
    to an ArgumentParser object.
    You can specify additional toml files with the -c cli argument.
    You can overwrite any values by providing an overwrite argument.

    This function does not look for cli arguments in an ipython context.

    Args:
        toml_path: a relative or absolute path to the toml file.
        parser: ArgumentParser object that can be pre-filled.
        description: a cli description for if the ArgumentParser is not given.
        toml_dir: the absolute path to the parent directory of the toml file.
        strings_to_paths: whether to convert path-like strings to 
            pathlib.Path objects.
        grandparent: use grandparent directory of the file calling argtoml
            instead of parent directory. Defaults to True if argtoml is not
            called from ipython.
        overwrite: values with the highest presedence.
    Out:
        A (nested) SimpleNamespace object filled with cli argument values that
        defaults to values from the toml file.
    """
    toml_path = toml_path if isinstance(toml_path, list) else [toml_path]
    locations = [Path(path) for path in toml_path]

    # Merge all the toml files into a single dictionary.
    options: dict = {}
    for location in locations:
        options = toml_to_opt(location, options, strings_to_paths)

    # Jupyter Lab crashes if argparse looks for command line arguments.
    try:
        get_ipython()  #type:ignore
        options = merge_opts(options, overwrite, None)  #type:ignore
        return TomlConfig(options)
    except NameError:
        pass

    # Translate that dictionary into command line arguments.
    if parser is None:
        parser = ArgumentParser(description=description)
    parser.add_argument("-c", required=False, help="path to an optional extra \
                        toml file for loading configuration from.")
    parser = opt_to_argument_parser(options, parser)
    args = parser.parse_args()

    # Merge any cli-supplied toml file.
    if args.c:
        options = toml_to_opt(Path(args.c), options, strings_to_paths)
        args.c = None

    # Merge the cli-supplied values.
    options = cli_arguments_to_opt(args, options)

    # Apply any options provided during the function call.
    options = merge_opts(options, overwrite, None)  #type:ignore

    return TomlConfig(options)


if __name__ == "__main__":
    print(parse_args())
