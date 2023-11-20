import sys
import os
from typing import (
    Final, Literal, Optional, get_args, Any, get_origin, Union, NamedTuple
    )
import logging
import base64
import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
import configparser

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
    linting: Optional[Literal["Flake8", "Mypy", "Ruff", "Pylint"]] = field(default=None)
    tests: Optional[Literal["Unittest", "Pytest"]] = field(default=None)
    main_code: Path = field(default=Path("src"))


@dataclass
class GitConfig:
    """Holds configuration settings for git code management."""
    add: bool = field(default=False)
    commit: bool = field(default=True)
    push: bool = field(default=False)


class TogglAuth(NamedTuple):
    username: str
    password: str
    api_key: str


@dataclass
class TogglConfig:
    user_data: TogglAuth
    project: Optional[int] = field(default=None)
    cancel: bool = field(default=False)


@dataclass
class DefaultConfig:
    target_directory: Path = field()
    python: PythonConfig
    git: GitConfig
    toggl: TogglConfig

    def __post_init__(self):
        self.target_directory = Path(self.target_directory)


class ConfigManager:
    """Class for managing basic configuration duties."""

    def __init__(self):
        self.config_folder = Path(r"toggl_git_python_utility\config")

        self.config_file_path = self.config_folder / "configuration.json"

        if self.config_file_path.exists():
            self.load_config()
            return

        logging.warning("No Configuration Detected")
        self.config = self.generate_config(DefaultConfig)

        logging.info("Writing New Configuration To Save Location.")

        conf = asdict(self.config)
        with self.config_file_path.open("w", encoding="utf-8") as configfile:
            configfile.write(json.dumps(conf, cls=util.CustomJSONEncoder))

    def load_config(self):
        logging.info("Loading Configuration")
        with self.config_file_path.open("r", encoding="utf-8") as config:
            data = json.load(config)

        self.config = self.generate_config(DefaultConfig, data)

    def generate_config(self, config_model: type,
                        convert: Optional[dict] = None):
        """Generates a json config or converts an existing one depending if a 
           convert was passed in or not."""

        config_an = util.all_annotations(config_model)

        data = {}
        for k, v in config_an.items():
            item = v
            default = None
            origin = get_origin(item)

            if origin == Union:
                item = get_args(item)[0]

            d = v
            if convert:
                d = self.generate_config(v, convert[k])
            if item == bool:
                d = default
            elif v == Path:
                d = create_path(k)
            elif v in {TogglConfig, TogglAuth, PythonConfig, GitConfig}:
                d = self.generate_config(v)
            elif k in {"password", "api_key"}:
                d = select_password(k)
            elif k == "username":
                d = select_username()
            elif get_origin(item) == Literal:
                d = select_option(k, item, default)
            elif v == int:
                d = select_int(k)

            data[k] = d

        return config_model(**data)


def create_path(key: str, default=Path(".")) -> str:
    key = key.replace("_", " ").title()
    while True:
        print(f"Please specify a valid target {key} path.")

        path = input("> ")

        if Path(path).exists():
            return path

        print("Invalid Path Specified")


def select_option(key: str, values: Literal, default: Optional[Any] = None
                  ) -> Any:

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
    patt = r"([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+"

    regex = re.compile(patt)

    print("Input a username(email) for your Toggl account.")

    while True:
        email = input("> ")

        if re.fullmatch(regex, email):
            return email
        print("Wrong Email Format! Try Again.")


def select_password(key: str) -> str:
    key = key.replace("_", " ").title()
    print(f"Type in your {key} for your Toggle Account")
    pw = maskpass.askpass(prompt=f"Enter {key}: ", mask="*")

    return base64.b64encode(pw.encode("utf-8")).decode("utf-8")


def select_int(key: str) -> int:
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

    an = util.all_annotations(DefaultConfig)

    print(an)