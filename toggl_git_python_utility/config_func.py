import sys
import os
from typing import (
    Literal,
    Optional,
    get_args,
    Any,
    get_origin,
    Union,
)
import logging
# from pprint import pformat, pprint

import base64
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path

import json


import maskpass

if __name__ == "__main__":
    root_path = Path(__file__).parent.resolve().parents[0]
    sys.path.append(os.path.abspath(root_path))

from toggl_git_python_utility import util


@dataclass
class PythonConfig:
    """Holds configuration for python code management."""

    package_manager: Literal["PIP", "Conda", "Poetry"] = field(default="PIP")
    environment: Literal["Conda", "Venv"] = field(default="Venv")
    type_checking: Optional[Literal["Mypy"]] = field(default=None)
    security_checking: Optional[Literal["Bandit"]] = field(default=None)
    linting: Optional[Literal["Flake8", "Ruff", "Pylint"]]\
        = field(default=None)
    tests: Optional[Literal["Unittest", "Pytest"]] = field(default=None)
    main_code: Path = field(default=Path("src"))
    format_code: bool = field(default=True)

    def __post_init__(self):
        self.main_code = Path(self.main_code)


@dataclass
class GitConfig:
    """Holds configuration settings for git code management."""

    add: bool = field(default=False)
    commit: bool = field(default=True)
    push: bool = field(default=False)


@dataclass
class TogglAuth:
    """Authentication information for Toggl Tracker."""

    username: str
    password: str
    api_key: Optional[str] = field(default=None)


@dataclass
class TogglConfig:
    """Configuration information for Toggl management."""

    user_data: TogglAuth
    project: Optional[int] = field(default=None)
    cancel: bool = field(default=False)


@dataclass
class ConfigModel:
    """Base Config items including the original target_directory."""

    target_directory: Path = field()
    python: PythonConfig
    git: GitConfig
    toggl: TogglConfig

    def __post_init__(self):
        self.target_directory = Path(self.target_directory)


class ConfigManager:
    """Class for managing basic configuration duties."""

    def __init__(self, new=False):
        self.config_folder = Path(r"toggl_git_python_utility\config")
        self.config_file_path = self.config_folder / "configuration.json"

        if self.config_file_path.exists() and not new:
            self.load_config()
            return

        logging.warning("No Configuration Detected")
        self.new_config()

        self.config: ConfigModel

    def load_config(self):
        """Loads the existing configuration. If one doesn't exist or is
        corrupted. It starts creating a new one."""
        logging.info("Loading Configuration")
        try:
            with self.config_file_path.open("r", encoding="utf-8") as config:
                data = json.load(config)
                self.config = self.generate_config(ConfigModel, data)
        except json.JSONDecodeError:
            self.new_config()

    def new_config(self):
        """Creates a new config with user input and defaults."""
        self.config = self.generate_config(ConfigModel)

        logging.info("Writing New Configuration To Save Location.")

        conf = asdict(self.config)
        with self.config_file_path.open("w", encoding="utf-8") as configfile:
            configfile.write(json.dumps(conf, cls=util.CustomJSONEncoder))

    def generate_config(
        self, config_model: type, convert: Optional[dict] = None
    ) -> Any:
        """Generates a json config or converts an existing one depending if a
        convert was passed in or not."""

        config_an = util.all_annotations(config_model)
        defaults = util.collect_defaults(config_model)

        if config_model not in {
            TogglConfig,
            TogglAuth,
            PythonConfig,
            GitConfig,
            ConfigModel,
            dict,
        }:
            if get_origin(config_model) == Union:
                config_model = get_args(config_model)[0]
            if get_origin(config_model) == Literal:
                config_model = str

            return config_model(convert)

        data = {}
        for k, v in config_an.items():
            item = v
            default = defaults[k]
            origin = get_origin(item)

            if origin == Union:
                item = get_args(item)[0]

            d = v
            if convert:
                d = self.generate_config(v, convert.get(k))
            elif item == bool:
                d = default
            elif item == Path:
                d = create_path(k)
            elif item in {TogglConfig, TogglAuth, PythonConfig, GitConfig}:
                d = self.generate_config(v)
            elif k in {"password", "api_key"}:
                d = select_password(k)
            elif k == "username":
                d = select_username()
            elif get_origin(item) == Literal:
                d = select_option(k, item, default)
            elif item == int:
                d = select_int(k)

            data[k] = d

        return config_model(**data)


def create_path(key: str, default=Path(".")) -> str:
    util.create_seperator()

    key = key.replace("_", " ").title()
    while True:
        print(f"Please specify a valid target {key} path.")

        path = input("> ")

        if Path(path).exists():
            return path

        print("Invalid Path Specified")


def select_option(key: str, values: Literal, default: Optional[Any] = None) -> Any:
    util.create_seperator()

    items = get_args(values)
    len_it = len(items)
    print(f"Select the {key} you use.")
    while True:
        for i, item in enumerate(items):
            i += 1
            print(f"{i}: {item} ")

        print(f"{len_it + 1}: DEFAULT[{default}]")

        try:
            selection = int(input("> "))
        except ValueError:
            print(f"Bad input select a number between 1 and {len_it + 1}")
            continue

        if selection in range(1, len_it + 1):
            return items[selection - 1]
        elif selection == len_it + 1:
            return default

        print(f"Bad input select a number between 1 and {len_it + 1}")


def select_username() -> str:
    util.create_seperator()
    patt = r"([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+"

    regex = re.compile(patt)

    print("Input a username(email) for your Toggl account.")

    while True:
        email = input("> ")

        if re.fullmatch(regex, email):
            return email
        print("Wrong Email Format! Try Again.")


def select_password(key: str) -> str:
    util.create_seperator()
    key = key.replace("_", " ").title()
    print(f"Type in your {key} for your Toggle Account")
    pw = maskpass.askpass(prompt=f"Enter {key}: ", mask="*")

    return base64.b64encode(pw.encode("utf-8")).decode("utf-8")


def select_int(key: str) -> int:
    util.create_seperator()
    print(f"What is the {key} you want to use?")

    while True:
        try:
            item = int(input(f"{key} > "))
        except ValueError:
            print(f"Selected {key} needs to be an integer!")
            print("Try Again!")
            continue

        return item


if __name__ == "__main__":
    FMT = "%(asctime)s | %(module)s@%(funcName)s:%(lineno)d | %(levelname)s ->"
    FMT += " %(message)s"
    logging.basicConfig(format=FMT, level=logging.INFO)
    config = ConfigManager()
