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
        if contains_activity(self.activity_name, before):
            # stopped using tracked activity
            users = await self.server.run_command("logged_in_users")
            await before.send(users)

        if contains_activity(self.activity_name, after):
            # started using tracked activity
            ls = await self.server.run_command("ls")
            await before.send(ls)

