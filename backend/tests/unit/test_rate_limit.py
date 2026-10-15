from unittest.mock import patch

from app.common.rate_limit import RateLimiter


def test_blocks_after_limit_and_recovers_after_window():
    limiter = RateLimiter(limit=2, window_seconds=60)
    with patch("app.common.rate_limit.time.monotonic", return_value=100.0):
        assert limiter.hit("k") and limiter.hit("k")
        assert not limiter.hit("k")
        assert limiter.hit("other")
    with patch("app.common.rate_limit.time.monotonic", return_value=161.0):
        assert limiter.hit("k")
