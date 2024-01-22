#! /usr/bin/env python3
# vim:fenc=utf-8

"""
Functions for finding toml configuration files in default locations.
"""

import os
from importlib.resources import as_file, files
from importlib.resources.abc import Traversable
from pathlib import Path
from typing import Optional, Tuple, Union

import __main__

TPath = Union[Traversable, Path]
StrPath = Union[str, Path]
try:
    get_ipython()
    IPYTHON = True
except NameError:
    IPYTHON = False


def locate_toml_path(
    toml_path: StrPath = Path("config.toml"),
    toml_dir: Optional[Union[StrPath, Traversable]] = None,
    parent: Optional[bool] = None
) -> TPath:
    """ Return the absolute path to the location where a toml file should be.

    This function does not test whether the returned path actually contains a
    toml file.

    There are various scenario's, the most predictable behavior arises when
    you supply a toml_dir xor an absolute toml_path.
    Else, the system will look for the toml file in order of:
    1. the package directory
    2. the directory of the main file
    3. the directory of the ipynb file

    Args:
        toml_path: a relative or absolute path to the toml file.
        toml_dir: an absolute path in which to look for the toml file.
        parent: whether to look for the toml file in the parent directory of
            the directory containing the toml file.

    Returns:
        The path to the toml file.

    Errors:
        NotImplementedError: The context in which this function was called does
            not lend itself for the automatic location of toml files. Supply
            an absolute toml_path or toml_dir instead.
    """
    toml_path = Path(toml_path)
    parent = parent if parent is not None else not IPYTHON

    # Return toml_dir / toml_path if possible.
    if toml_dir is not None:
        if toml_dir is Traversable:
            if parent:
                toml_dir = toml_dir.joinpath(Path(".."))
            return toml_dir.joinpath(toml_path)
        else:
            return Path(toml_dir) / toml_path

    # Return the toml_path if it is absolute.
    elif toml_path.is_absolute():
        return Path(toml_path)

    # Have toml_dir be the package dir if argtoml is called from a package.
    if __main__.__package__:
        toml_dir = files(__main__.__package__)
        if parent:
            toml_dir = toml_dir.joinpath(Path(".."))
        return toml_dir.joinpath(toml_path)

    # Use the folder of the main file as toml_dir.
    elif "__file__" in dir(__main__):
        toml_dir = Path(__main__.__file__).parent
        if parent:
            toml_dir = toml_dir.parent
        return toml_dir / toml_path

    # Find the path of the ipython notebook.
    elif IPYTHON:
        try:
            import ipynbname

            toml_dir = Path(ipynbname.path().parent)
            if parent:
                toml_dir = toml_dir.parent
            return toml_dir / toml_path

        except IndexError:
            toml_dir = Path(os.path.abspath("."))
            return toml_dir / toml_path

    raise NotImplementedError
