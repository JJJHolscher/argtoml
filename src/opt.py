#! /usr/bin/env python3
# vim:fenc=utf-8

from argparse import ArgumentParser
from ast import literal_eval
import copy
import hashlib
from pathlib import Path
import tomllib
import tomli_w
from typing import Optional, Union, get_args

Opt = Union[dict, list]


def iter_opt(opt: Opt):
    if isinstance(opt, list):
        for i, v in enumerate(opt):
            yield i, v
    elif isinstance(opt, dict):
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
        return prefix / ".."

    elif len(string) > 0 and string[0] == "/":
        return Path(string)

    elif len(string) > 1 and string[0:2] == "~/":
        return Path.home() / string[2:]

    elif len(string) > 1 and string[0:2] == "./":
        return prefix / string[2:]

    elif len(string) > 2 and string[0:3] == "../":
        # Remove the top directory of the prefix as long as the start of the string
        # points to a parent directory.
        while len(string) > 2 and string[0:3] == "../" and prefix.parent != prefix:
            prefix = prefix.parent
            string = string[3:]
        return prefix / string

    return string


def merge_opts(old: dict, add: dict, path: Optional[Path]):
    new = copy.deepcopy(old)

    for k, v in iter_opt(add):
        if type(v) is str and path is not None:
            v = string_to_path(v, path)

        # Assert that keys retain their type after updating.
        if (
            k in old 
            and type(old[k]) is not type(v) 
            and not (isinstance(old[k], str) and isinstance(v, Path)) # Strings may become paths however.
        ):
            raise TypeError(
                f"{k} is originally '{old[k]}' of type {type(old[k])},"
                + f"but is to become '{v}' of type {type(v)}."
            )

        if isinstance(v, dict):
            new[k] = merge_opts(old[k] if k in old else {}, v, path)  #type:ignore
        elif isinstance(v, list):
            # lists aren't merged but entirely overwritten
            new[k] = add_list(v, path)  #type:ignore
        else:
            new[k] = v

    return new


def add_list(add: list, path: Optional[Path]):
    return [merge_opts({}, v, path) if isinstance(v, dict) else v for v in add]


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


def travel_opt(key: list, new: Opt, unedited: Opt, value):
    """ Recursively apply all keys to the opt and then return or set the value.

    Args:
        key: A list of the cli argument splitted over the dot (.).
        new: Options to which the value will be added.
        old: Identical to new, except whenever a value is added in new, that key
            is deleted in old. This is to track double edits.
        value: The value to be placed in new at key.

    Raises:
        IndexError: The reference variable missed an object that was about to
            be indexed into. This likely means that some value of the opt was
            about to be accessed or edited after it already was edited.
    """
    k0 = key[0]
    if len(key) > 1:
        # If a key is not in $unedited but is in $new, 
        # then the value of that key was already edited in $new.
        if k0 not in unedited and k0 in new:
            raise KeyError(f"{key} is being edited twice.")
        return travel_opt(key[1:], new[k0], unedited[k0], value)

    if isinstance(unedited[k0], Path) and isinstance(value, str):
        value = string_to_path(value, Path('.'))
    elif type(unedited[k0]) is not type(value):
        unedited_value = unedited[k0]
        raise TypeError(
            f"{key} is originally '{unedited_value}' of type {type(unedited_value)},"
            + f" but is to become '{value}' of type {type(value)}."
        )
    
    # We want to forbid the user from adding cli arguments like:
    # --a "{b: 0}" --a.b 1
    # Because here, the same key "a.b" is edited twice.
    # To avoid this, we delete keys from $unedited that are changed in new.
    del unedited[k0]
    new[k0] = value


def cli_arguments_to_opt(cli_args, opt: dict) -> dict:
    """ Merge options from arguments with existing options."""
    # Filter for cli-arguments that got a user-supplied value.
    args = filter(
        lambda kv: kv[-1] is not None,
        vars(cli_args).items()
    )
    unedited = copy.deepcopy(opt)

    for key, value in args:
        try:
            value = literal_eval(value)
        except ValueError:
            pass

        # The dot is used for indexing.
        # --h.a 0 from the cli would in python be h["a"] = 0
        key = key.split(".")
        try:
            travel_opt(key, opt, unedited, value)

        except IndexError as e:
            # Boolean arguments have two arguments, the negative starts with 'no-'.
            if len(key[-1]) <= 3 or key[-1][:3] != "no-":
                raise e

            # If travel_opt did not find the negative, we can re-search for the positive.
            key[-1] = key[-1][3:]
            travel_opt(key, opt, unedited, value)

    return opt


def toml_to_opt(toml_path: Path, opt: dict, strings_to_paths: bool) -> dict:
    with open(toml_path, 'rb') as toml_file:
        toml_options = tomllib.load(toml_file)
    base_path = Path(toml_path).parent if strings_to_paths else None
    out = merge_opts(opt, toml_options, base_path)
    assert type(out) is dict
    return out


class TomlConfig(dict):

    def __init__(self, opt):
        for k, v in opt.items():
            if isinstance(v, dict):
                opt[k] = TomlConfig(v)
            elif isinstance(v, list):
                opt[k] = TomlConfig.list_init(v)

        super().__init__(opt)
        self.__dict__ = opt

    def __str__(self):
        return self.dumps()

    def dumps(self, prefix: Union[Path, str] = "./", reverse_prefix=True):
        if reverse_prefix:
            prefix = self.reverse_path(prefix)
        opt = self.dict_paths_to_string(vars(self), str(prefix))
        return tomli_w.dumps(opt)

    def dump(self, file: Union[Path, str]):
        prefix = self.reverse_path(file)
        opt = self.dict_paths_to_string(vars(self), prefix)
        with open(file, "wb") as f:
            return tomli_w.dump(opt, f)

    def hash(self, length=8, prefix: Union[Path, str] = "./", reverse_prefix=True):
        string = self.dumps(prefix, reverse_prefix)
        hash = hashlib.sha256(
            string.encode('utf-8'),
            usedforsecurity=False
        ).hexdigest()
        return hash[:length]


    @staticmethod
    def list_init(opt):
        for k, v in enumerate(opt):
            if isinstance(v, dict):
                opt[k] = TomlConfig(v)
            elif isinstance(v, list):
                opt[k] = TomlConfig.list_init(v)
        return opt

    @staticmethod
    def dict_paths_to_string(opt: dict, prefix: str):
        new = {}
        for k, v in opt.items():
            if isinstance(v, dict):
                new[k] = TomlConfig.dict_paths_to_string(v, prefix)
            elif isinstance(v, list):
                new[k] = TomlConfig.list_paths_to_string(v, prefix)
            elif isinstance(v, Path):
                new[k] = TomlConfig.path_to_string(prefix, v)
            else:
                new[k] = v
        return new
            
    @staticmethod
    def list_paths_to_string(opt: list, prefix: str):
        new = []
        for v in opt:
            if isinstance(v, dict):
                new.append(TomlConfig.dict_paths_to_string(v, prefix))
            elif isinstance(v, list):
                new.append(TomlConfig.list_paths_to_string(v, prefix))
            elif isinstance(v, Path):
                new.append(TomlConfig.path_to_string(prefix, v))
            else:
                new.append(v)
        return new


    @staticmethod
    def path_to_string(prefix: str, path: Path) -> str:
        if path.is_absolute():
            return str(path)

                    # avoid any "./../thing.toml"
        path_parts = str(path).split("/")
        prefix_parts = prefix.split("/")
        if prefix_parts[-1] == "":
            prefix_parts = prefix_parts[:-1]

        # If the path starts with ".." and the prefix does not end in "..",
        # then we can simplify by removing the ".." from the path with the
        # top directory of the prefix.
        while path_parts and prefix_parts and path_parts[0] == "..":
            while prefix_parts and prefix_parts[-1] == ".":
                del prefix_parts[-1]

            if not prefix_parts:
                break

            if prefix_parts[-1] == "..":
                break

            del prefix_parts[-1]
            del path_parts[0]

        path_str = "/".join(path_parts)

        if not prefix_parts:
            if not path_parts:
                return "./"
            if path_parts[0] == "..":
                return path_str
            prefix_parts = ["."]

        return "/".join(prefix_parts) + "/" + path_str



    @staticmethod
    def reverse_path(path) -> str:
        if str(path)[0] == "/":
            return str(Path(path).parent)
        elif str(path)[:1] == "~/":
            return "~/" + str(Path(path).parent)

        # cut the filename
        parts = str(path).split("/")[:-1]
        if len(parts) == 0 or (len(parts) == 1 and parts[0] == "."):
            return "."

        # Walk the path and record the reverse operation every step.
        cwd = Path.cwd()
        prefix = []
        for part in parts:
            if part == "..":
                if cwd == Path("/"):
                    continue
                prefix.append(cwd.name)
                cwd = cwd.parent
            elif part == ".":
                continue
            else:
                if len(prefix) == 0 or prefix[-1] == "..":
                    prefix.append("..")
                else:
                    del prefix[-1]
                cwd /= part

        out = "/".join(prefix)
        if prefix[0] != "..":
            out = "./" + out
        return out




