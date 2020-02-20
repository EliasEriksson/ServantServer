from Server.watcher import Watcher
from Server import settings
from pathlib import Path
import json


if __name__ == '__main__':
    watcher = Watcher(settings["activity_name"])
    with Path("discord_bot_token.json").open() as file:
        bot_token = json.load(file)
    watcher.run(bot_token)
