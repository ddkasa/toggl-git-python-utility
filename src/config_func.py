from typing import Final, Literal, Optional

import base64

from pathlib import Path

import configparser


class ConfigManager(configparser.ConfigParser):
    CONFIG_DEFAULT: Final[dict] = {
        "target_directory": Path,
        "python": {
            "environment": Literal["PIP", "Conda", "Poetry", "Venv"],
            "type_checking": Optional[Literal["Mypy"]],
            "linting": Optional[Literal["Flake8", "Mypy", "Ruff", "Pylint"]],
            "tests": Optional[Literal["Unittest", "Pytests"]]
        },
        "git": {
            "add": bool,
            "commit": bool,
            "push": bool,
        },
        "toggl": {
            "user_name": str,
            "password": str,
            "api_key": str,
            "project": int
        },

    }

    def __init__(self):
        self.config_folder = Path(r"src\config")

        self.config_file = self.config_folder / "configuration.ini"

    def load_config(self):
        pass

    def generate_config(self):
        pass
