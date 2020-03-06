import json
from pathlib import Path


PROJECT_DIR = Path(__file__).parent.parent


def load(filename: str) -> dict:
    with PROJECT_DIR.joinpath(filename).open() as f:
        return json.load(f)


settings = load("settings.json")
commands = settings["commands"]
binding_details = (settings["ip"], settings["port"])


class Communication:
    disconnected = b""
    commands_success = b"0"
    command_not_found = b"1"
    disconnect = b"2"
    provide_mac = b"3"
    commands = tuple(commands.keys())
