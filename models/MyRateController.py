from random import randint
from time import sleep

import instaloader


class MyRateController(instaloader.RateController):
    def sleep(self, secs: float) -> None:
        sleep(secs + randint(13, 20))
