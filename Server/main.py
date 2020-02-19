from Server.watcher import Watcher
from Server import settings


if __name__ == '__main__':
    watcher = Watcher(settings["activity_name"])
    watcher.run("NTU1ODQ1MzI4MTUxMTE3ODQ1.XkFFbw.spXyVpNdhH9k2Xn9H4L6cvJZykE")
