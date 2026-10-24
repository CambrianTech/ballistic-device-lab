import unittest
from unittest.mock import Mock

import numpy as np

from physics_layers.current_cache import ExactCurrentCache


class CurrentCacheTests(unittest.TestCase):
    def test_exact_reuse_copies_and_distinguishes_jacobian_perturbation(self):
        provider = Mock()
        provider.currents.return_value = np.array([1.0, -1.0, 0.0, 0.0])
        cache = ExactCurrentCache(provider)
        first = cache.currents([0.005, -0.005, 0, 0])
        first[0] = 99
        self.assertEqual(cache.currents([0.005, -0.005, 0, 0])[0], 1)
        self.assertEqual(provider.currents.call_count, 1)
        cache.currents([0.005, -0.005, 1e-12, 0])
        self.assertEqual(provider.currents.call_count, 2)

    def test_failure_not_cached_and_capacity_bounded(self):
        provider = Mock()
        provider.currents.side_effect = [ArithmeticError(), np.zeros(4), np.zeros(4), np.zeros(4)]
        cache = ExactCurrentCache(provider, capacity=1)
        with self.assertRaises(ArithmeticError):
            cache.currents([0] * 4)
        cache.currents([0] * 4)
        cache.currents([1] * 4)
        cache.currents([0] * 4)
        self.assertEqual(provider.currents.call_count, 4)
        self.assertEqual(len(cache._cache), 1)
