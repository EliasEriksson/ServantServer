from Client.client import Client
import asyncio


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    client = Client()
    try:
        loop.run_until_complete(client.run())
    except KeyboardInterrupt:
        client.close()
