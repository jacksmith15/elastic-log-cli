from collections.abc import Callable, Generator
from contextlib import contextmanager
from time import sleep
from typing import Type

BackoffGenerator = Generator[None, Exception | None, None]


class Backoff:
    """Simple wrapper around generators for doing backoff.

    The generator should send None on success, or an exception on failure.
    """

    def __init__(self, generator: BackoffGenerator):
        self._generator = generator
        self._generator.send(None)

    def reset(self):
        self._generator.send(None)

    def trigger(self, exc: Exception):
        self._generator.send(exc)

    @contextmanager
    def on(self, *exception_types: Type[Exception]):  # pylint: disable=invalid-name
        try:
            yield
            self.reset()
        except exception_types as exc:
            self.trigger(exc)


def exponential_backoff(
    base: float = 2.0,
    factor: float = 1.0,
    maximum: int = 10,
    on_backoff: Callable[[Exception, float], None] = None,
) -> Backoff:
    """Exponential back-off.

    Usage:

        backoff = exponential_backoff()
        while True:
            with backoff.on(MyException, MyOtherException):
                ...
    """

    def _generator() -> BackoffGenerator:
        count = 0
        while True:
            exc = yield
            if exc is None:
                count = 0
                continue
            if count >= maximum - 1:
                raise exc
            backoff = factor * base**count
            if on_backoff:
                on_backoff(exc, backoff)
            sleep(backoff)
            count += 1

    return Backoff(_generator())
