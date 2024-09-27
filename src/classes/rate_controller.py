import time
from secrets import randbelow

from instaloader import RateController


class MyRateController(RateController):
    def sleep(self, secs: float) -> None:
        time.sleep(secs + randbelow(8) + 15)
