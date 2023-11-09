# import sys
import logging
import requests
from base64 import b64encode
from typing import NamedTuple

import subprocess

APP_NAME = "Python, Git & TGGL Tracker Utility"


class TgglAuth(NamedTuple):
    user: str
    pw: str
    key: str


class TgglTracker(NamedTuple):
    entry_id: int
    workspace_id: int
    description: str


class NotTrackingerror(Exception):
    """Exception if a user is not tracking on Toggl."""

    def __str__(self) -> str:
        return self.__class__.__name__


class TgglApi:

    def __init__(self, auth_token: TgglAuth):
        self.email = auth_token.user
        password = auth_token.pw
        auth_txt = f"{self.email}:{password}"
        decode = b64encode(bytes(auth_txt, "utf-8")).decode("ascii")
        self.auth_encode = "Basic %s" % decode

        self.base_url = r'https://api.track.toggl.com/api/v9'
        self.headers = {'content-type': 'application/json',
                        'Authorization': self.auth_encode}

    def grab_tggl_time_entry(self) -> TgglTracker:
        """Grabs the specified users current tggl entry"""
        logging.info(f"Grabbing current tggl time entry for user {self.email}")
        response = requests.get(self.base_url + "/me/time_entries/current",
                                headers=self.headers)
        code = response.status_code
        if code != 200:
            logging.error("Failed to connect to tggl api.")
            logging.error(f"Response Code {code}")
            raise ConnectionError(code)

        content = response.json()
        if not isinstance(content, dict):
            raise NotTrackingerror("Specified user is not tracking atm.")

        tracker = TgglTracker(content["id"],
                              content["workspace_id"],
                              content["description"])

        return tracker

    def stop_tggl_time_entry(self, workspace_id: int, time_entry_id: int
                             ) -> bool:
        """Stops the specified time tracker."""
        logging.info(f"Stopping time tracker with id {time_entry_id}")
        url = self.base_url
        url += f'/workspaces/{workspace_id}/time_entries/{time_entry_id}/stop'
        response = requests.patch(url, headers=self.headers)

        code = response.status_code
        if code != 200:
            logging.error("Failed to stop time entry.")
            logging.error(f"Response: {code}")

            return False

        return True


def check_git_repo() -> bool:
    """Checks the current folder for a git repository."""
    is_git_repo = "git rev-parse --is-inside-work-tree"
    command = subprocess.run(is_git_repo, capture_output=True, text=True)
    response = command.stdout
    return "true" in response


def main(auth: TgglAuth):
    """
    >>> 0a. Configuration -> API, Working Directory
        0b. Check if the current directory is a git repo.
    >>> 1. This needs to pull the current tracker.
    >>> 2. Create config/docfiles such as requirements, poetry
    >>> 3. Pull Tracker Message / Add to Commit / Cancel Tracker
    """

    if not check_git_repo():
        return

    tggl_api = TgglApi(auth)

    try:
        entry = tggl_api.grab_tggl_time_entry()
    except ConnectionError:
        logging.critical("Failed to grab the current tggl entry.")
        return
    except NotTrackingerror:
        logging.critical("User is not tracking a time entry atm.")
        return

    tggl_api.stop_tggl_time_entry(entry.workspace_id, entry.entry_id)


if __name__ == "__main__":
    # from pprint import pprint
    from config import secure_files as SF

    FMT = "%(asctime)s | %(module)s@%(funcName)s:%(lineno)d | %(levelname)s ->"
    FMT += " %(message)s"
    logging.basicConfig(format=FMT, level=logging.INFO)

    logging.info(APP_NAME.upper())

    tauth = TgglAuth(*SF.tggl_api)

    main(tauth)
