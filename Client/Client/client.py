from typing import Union
import socket
import asyncio
import subprocess
from . import commands, DisconnectedFromServer


def run_command(command: str) -> bytes:
    if command in commands:
        process = subprocess.run(
            commands[command]["command"].split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        if process.stderr:
            return process.stderr
        else:
            return process.stdout
    else:
        return b"command not found"


class Client:
    connection_details = ("127.0.0.1", 1337)

    def __init__(self, loop=None):
        self.socket = socket.socket()
        self.socket.setblocking(False)
        self.loop = loop if loop else asyncio.get_event_loop()

    def close(self):
        """
        closes the current socket and reopens a new one ready for connection
        """
        self.socket.close()
        self.socket = socket.socket()
        self.socket.setblocking(False)

    async def send(self, data: bytes):
        await self.loop.sock_sendall(self.socket, data)

    async def recieve(self):
        """
        recieves a command from the
        sends   b"command not found"
                or whatever is returned from stdout (including b"")
        """
        data = await self.loop.sock_recv(self.socket, 1024)
        print(f"client recieved '{data}' from the server")
        stdout = run_command(data.decode("utf-8"))
        await self.send(stdout)

    async def await_reception(self):
        while True:
            print("Awaiting a message from the server.")
            await self.recieve()

    async def connect(self):
        print("client awaiting server for connection...")
        await self.loop.sock_connect(self.socket, self.connection_details)
        print("connected with server, sending message about being connected")
        await self.send(b"connected")
        print("quick message sent")
        await self.await_reception()

    async def run(self):
        try:
            while True:
                await self.connect()
        except Exception as e:
            self.close()
            raise e

