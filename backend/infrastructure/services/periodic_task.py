import asyncio
from functools import wraps


def periodic_task(*, delay: float):
    def decorator(func):
        @wraps(func)
        async def wrapped(*args, **kwargs):
            loop = asyncio.get_event_loop()
            res = await func(*args, **kwargs)
            loop.call_later(delay, loop.create_task, wrapped(*args, **kwargs))
            return res

        return wrapped

    return decorator
