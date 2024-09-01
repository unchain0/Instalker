import time

from instaloader import InstaloaderContext, RateController

TIMER = 5


class MyRateController(RateController):
    def __init__(self, context: InstaloaderContext):
        super().__init__(context)
        self._earliest_next_request_time = TIMER
        self._iphone_earliest_next_request_time = TIMER

    def sleep(self, secs):
        time.sleep(secs + TIMER)
