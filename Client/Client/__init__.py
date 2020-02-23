import json
from pathlib import Path


PROJECT_DIR = Path(__file__).parent.parent


def load(filename: str) -> dict:
    with PROJECT_DIR.joinpath(filename).open() as f:
        return json.load(f)


settings = load("settings.json")
commands = settings["commands"]
connection_details = (settings["ip"], settings["port"])


class Communication:
    disconnected = b""
    commands_success = 0
    command_not_found = 1
    disconnect = 2
    commands = tuple(commands.keys())
