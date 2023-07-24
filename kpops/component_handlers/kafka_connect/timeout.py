import asyncio
import inspect
import logging
from asyncio import TimeoutError
from typing import Awaitable, Callable, TypeVar

log = logging.getLogger("Timeout")

T = TypeVar("T")


async def timeout(func: Callable[..., T] | Awaitable[T], *, secs: int = 0) -> T | None:
    """
    Sets a timeout for a given lambda function
    :param func: The callable function
    :param secs: The timeout in seconds
    """
    try:
        if inspect.isawaitable(func):
            runner = func
        else:
            runner = asyncio.to_thread(func)
        task = asyncio.create_task(runner)
        if secs == 0:
            return await task
        else:
            return await asyncio.wait_for(task, timeout=secs)
    except TimeoutError:
        log.error(
            f"Kafka Connect operation {func.__name__} timed out after {secs} seconds. To increase the duration, set the `timeout` option in config.yaml."
        )
