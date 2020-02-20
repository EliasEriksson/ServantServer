import socket
import asyncio
import subprocess
from . import commands
from .errors import DisconnectedFromServer, ConnectionLostFromServer


def setup_socket() -> socket.socket:
    sock = socket.socket()
    sock.setblocking(False)
    return sock


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
    connection_details = ("127.0.0.1", 6969)

    def __init__(self, loop=None) -> None:
        self.socket = setup_socket()
        self.loop = loop if loop else asyncio.get_event_loop()

    def close(self) -> None:
        """
        closes the current socket and reopens a new one ready for connection
        """
        self.socket.close()
        self.socket = socket.socket()
        self.socket.setblocking(False)

    async def send(self, data: bytes) -> None:
        await self.loop.sock_sendall(self.socket, data)

    async def receive(self) -> None:
        """
        receives a command from the
        sends   b"command not found"
                or whatever is returned from stdout (including b"")
        """
        data = await self.loop.sock_recv(self.socket, 1024)
        if data == b"":
            raise ConnectionLostFromServer
        elif data == b"disconnect":
            raise DisconnectedFromServer
        else:
            print(f"client received '{data}' from the server")
            stdout = run_command(data.decode("utf-8"))
            if not stdout == b"":
                await self.send(stdout)
            else:
                await self.send(b"command executed successfully")

    async def await_reception(self) -> None:
        while True:
            print("Awaiting a message from the server.")
            await self.receive()

    async def connect(self) -> None:
        try:
            print("client awaiting server for connection...")
            await self.loop.sock_connect(self.socket, self.connection_details)
            print("connected with server.")
            await self.await_reception()
        except (ConnectionError, ConnectionLostFromServer) as e:
            print("server refused connection with the client. Server is probably down or firewall blocking the port.")
            print(e)
            print("attempting to reconnect in 3 seconds.")
            print()
            self.socket = setup_socket()
            await asyncio.sleep(3)

    async def run(self) -> None:
        try:
            while True:
                await self.connect()
        except DisconnectedFromServer:
            print("client was disconnected from the server.")
        except Exception as e:
            self.close()
            raise e

