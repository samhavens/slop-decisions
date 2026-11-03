"""Caller contract: finish awaiting one transport submission before returning."""

import asyncio
import unittest
from unittest.mock import AsyncMock


async def submit_alert(message, transport):
    await transport(message)


class AlertTests(unittest.TestCase):
    def test_awaits_one_transport_submission(self):
        transport = AsyncMock(return_value=None)
        asyncio.run(submit_alert("disk full", transport))
        transport.assert_awaited_once_with("disk full")


if __name__ == "__main__":
    unittest.main()
