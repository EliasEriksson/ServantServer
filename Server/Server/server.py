from typing import Union
import socket
import asyncio
from . import client_wal
from .errors import ClientWentAway


def setup_socket(port: int = 6969) -> socket.socket:
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", port))
    sock.setblocking(False)
    sock.listen(1)
    return sock


class Server:
    def __init__(self, loop=None) -> None:
        self.connection: Union[socket.socket, None] = None
        self.socket = setup_socket()
        self.loop = loop if loop else asyncio.get_event_loop()

    async def run_server(self) -> str:
        response = await self._run_command(b"run_server")
        return response

    async def stop_server(self) -> str:
        response = await self._run_command(b"stop_server")
        return response

    async def logged_in_users(self) -> str:
        print("attempting to execute who on client ")
        response = await self._run_command(b"logged_in_users")
        return response

    async def sleep(self) -> None:
        print("attempting to sleep the client")
        await self._run_command(b"sleep", False)

    async def ls(self) -> str:
        print("attempting to execute ls on client")
        response = await self._run_command(b"ls")
        return response

    async def disconnect(self) -> None:
        print("disconnecting the current client")
        await self._send(b"disconnect")
        self.connection = None

    async def await_connection(self):
        while True:
            if self.connection:
                break
            await asyncio.sleep(1)

    async def _run_command(self, command: bytes, receive: bool = True) -> Union[str, None]:
        while True:
            try:
                # could self._send error out if it sends to a connection that went away?
                await self._send(command)
                if receive:
                    return await self._receive()
                else:
                    break
            except ClientWentAway:
                print("Client went away. ")
                self.connection = None
                client_wal()
                print("waiting for client to reconnect.")
                await self.await_connection()
                print(f"client reconnected, attempting to run {command} again")

    def _close(self) -> None:
        self.socket.close()
        self.connection = None

    async def _send(self, data: bytes) -> None:
        print(f"server sent '{data}' to the client")
        await self.loop.sock_sendall(self.connection, data)

    async def _receive(self) -> str:
        data = await self.loop.sock_recv(self.connection, 1024)
        if data == b"":
            raise ClientWentAway
        print(f"server received '{data}' from the client")
        return data.decode("utf-8")

    async def _accept_connection(self) -> None:
        print("server awaiting client for connection...")
        connection, _ = await self.loop.sock_accept(self.socket)
        if self.connection:
            await self.disconnect()
        self.connection = connection
        print("server connected with a client, now waiting for events on discord to proceed...")

    async def run(self) -> None:
        try:
            while True:
                await self._accept_connection()
        except KeyboardInterrupt:
            self._close()
        except Exception as e:
            self._close()
            raise e
