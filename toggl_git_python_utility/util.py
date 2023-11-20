from pathlib import Path

from typing import Any, ForwardRef
import json

from collections import ChainMap

import subprocess
import shutil


def run_sub_command(cmd: str) -> str:
    width, _ = shutil.get_terminal_size(fallback=(80, 24))
    print("Subprocess".center(width, "+"))
    print(cmd)
    run = subprocess.run(cmd, capture_output=True, text=True)
    print("+".center(width, "+"))
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
        if '__annotations__' in c.__dict__:
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


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Path):
            return str(obj)
        return super().default(obj)


if __name__ == "__main__":
    pass