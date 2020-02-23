from typing import *
import socket
import asyncio
import subprocess
from . import commands
from . import Communication
from . import connection_details
from .errors import DisconnectedFromServer, ConnectionLostFromServer


def setup_socket() -> socket.socket:
    """
    sets up the client socket

    :return: socket.socket
    """
    sock = socket.socket()
    sock.setblocking(False)
    return sock


def communication_signature(communication: Type[Communication]):
    """
    creates a byte signature from a class dict
    this signature byte signature is used to see if the server and
    client are setup to be able to properly communicate

    the keys under 'commands' in Server/settings.json must match with Client/settings.json
    must be identical and the response codes must be identical
    :param communication: Communication class from __init__.py
    :return: bytes, byte signature
    """
    attrs = {attr: value for attr, value in communication.__dict__.items()
             if not attr.startswith("__") or not attr.startswith("_")}

    bites = b"".join([str(attr).encode() + str(value).encode() for attr, value in attrs.items()])
    return bites


def run_command(command: str) -> bytes:
    """
    runs a command in the shell

    :param command: command to be ran
    :return: result from the command
    """
    if command in commands:
        process = subprocess.run(
            commands[command].split(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        if process.stderr:
            return process.stderr
        elif process.stdout:
            return process.stdout
        else:
            return Communication.commands_success
    else:
        return Communication.command_not_found


class Client:
    """
    a client that will receive commands to be executed from a server and reply back with the result
    """
    def __init__(self, loop=None) -> None:
        self.socket = setup_socket()
        self.loop = loop if loop else asyncio.get_event_loop()
        self.communication = communication_signature(Communication)

    def close(self) -> None:
        """
        closes the connection with the server and the own socket

        :return: None
        """
        self.socket.close()
        self.socket = socket.socket()
        self.socket.setblocking(False)

    async def send(self, data: bytes) -> None:
        """
        sends data back to the server after successful command execution

        or a response code about it being successfully executed
        :param data: bytes, result from command execution
        :return: None
        """
        await self.loop.sock_sendall(self.socket, data)

    async def receive(self) -> None:
        """
        receives a command or response code from the server

        the received command will be executed and if it returns anything
        it will be sent back to the server
        :return: None
        """
        data = await self.loop.sock_recv(self.socket, 1024)
        if data == Communication.disconnected:
            raise ConnectionLostFromServer
        elif data == Communication.disconnect:
            raise DisconnectedFromServer
        else:
            stdout = run_command(data.decode())
            await self.send(stdout)

    async def await_reception(self) -> None:
        """
        awaits commands from the server

        :return: None
        """
        while True:
            await self.receive()

    async def connect(self) -> None:
        """
        reaches out to connect to a server

        if server closes down there will be attempts to reconnect every 3 seconds
        unless the server specifically told the client to disconnect
        :return: None
        """
        try:
            print("client awaiting server for connection...")
            await self.loop.sock_connect(self.socket, connection_details)
            print("connected with server.")
            await self.send(self.communication)
            await self.await_reception()
        except (ConnectionError, ConnectionLostFromServer):
            print("disconnected from the client, attempting reconnection")
            self.socket = setup_socket()
            await asyncio.sleep(3)

    async def run(self) -> None:
        """
        runs the client

        :return: None
        """
        try:
            while True:
                await self.connect()
        except DisconnectedFromServer:
            print("client was disconnected from the server.")
        except Exception as e:
            self.close()
            raise e

