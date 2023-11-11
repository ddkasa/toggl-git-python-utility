from typing import Final, Literal, Optional, get_args, Any, get_origin, Union
import logging
import base64
import re
from pathlib import Path
import configparser

import maskpass


class ConfigManager(configparser.ConfigParser):
    """Class for managing basic configuration duties."""
    CONFIG_DEFAULT: Final[dict] = {
        "target_directory": Path,
        "python": {
            "package_manager": (Literal["PIP", "Conda", "Poetry"], "PIP"),
            "environment": (Literal["Conda", "Venv"], "Venv"),
            "type_checking": (Optional[Literal["Mypy"]], None),
            "linting": (Optional[Literal["Flake8", "Mypy", "Ruff", "Pylint"]],
                        None),
            "tests": (Optional[Literal["Unittest", "Pytest"]], None)
        },
        "git": {
            "add": (bool, False),
            "commit": (bool, True),
            "push": (bool, False),
        },
        "toggl": {
            "username": str,
            "password": str,
            "api_key": str,
            "project": (Optional[int], None),
            "cancel": (bool, True)
        },
    }

    def __init__(self, *args, **kwargs):
        super(ConfigManager, self).__init__(*args, **kwargs)
        self.config_folder = Path(r"src\config")

        self.config_file = self.config_folder / "configuration.ini"

        if self.config_file.exists():
            self.load_config()
            return

        logging.warning("No Configuration Detected")
        self.generate_config(self.CONFIG_DEFAULT)

        logging.info("Writing New Configuration To Save Location.")
        with self.config_file.open("w", encoding="utf-8") as configfile:
            self.write(configfile)

    def load_config(self):
        logging.info("Loading Configuration")
        self.read(self.config_file, encoding="utf-8")

    def generate_config(self, value: dict[str, type | dict],
                        key: str = "Main"):
        key = key.capitalize()
        self.add_section(key)

        for k, v in value.items():
            item = v
            default = False
            if isinstance(v, tuple):
                item, default = v
            origin = get_origin(item)

            if origin == Union:
                item = get_args(item)[0]

            if item == bool:
                item = int(default)

            elif item == int:
                item = select_int(k)

            elif k == "username":
                item = select_username()
            elif k in {"password", "api_key"}:
                item = select_password(k)

            elif item == Path:
                item = create_path()
            elif get_origin(item) == Literal:
                item = select_option(k, item, default)  # type: ignore

            elif isinstance(v, dict):
                item = self.generate_config(v, k)
                continue

            self.set(key, option=k, value=str(item))


def create_path(default=Path(".")) -> str:
    while True:
        print("Please specify a valid target project path")

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
