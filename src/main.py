import sys
import logging
import requests
import json
from typing import NamedTuple

APP_NAME = "Python, Git & TGGL Tracker Utility"

class TgglAuth(NamedTuple):
    user: str
    pw: str
    key: str

def grab_tggl_tracker(auth: TgglAuth):
    
    response = requests.get()

def main():
    """
    >>> 0a. Configuration -> API, Working Directory
        0b. Check if the current directory is a git repo.
    >>> 1. This needs to pull the current tracker.
    >>> 2. Create config/docfiles such as requirements, poetry
    """

if __name__ == "__main__":

    FMT = "%(asctime)s | %(module)s@%(funcName)s:%(lineno)d | %(levelname)s -> "
    FMT += "%(message)s"
    logging.basicConfig(format=FMT, level=logging.INFO)

    logging.info(APP_NAME.upper())

    from config import secure_files as SF

    tauth = TgglAuth(*SF.tggl_api)



