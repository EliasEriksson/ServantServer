from typing import *
import discord
import asyncio
from .server import Server


def contains_activity(activity_name: str, member: discord.Member) -> bool:
    """
    checks weather the member is preforming a specific activity
    """
    return any([True if activity and activity.name and activity_name.lower() in activity.name.lower() else False
                for activity in member.activities])


class Watcher(discord.Client):
    """
    utilizes the servant server/client to be able to determine if a game server host PC
    should be kept awake or put to sleep (when no one is using it)
    """
    def __init__(self, settings: dict):
        """
        initiates the watcher

        self.server is used to communicate between the servant/server and the servant/client
        self.activity name is the activity that will be tracked to sleep / wake the servant/client
        self.scheduled_shutdown is to be able to have access to canceling the shutdown from anywhere in the class
        """
        super(Watcher, self).__init__()
        self.server = Server(self.loop)
        self.activity_name = settings["activity_name"]
        self._scheduled_shutdown: Union[asyncio.Task, None] = None

    async def safe_to_shutdown(self) -> bool:
        """
        checks for reasons it would not be safe to shutdown

        if any local user is logged in
        if the game server have any connections
        if anyone is playing the game (on discord)
        """
        if not await self.server.run_command("logged_in_users"):
            connections = await self.server.run_command("connections")
            if connections:
                if not any([contains_activity(self.activity_name, member)
                            for guild in self.guilds
                            for member in guild.members]):
                    return True
                else:
                    print("there are still players playing the game on discord")
            else:
                print("there are still connections to the server")
        else:
            print("there are still users logged in")
        return False

    async def initiate_shutdown(self):
        """
        initiates a countdown for a shutdown (sleep)

        after the countdown a second set of checks is made to ensure that its safe to shutdown
        """
        print("initiates shutdown")
        await asyncio.sleep(320)
        # TODO edit parsing for read_log in server/settings.json
        print("shutdown wait finished, double checking one last time....")
        if await self.safe_to_shutdown() and not self.server.run_command("read_log"):
            print("putting client to sleep")
            await self.server.run_command("sleep")

    def cancel_shutdown(self):
        """
        cancels a shutdown if there is one scheduled
        """
        if self._scheduled_shutdown:
            print("scheduled shutdown detected and stopped")
            self._scheduled_shutdown.cancel()
            self._scheduled_shutdown = None

    async def on_member_update(self, *_):
        """
        checks weather the game server should be alive or if the servant/client should be put to sleep

        given parameters are not required as only the updated state of all users visible for the
            bot is used. using *_ to indicate that they are not used
        """
        if await self.safe_to_shutdown() and not self._scheduled_shutdown:
            # if its safe to shutdown an attempt to shut down is made
            try:
                # sets the task to variable so it can be canceled from anywhere within the class
                self._scheduled_shutdown = asyncio.create_task(self.initiate_shutdown())
                await self._scheduled_shutdown
            except (asyncio.CancelledError, TypeError):
                # shutdown was canceled during or before initiation
                # the cleanup is handled in self.cancel_shutdown as that executes synchronously
                print("the initiated shutdown did not finish")
        else:
            # making sure the server is not shutting down and if it is cancel the shutdown
            # sending any command to make sure the client is awake
            self.cancel_shutdown()
            await self.server.run_command("ls")

    async def on_ready(self):
        print("Ready.")
        await self.server.run()

