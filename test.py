import asyncio


async def hello():
    print("Testing")


async def long():
    return "this is long"


def otherThing():
    loop = asyncio.run(long())


async def main():
    await hello()
    otherThing()
    await hello()

asyncio.run(main())
