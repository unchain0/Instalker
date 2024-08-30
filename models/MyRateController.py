import time
from random import random

from instaloader import InstaloaderContext, RateController


class MyRateController(RateController):
    def __init__(self, context: InstaloaderContext):
        super().__init__(context)
        self._earliest_next_request_time = 5 + random()
        self._iphone_earliest_next_request_time = 5 + random()

    def sleep(self, secs):
        time.sleep(secs + 5 + random())
