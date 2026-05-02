"""[SPEC-B-015] Unit tests: per-provider token-bucket throttle (AC-3).

5 concurrent acquires for one provider with quota=2 must yield 2 acquired
and 3 queued (no loss). Releases dequeue FIFO.
"""

from __future__ import annotations


class TestAC3ProviderQuotaThrottling:
    """Single provider overflow -> 3 queued, 2 acquired, none lost."""

    def test_quota_of_two_with_five_acquires_puts_three_in_queue(self):
        from src.backend.workers.p7a_throttle import ProviderThrottle

        throttle = ProviderThrottle(quotas={"unsplash": 2})
        results = [throttle.try_acquire("unsplash") for _ in range(5)]

        # First two granted, remaining three queued
        assert results == [True, True, False, False, False]
        assert throttle.in_flight("unsplash") == 2
        assert throttle.queued("unsplash") == 3

    def test_release_drains_queue_to_next_waiter(self):
        from src.backend.workers.p7a_throttle import ProviderThrottle

        t = ProviderThrottle(quotas={"pexels": 2})
        for _ in range(5):
            t.try_acquire("pexels")
        # Release one slot -> next queued waiter promotes to in-flight
        promoted = t.release("pexels")
        assert promoted is True
        assert t.in_flight("pexels") == 2
        assert t.queued("pexels") == 2

    def test_release_when_no_waiters_only_decrements(self):
        from src.backend.workers.p7a_throttle import ProviderThrottle

        t = ProviderThrottle(quotas={"aiva": 1})
        assert t.try_acquire("aiva") is True
        # No queued waiter: release returns False (nothing to promote)
        assert t.release("aiva") is False
        assert t.in_flight("aiva") == 0
        assert t.queued("aiva") == 0

    def test_multi_provider_isolation(self):
        """Provider A overflow must not affect provider B."""
        from src.backend.workers.p7a_throttle import ProviderThrottle

        t = ProviderThrottle(quotas={"unsplash": 1, "pexels": 1})
        assert t.try_acquire("unsplash") is True
        assert t.try_acquire("unsplash") is False  # queued
        # Pexels quota is independent
        assert t.try_acquire("pexels") is True
        assert t.in_flight("pexels") == 1
        assert t.queued("pexels") == 0

    def test_unknown_provider_uses_default_quota(self):
        """Providers not listed in quotas fall back to default_quota."""
        from src.backend.workers.p7a_throttle import ProviderThrottle

        t = ProviderThrottle(quotas={}, default_quota=1)
        assert t.try_acquire("newcomer") is True
        assert t.try_acquire("newcomer") is False  # queued

    def test_no_loss_five_acquires_accounted(self):
        """AC-3 explicit: 5 acquires, quota=2 -> 2 acquired + 3 queued,
        total accounted == 5."""
        from src.backend.workers.p7a_throttle import ProviderThrottle

        t = ProviderThrottle(quotas={"unsplash": 2})
        for _ in range(5):
            t.try_acquire("unsplash")
        assert t.in_flight("unsplash") + t.queued("unsplash") == 5
