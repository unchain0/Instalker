"""Module containing a custom RateController.

The custom RateController adds a random delay to the sleep time.
"""

import time
from secrets import randbelow

from instaloader import RateController


class MyRateController(RateController):
    """Custom RateController that adds a random delay to the sleep time."""

    def sleep(self, secs: float) -> None:
        """Sleep for a given number of seconds plus a random delay."""
        time.sleep(secs + randbelow(8) + 15)
