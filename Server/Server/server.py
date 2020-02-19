from typing import Union
import socket
import asyncio
from . import client_wal


class Server:
    binding_details = ("", 1337)

    def __init__(self, loop=None):
        self.connection: Union[socket.socket, None] = None
        self.socket = socket.socket()
        self.socket.bind(self.binding_details)
        self.socket.listen(1)
        self.socket.setblocking(False)
        self.loop = loop if loop else asyncio.get_event_loop()

    async def run_server(self):
        client_wal()
        await self._recieve()
        await self._send(b"run_server")
        await self._recieve()

    async def stop_server(self):
        await self._send(b"stop_server")
        await self._recieve()

    async def logged_in_users(self):
        print("atempting to execute who on client ")
        await self._send(b"logged_in_users")
        return await self._recieve()

    async def sleep(self):
        await self._send(b"sleep")
        # await self._recieve()

    async def ls(self):
        print("atempting to execute ls on client")
        await self._send(b"ls")
        return await self._recieve()

    def _close(self):
        self.socket.close()
        self.connection = None

    async def _send(self, data: bytes):
        print(f"server sent '{data}' to the client")
        await self.loop.sock_sendall(self.connection, data)

    async def _recieve(self) -> str:
        data = await self.loop.sock_recv(self.connection, 1024)
        return data.decode("utf-8")

    async def _accept_connection(self):
        print("server awaiting client for connection...")
        self.connection, _ = await self.loop.sock_accept(self.socket)
        print("server connected with the client, now waiting for client to send anything...")
        data = await self._recieve()
        print(f"recieved {data} from the server. now waiting for events on discord to proceed.")

    async def run(self):
        try:
            while True:
                await self._accept_connection()
        except KeyboardInterrupt:
            self._close()
        except Exception as e:
            self._close()
            raise e
