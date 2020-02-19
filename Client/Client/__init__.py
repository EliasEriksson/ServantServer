import json
from pathlib import Path


PROJECT_DIR = Path(__file__).parent.parent


def load(filename: str) -> dict:
    with PROJECT_DIR.joinpath(filename).open() as f:
        return json.load(f)


class DisconnectedFromServer(Exception):
    pass




commands = load("commands.json")
