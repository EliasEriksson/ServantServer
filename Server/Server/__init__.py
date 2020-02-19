import json
from pathlib import Path
from wakeonlan import send_magic_packet


DESKTOP_MAC = "9C:5C:8E:BE:D8:FB"
PROJECT_DIR = Path(__file__).parent.parent


def load(filename: str) -> dict:
    with PROJECT_DIR.joinpath(filename).open() as f:
        return json.load(f)


def client_wal():
    send_magic_packet(DESKTOP_MAC)


settings = load("settings.json")
