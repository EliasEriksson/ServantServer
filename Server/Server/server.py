from typing import Union, List, Coroutine
import socket
import asyncio
from . import client_wol
from .errors import ClientWentAway
from functools import partial


def setup_socket(port: int = 6969) -> socket.socket:
    sock = socket.socket()
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", port))
    sock.setblocking(False)
    sock.listen(1)
    return sock


class Server:
    def __init__(self, loop=None, queue: bool = True) -> None:
        self.connection: Union[socket.socket, None] = None
        self.connection_address: Union[str, None] = None
        self.socket = setup_socket()
        self.loop = loop if loop else asyncio.get_event_loop()
        self.queue: Union[List[partial[[], Coroutine[None, None, Union[str, None]]]], None] = [] if queue else None

    async def run_server(self) -> str:
        print("attempting to start the server on the client")
        return await self._run_command_wrapper(b"run_server")

    async def stop_server(self) -> str:
        print("attempting to stop the server on the client")
        return await self._run_command_wrapper(b"stop_server")

    async def logged_in_users(self) -> str:
        print("attempting to execute who on client")
        return await self._run_command_wrapper(b"logged_in_users")

    async def sleep(self) -> None:
        print("attempting to sleep the client")
        await self._run_command(b"sleep", False)

    async def ls(self) -> str:
        print("attempting to execute ls on client")
        return await self._run_command_wrapper(b"ls")

    async def disconnect(self) -> None:
        print("disconnecting the current client")
        await self._send(b"disconnect")
        self.connection = None
        self.connection_address = None
        self._delete_queue()

    async def _run_command_wrapper(self, command: bytes, receive: bool = False):
        if self.queue is not None:
            response = await self._run_command(command, receive)
        else:
            response = await self._add_command_to_queue(command, receive)
        return response

    async def _run_command(self, command: bytes, receive: bool = True) -> Union[str, None]:
        print()
        try:
            await self._send(command)
            if receive:
                data = await self._receive()
                return data

        except ClientWentAway:
            if self.connection:
                print("attempting to awake the client since it went away")
                self.connection = None
                client_wol()
                if self.queue is None:
                    await self._await_connection()
                    return await self._run_command(command, receive)
                else:
                    return await self._add_command_to_queue(command, receive)
            else:
                if self.queue is not None:
                    return await self._add_command_to_queue(command, receive)
                else:
                    return f"skipping command {command.decode('utf-8')} since client is away"

    async def _await_connection(self):
        print("awaiting new connection from client")
        while True:
            if self.connection:
                print("client have reconnected")
                break
            await asyncio.sleep(1)

    async def _run_queued_command(self, func: partial[[], Coroutine[None, None, Union[str, None]]]) -> str:
        print("awaiting new connection from client before running queued command")
        while True:
            if self.connection:
                if func is self.queue[0]:
                    print(f"executing command next in line: {func}")
                    return await func()
                print(f"command not next in line, sleeping and waiting for this commands turn")
            await asyncio.sleep(1)

    async def _add_command_to_queue(self, command: bytes, receive: bool):
        print(f"adding command {command.decode('utf-8')} to the command queue")
        func = partial(self._run_command, command, receive)
        self.queue.append(func)
        response = await self._run_queued_command(func)
        self.queue.pop(0)
        return response

    def _close(self) -> None:
        self.socket.close()
        self.connection = None
        self.connection_address = None

    async def _send(self, data: bytes) -> None:
        if self.connection:
            try:
                await self.loop.sock_sendall(self.connection, data)
                print(f"server sent '{data}' to the client")
            except BrokenPipeError as e:
                print(f"client was away when trying to send {data}")
                print(e)
                raise ClientWentAway
        else:
            raise ClientWentAway

    async def _receive(self) -> str:
        print("server receiving data from client.")
        data = await self.loop.sock_recv(self.connection, 1024)
        print(f"server received {data} from client")
        if data == b"":
            raise ClientWentAway
        return data.decode("utf-8")

    async def _accept_connection(self) -> None:
        print("server awaiting client for connection...")
        connection, connection_address = await self.loop.sock_accept(self.socket)
        if self.connection:
            await self.disconnect()
        elif self.connection_address == connection_address:
            self._delete_queue()

        self.connection = connection
        self.connection_address = connection_address
        print("server connected with a client, now waiting for events on discord to proceed...")

    def _delete_queue(self):
        if self.queue is not None:
            self.queue = []

    async def run(self) -> None:
        try:
            while True:
                await self._accept_connection()
        except KeyboardInterrupt:
            self._close()
        except Exception as e:
            self._close()
            raise e
