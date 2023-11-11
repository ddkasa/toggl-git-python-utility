import sys
import os
from typing import Optional
from pathlib import Path
import logging
import requests
from base64 import b64encode, b64decode
from typing import NamedTuple
import subprocess

import config_func as CF

APP_NAME = "Python, Git & TGGL Tracker Utility"


class TgglAuth(NamedTuple):
    user: str
    pw: str
    key: str


class TgglTracker(NamedTuple):
    entry_id: int
    workspace_id: int
    description: str


class TrackerError(Exception):
    """Exception related to anything todo with Toggl data."""


class NotTrackingerror(TrackerError):
    """Exception if a user is not tracking on Toggl."""


class TgglApi:
    """Setup for dealing with the Toggl API."""

    def __init__(self, auth_token: TgglAuth):
        self.email = auth_token.user

        password = b64decode(auth_token.pw).decode("utf-8")

        auth_txt = f"{self.email}:{password}"
        decode = b64encode(bytes(auth_txt, "utf-8")).decode("ascii")
        self.auth_encode = "Basic %s" % decode

        self.base_url = r'https://api.track.toggl.com/api/v9'
        self.headers = {
            'content-type': 'application/json',
            'Authorization': self.auth_encode
        }

    def grab_tggl_time_entry(self, project_id: int = 0) -> TgglTracker:
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

        tracker_project_id = content.get("project_id", 0)
        if project_id != 0 and project_id != tracker_project_id:
            raise TrackerError("Wrong project id: ", tracker_project_id)

        tracker = TgglTracker(content["id"], content["workspace_id"],
                              content["description"])

        return tracker

    def stop_tggl_time_entry(self, workspace_id: int,
                             time_entry_id: int) -> bool:
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


class GitManagement:
    """Class for dealing with git commands and manipulation."""

    def __init__(self, path: Path = Path(".")):
        self.path = path if path is not None else Path(".")
        if path is not None and path != Path("."):
            os.chdir(path)

    def add_files(self):
        """Adds all files to version control."""
        logging.info("Adding files to version control.")
        command = "git add ."
        subprocess.run(command)

    def create_commit(self, message: str):
        """Creates a commit with the message specified."""
        message = message.upper()
        logging.info(f"Creating a git commit with message: {message}.")
        print("-".center)
        command = f'git commit -a -m "{message}"'
        subprocess.run(command)

    def push_to_remote_repo(self, branch: str = "main"):
        """Pushes current repo to the specificed branch."""
        print("-".center(60, "-"))
        command = f"git push origin {branch}"
        subprocess.run(command)

    def check_git_repo(self) -> bool:
        """Checks the current folder for a git repository."""
        is_git_repo = "git rev-parse --is-inside-work-tree"
        command = subprocess.run(is_git_repo, capture_output=True, text=True)
        response = command.stdout
        return "true" in response


class CodeManagement:
    """
    >>> Deals with managing automatic linting, environment, tests
        and dependency management.
    """

    def __init__(self, config: CF.ConfigManager):
        self.config = config["Python"]


def main():
    """
    >>> 0a. Configuration -> API, Working Directory
        0b. Check if the current directory is a git repo.
    >>> 1. This needs to pull the current tracker.
    >>> 2. Create config/docfiles such as requis/ Cancel Tracker
        2a. Check directory for env type and if it contains a req file or
            poetry file / conda env
        2b. Create automatic req files with that info.
        3a. Run Tests
    >>> 3. Use TGGL Tracker to create commit information and commit + push
        3b. Possibly add files to repo here in the future.
    >>> 4. End the TGGL Tracker
    """
    config = CF.ConfigManager()

    repo_path = Path(config["Main"]["target_directory"])
    if not repo_path.exists():
        logging.critical("Specfied repo folder does not exist.")
        sys.exit()

    git_obj = GitManagement(repo_path)

    if not git_obj.check_git_repo():
        logging.critical("Specified folder is not a GIT repo.")
        sys.exit()

    tggl_data = config["Toggl"]

    auth = TgglAuth(tggl_data["username"], tggl_data["password"],
                    tggl_data["api_key"])

    tggl_api = TgglApi(auth)

    try:
        project_id = int(config["Toggl"]["project"])
        entry = tggl_api.grab_tggl_time_entry(project_id)
    except ConnectionError:
        logging.critical("Failed to grab the current tggl entry.")
        sys.exit()
    except NotTrackingerror:
        logging.critical("User is not tracking a time entry atm.")
        sys.exit()

    if config["Git"]["add"] == "1":
        git_obj.add_files()

    if config["Git"]["commit"] == "1":
        git_obj.create_commit(entry.description)

    if config["Git"]["push"] == "1":
        git_obj.push_to_remote_repo()

    if config["Toggl"]["cancel"] == "1":
        tggl_api.stop_tggl_time_entry(entry.workspace_id, entry.entry_id)


if __name__ == "__main__":
    FMT = "%(asctime)s | %(module)s@%(funcName)s:%(lineno)d | %(levelname)s ->"
    FMT += " %(message)s"
    logging.basicConfig(format=FMT, level=logging.INFO)

    logging.info(APP_NAME.upper())

    main()
