import time
from random import random

import instaloader


class MyRateController(instaloader.RateController):
    def sleep(self, secs: float):
        time.sleep(random() + 1.5)
