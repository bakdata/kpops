import asyncio


def get_loop():
    return asyncio.get_running_loop()
