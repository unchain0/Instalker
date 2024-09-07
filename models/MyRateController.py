from random import randint
from time import sleep

from instaloader import RateController


class MyRateController(RateController):
    def sleep(self, secs: float) -> None:
        sleep(secs + randint(7, 20))
