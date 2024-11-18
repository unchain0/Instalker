import random
import time

import instaloader


class StealthRateController(instaloader.RateController):
    """Enhanced RateController with anti-detection measures."""

    def __init__(self, context: instaloader.InstaloaderContext) -> None:
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
        # Add random variation (±15%)
        jitter = secs * random.uniform(-0.15, 0.15)
        adjusted_sleep = max(0.1, secs + jitter)

        # Add micro-pauses for more human-like behavior
        chunks = int(adjusted_sleep / 0.5)
        for _ in range(chunks):
            time.sleep(0.5 + random.uniform(0.1, 0.3))

        remaining = adjusted_sleep % 0.5
        if remaining > 0:
            time.sleep(remaining)

    def wait_before_query(self, query_type: str) -> None:
        """Enhanced wait logic with variable delays."""
        current_time = time.monotonic()

        # Minimum delay between requests
        min_delay = random.uniform(2.0, 4.0)

        # Time since last request
        time_since_last = current_time - self.last_request_time
        if time_since_last < min_delay:
            self.sleep(min_delay - time_since_last)

        # Calculate session duration and adjust delays
        session_duration = current_time - self.session_start_time
        if session_duration > 3600:  # After 1 hour
            self.backoff_factor = min(2.0, self.backoff_factor * 1.1)

        # Apply backoff to standard wait time
        wait_time = self.query_waittime(query_type, current_time, False)
        adjusted_wait = wait_time * self.backoff_factor

        if adjusted_wait > 0:
            self.sleep(adjusted_wait)

        self.last_request_time = time.monotonic()

    def handle_429(self, query_type: str) -> None:
        """Enhanced 429 handling with exponential backoff."""
        self.backoff_factor *= 1.5
        current_time = time.monotonic()

        # Calculate longer wait time
        base_wait = self.query_waittime(query_type, current_time, True)
        extended_wait = base_wait * self.backoff_factor

        # Add random extra delay
        extra_delay = random.uniform(30, 180)
        total_wait = extended_wait + extra_delay

        self._context.error(
            f"Rate limit hit. Backing off for {int(total_wait)} seconds"
        )
        self.sleep(total_wait)
