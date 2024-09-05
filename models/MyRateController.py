from random import randint
from time import sleep

from instaloader import InstaloaderContext, RateController


class MyRateController(RateController):
    def __init__(self, context: InstaloaderContext):
        super().__init__(context)
        self._earliest_next_request_time = randint(13, 55)
        self._iphone_earliest_next_request_time = randint(13, 55)

    def sleep(self, secs: float) -> None:
        sleep(secs + randint(13, 55))
