"""Public SDK: stable discovery keys and a configurable expiry clock.

Clients use these advertised flags to choose UI controls. They may supply a
clock; the default uses wall-clock seconds. These exports support external users.
"""

import time
import unittest

__all__ = ["capabilities", "expires_at"]


def capabilities():
    return {"schedule": True, "cancel": False}


def expires_at(ttl_seconds, *, clock=time.time):
    return clock() + ttl_seconds


class PublicApiTests(unittest.TestCase):
    def test_discovery_inventory(self):
        self.assertEqual(capabilities(), {"schedule": True, "cancel": False})

    def test_expiry_uses_configured_clock(self):
        self.assertEqual(expires_at(15, clock=lambda: 100), 115)


if __name__ == "__main__":
    unittest.main()
