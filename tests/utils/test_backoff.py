import time
from itertools import pairwise

import pytest

from elastic_log_cli.utils.backoff import exponential_backoff


class MockException(Exception):
    pass


class TestBackoff:
    @staticmethod
    def should_backoff_on_specified_errors():
        attempts = []
        backoff = exponential_backoff(
            factor=0.001,  # Start at 1ms
            base=2.0,  # Double the wait each time
            maximum=5,  # Give up after 5 failures
        )
        count = 0
        with pytest.raises(MockException):
            while True:
                count += 1
                with backoff.on(MockException):
                    if count == 5:
                        continue
                    attempts.append(time.monotonic())
                    raise MockException()

        assert len(attempts) == 9

        before_reset = attempts[:4]
        after_reset = attempts[4:]

        for backoff_sequence in (before_reset, after_reset):
            waits = [end - start for start, end in pairwise(backoff_sequence)]
            assert 0.0009 < waits[0] < 0.0013  # Wait around 1ms for first backoff after reset
            for former, latter in pairwise(waits):
                assert 1.8 < latter / former < 2.2  # Double the backoff on each successive error
