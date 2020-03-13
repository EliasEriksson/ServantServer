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
        self.shutting_down = False

    async def safe_to_shutdown(self) -> bool:
        if not await self.server.run_command("logged_in_users"):
            if await self.server.run_command("connections"):
                if not any([contains_activity(self.activity_name, member)
                            for guild in self.guilds
                            for member in guild.members]):
                    return True
        return False

    async def initiate_shutdown(self):
        while self.shutting_down:
            pass



    async def on_ready(self):
        print("Ready.")
        await self.server.run()

    async def on_message(self, message: discord.Message):
        pass

    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if self.safe_to_shutdown():
            # initiate shutdown
            pass
        else:
            # sending any command to make sure the server is awake
            await self.server.run_command("start_server")

