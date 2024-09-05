from random import randint
from time import sleep

from instaloader import RateController


class MyRateController(RateController):
    def wait_before_query(self, query_type: str) -> None:
        sleep(randint(20, 40))
        return None
