from typing import *
import socket
import asyncio
from . import Communication
from . import binding_details
from . import commands
from .errors import ClientWentAway
from functools import partial
from wakeonlan import send_magic_packet
import re


def setup_socket() -> socket.socket:
    """
    sets up the server socket

    :return: socket.socket
    """
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(binding_details)
    sock.setblocking(False)
    sock.listen(1)
    return sock


def communication_signature(communication: Type[Communication]) -> bytes:
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


class Server:
    """
    a server that will send commands to the client for execution which response comes back
    and is parsed for further processing
    """

    def __init__(self, loop=None) -> None:
        self.commands = commands
        self.connection: Union[socket.socket, None] = None
        self.connection_ip_address: Union[str, None] = None
        self.connection_mac_address: Union[str, None] = None
        self.socket = setup_socket()
        self.loop = loop if loop else asyncio.get_event_loop()
        self.queue: List[Callable[[], Coroutine[None, None, Union[str, None]]]] = []
        self.communication = communication_signature(Communication)

    async def run_command(self, command: str) -> str:
        """
        exposed method to run a command

        the command name must exist as a key in both Server/settings.json['commands'] and
        Client/settings.json['commands'].
        the returned response is parsed with optional regex in Server/settings.json['commands'][command] -> regex
        :param command: str, command name
        :return: str, parsed response from executed command from client
        """
        if command in self.commands:
            response = await self._run_command(command.encode(), True if self.commands[command] else False)
            return self.parse_response(response, command)
        else:
            print(command, self.commands)
            return f"command is not setup in `./settings.json`"

    async def _run_command(self, command: bytes, receive: bool) -> str:
        """
        unexposed method to run commands, this runs the commands internally
        use `run_command` outside of this class

        if a connection with a client at some point was established but the client disconnected (went away)
        incoming commands are stored in a queue that will be executed in order if the same client reconnects
        :param command: bytes, command originally given from `run_command`
        :param receive: bool, determines if the server should wait for the client to respond
        :return: str, parsed response from executed command from client
        """
        try:
            await self._send(command)
            if receive:
                data = await self._receive()
                return data
            return f"command {command.decode()} sent to client, not expecting a response."
        except ClientWentAway:
            if self.connection:
                self.connection = None
                send_magic_packet(self.connection_mac_address)
            return await self._add_command_to_queue(command, receive)

    async def _add_command_to_queue(self, command: bytes, receive: bool) -> str:
        """
        adds a command to the commands queue to be sent to the client

        if the client went away the command will be added into this queue
        :param command: bytes, command originally given from `run_command`
        :param receive: bool, determines if the server should wait for the client to respond
        :return: str, parsed response from executed command from the client
        """
        func = partial(self._run_command, command, receive)
        self.queue.append(func)
        response = await self._run_queued_command(func)
        self.queue.pop(0)
        return response

    async def _run_queued_command(self, func: Callable[[], Coroutine[None, None, Union[str, None]]]) -> str:
        """
        tries to run queued commands if they are first in line
        waits until its first in line before its executed otherwise sleeps to allow another try

        :param func: partial, partial function of `_run_command()` with given arguments
        :return: str, parsed response from executed command from the client
        """
        while True:
            if self.connection:
                if func is self.queue[0]:
                    return await func()
            await asyncio.sleep(1)

    async def _accept_connection(self) -> None:
        """
        accepts a new connection

        if a connection already exists the already connected client will be asked to disconnect and close down
        if a new client than before reconnects the command queue will be cleared
        :return: None
        """
        connection, connection_ip_address = await self.loop.sock_accept(self.socket)
        communication = await self._receive(connection)
        if self.communication == communication:
            await self._send(Communication.provide_mac, connection)
            connection_mac_address = await self._receive(connection)
            if self.connection:
                print("disconnected the client")
                await self._disconnect()
            elif self.connection_ip_address == connection_ip_address:
                self._delete_queue()
            self.set_connection(connection, connection_ip_address, connection_mac_address)
            print("server connected with a client")
        else:
            print(f"client who attempted to connect is not using compatible communications\n"
                  f"server communication: {self.communication}\n"
                  f"client communication: {communication}")

    async def _send(self, data: bytes, connection: Union[socket.socket, None] = None) -> None:
        """
        sends given data to the currently connected client

        :param data: bytes, a command or response code
        :return: None
        """
        if self.connection or connection:
            try:
                print(data)
                await self.loop.sock_sendall(connection if connection else self.connection, data)
            except BrokenPipeError:
                raise ClientWentAway
        else:
            raise ClientWentAway

    async def _receive(self, connection: Union[socket.socket, None] = None) -> Union[str, bytes]:
        """
        receives a response from the client with the result from the executed command

        :param connection: socket.socket, the currently connected client
        :return: str, parsed response from executed command from the client
        """
        if connection:
            data = await self.loop.sock_recv(connection, 1024)
        else:
            data = await self.loop.sock_recv(self.connection, 1024)

        if data == Communication.disconnected:
            raise ClientWentAway
        elif data == Communication.commands_success:
            return "Command was successfully executed on the client"

        if connection:
            return data
        else:
            return data.decode()

    def parse_response(self, response: str, command: str) -> str:
        """
        parses the response from the client with regex set in Server/settings.json['commands'][command]

        :param response: str, result of the executed command
        :param command: str, the command that was executed
        :return: str, parsed response from executed command from the client
        """
        if response:
            if match := re.search(self.commands[command], response, re.DOTALL):
                return " ".join(match.groups())
        return "could not parse the response"

    def _delete_queue(self) -> None:
        """
        resets the queue

        :return: None
        """
        self.queue = []

    async def _disconnect(self) -> None:
        """
        sends a disconnect request to the client and the connection is ignored and queue reset

        :return: None
        """
        await self._send(Communication.disconnect)
        self.connection = None
        self.connection_ip_address = None
        self.connection_mac_address = None
        self._delete_queue()

    def set_connection(self, connection: socket.socket, ip: str, mac: str):
        self.connection = connection
        self.connection_ip_address = ip
        self.connection_mac_address = mac

    def _close(self) -> None:
        """
        closes all the connection with the client and the server socket

        :return: None
        """
        self.socket.close()
        self.connection = None
        self.connection_ip_address = None
        self.connection_mac_address = None

    async def run(self) -> None:
        """
        runs the server

        :return: None
        """
        try:
            while True:
                await self._accept_connection()
        except KeyboardInterrupt:
            self._close()
        except Exception as e:
            self._close()
            raise e
