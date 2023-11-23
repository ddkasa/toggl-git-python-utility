from pathlib import Path


from dataclasses import _MISSING_TYPE, is_dataclass
from typing import Any, NamedTuple
import json

from collections import ChainMap, defaultdict

import subprocess
import shutil


def run_sub_command(cmd: str) -> str:
    width, _ = shutil.get_terminal_size(fallback=(80, 24))
    print("Subprocess".center(width, "+"))
    print(cmd)
    run = subprocess.run(cmd, capture_output=True, text=True)
    print(run.stdout)
    create_seperator("+")
    return run.stdout


def all_annotations(cls: Any) -> ChainMap:
    """
    >>> Returns a dictionary-like ChainMap that includes annotations for all
       attributes defined in cls or inherited from superclasses.
    """
    if not isinstance(cls, type):
        cls = cls.__class__
    anno = {}
    for c in reversed(cls.__mro__):
        if "__annotations__" in c.__dict__:
            for key, val in c.__annotations__.items():
                if key in anno:
                    continue
                elif not isinstance(val, type):
                    try:
                        val = eval(val)
                    except TypeError:
                        pass
                anno[key] = val

    return ChainMap(anno)


def collect_defaults(cls: type) -> defaultdict:
    """Collects default values of a Dataclass Class and replaces them with
    None if needed."""
    if not isinstance(cls, type):
        cls = cls.__class__

    defaults: defaultdict[str, Any] = defaultdict(lambda: None)

    if "__dataclass_fields__" not in cls.__dict__:
        return defaults

    fields = cls.__dataclass_fields__  # type: ignore

    for k, v in fields.items():
        default = v.default
        if isinstance(default, _MISSING_TYPE):
            default = None

        defaults[k] = default

    return defaults


def create_seperator(symbol: str = "#"):
    w, _ = shutil.get_terminal_size()
    print(symbol.center(w, symbol))


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Path):
            return str(obj)
        return super().default(obj)


if __name__ == "__main__":
    pass
