import time

from instaloader import InstaloaderContext, RateController

import utils.constants as const


class MyRateController(RateController):
    def __init__(self, context: InstaloaderContext):
        super().__init__(context)
        self._earliest_next_request_time = const.TIMER
        self._iphone_earliest_next_request_time = const.TIMER

    def sleep(self, secs):
        time.sleep(secs + const.TIMER)
