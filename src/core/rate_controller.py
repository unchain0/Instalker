import time
from random import uniform

from instaloader import InstaloaderContext, RateController


class StealthRateController(RateController):
    """Enhanced RateController with anti-detection measures."""

    def __init__(self, context: InstaloaderContext) -> None:
        super().__init__(context)
        self.backoff_factor = 1.0
        self.last_request_time = 0.0
        self.session_start_time = time.monotonic()

    def count_per_sliding_window(self, query_type: str) -> int:
        """Reduce request limits to stay well below Instagram's thresholds."""
        base_limit = super().count_per_sliding_window(query_type)
        return int(base_limit * 0.7)  # 30% reduction

    def sleep(self, secs: float) -> None:
        """Add randomized human-like delays."""
        # Add random variation (±25%)
        jitter = secs * uniform(-0.25, 0.25)
        adjusted_sleep = max(0.2, secs + jitter)

        # Add micro-pauses with more variation
        chunks = int(adjusted_sleep / 0.7)  # Larger chunks
        for _ in range(chunks):
            time.sleep(0.7 + uniform(0.2, 0.8))

        remaining = adjusted_sleep % 0.7
        if remaining > 0:
            time.sleep(remaining + uniform(0.1, 0.3))

    def wait_before_query(self, query_type: str) -> None:
        """Enhanced wait logic with variable delays."""
        current_time = time.monotonic()

        # Increased minimum delay between requests
        min_delay = uniform(3.0, 7.0)

        time_since_last = current_time - self.last_request_time
        if time_since_last < min_delay:
            self.sleep(min_delay - time_since_last)

        # Increased backoff after 1 hour
        session_duration = current_time - self.session_start_time
        if session_duration > 3600:
            self.backoff_factor = min(3.0, self.backoff_factor * 1.2)

        wait_time = self.query_waittime(query_type, current_time, False)
        adjusted_wait = wait_time * self.backoff_factor

        if adjusted_wait > 0:
            self.sleep(adjusted_wait)

        self.last_request_time = time.monotonic()

    def handle_429(self, query_type: str) -> None:
        """Enhanced 429 handling with exponential backoff."""

        self.backoff_factor *= 2.0  # Increased multiplier
        current_time = time.monotonic()

        base_wait = self.query_waittime(query_type, current_time, True)
        extended_wait = base_wait * self.backoff_factor

        # Increased random delay range
        extra_delay = uniform(60, 300)  # 1-5 minutes
        total_wait = extended_wait + extra_delay

        self._context.error(
            f"Rate limit hit. Backing off for {int(total_wait)} seconds"
        )
        self.sleep(total_wait)
