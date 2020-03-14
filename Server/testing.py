import asyncio


async def sleeper():
    print("sleeping for 5...")
    await asyncio.sleep(5)
    print("woke up!")


async def cancel(task):
    print("canceling the task...")
    task.cancel()
    print("task canceled.")


async def main():
    task1 = asyncio.create_task(sleeper())
    task2 = asyncio.create_task(cancel(task1))

    print("starting the first task")
    try:
        pass
        # task1.cancel()
        await task2
        # await asyncio.gather(task2)
    except asyncio.CancelledError:
        print("task was canceled")

    print("starting the second task")
    print("finishing up")


def tester(n: int) -> str:
    if n < 0:
        return "yes"
    return ""


def mine():
    if result := tester(-1):
        print("inside")
    else:
        print("outside")


if __name__ == '__main__':
    asyncio.run(main())
    # mine()
