#! /usr/bin/env python3

import tomllib
from setuptools import Command, setup
from pathlib import Path

import __main__
import tomli_w


class BumpVersion(Command):
    description = "A custom command for my project"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        with open("pyproject.toml", "rb") as f:
            pp = tomllib.load(f)

        major, minor, patch = [int(i) for i in pp["version"].split(".")]
        pp["version"] = f"{major}.{minor}.{patch + 1}"

        with open("pyproject.toml", "wb") as f:
            tomli_w.dump(pp, f)


def init_pyproject(pp):
    name = Path(__main__.__file__).parent.name
    pp["name"] = name
    pp["version"] = "0.0.0"
    pp["url"] = f"https://github.com/{pp['authors'][0]['github']}/{name}"
    return pp


def read_email(path=""):
    if path == "":
        path = Path.home() / ".secret/email.txt"
    with open(path) as f:
        return f.read().strip()


def read_description(path="README.md"):
    try:
        with open(path) as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""


if __name__ == "__main__":
    with open("pyproject.toml", "rb") as f:
        pp = tomllib.load(f)

    if pp["name"] == "":
        with open("pyproject.toml", "wb") as f:
            pp = init_pyproject(pp)
            tomli_w.dump(pp, f)

    setup(
        name=pp["name"],
        version=pp["version"],
        author=pp["authors"][0]["name"],
        author_email=read_email(),
        url=pp["url"],
        description=pp["abstract"],
        long_description=read_description(),
        long_description_content_type="text/markdown",
        license=pp["license"],
        packages=[pp["name"]],
        cmdclass={"bump": BumpVersion},
        # install_requires=[],
    )
