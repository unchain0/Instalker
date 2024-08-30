import time
from random import randint

from instaloader import InstaloaderContext, RateController


class MyRateController(RateController):
    def __init__(self, context: InstaloaderContext):
        super().__init__(context)
        self._earliest_next_request_time = randint(3, 5)
        self._iphone_earliest_next_request_time = randint(3, 5)

    def sleep(self, secs):
        time.sleep(secs + randint(3, 5))
