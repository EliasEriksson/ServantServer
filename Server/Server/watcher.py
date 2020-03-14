import discord
from .server import Server


def contains_activity(activity_name: str, member: discord.Member) -> bool:
    return any([True if activity and activity.name and activity_name.lower() in activity.name.lower() else False
                for activity in member.activities])


class Watcher(discord.Client):
    def __init__(self, settings: dict):
        super(Watcher, self).__init__()
        self.server = Server(self.loop)
        self.activity_name = settings["activity_name"]

    async def on_ready(self):
        print("Ready.")
        await self.server.run()

    async def on_message(self, message: discord.Message):
        pass

    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if not any([contains_activity(self.activity_name, member)
                    for guild in self.guilds
                    for member in guild.members]):
            # if not any member in any guild is currently doing tracked activity
            users = await self.server.run_command("logged_in_users")
            print(users)
            if not users:
                pass
        else:
            result = await self.server.run_command("read_server")
            print(result)
