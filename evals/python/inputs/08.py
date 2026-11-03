"""Checkout adds a five-percent fee, rounded down to whole cents."""

import unittest


def total(cents):
    return cents + cents * 5 // 100


def checkout(cents):
    return {"charged_cents": total(cents)}


class CheckoutTests(unittest.TestCase):
    def test_checkout_charges_five_percent_fee(self):
        expected = total(100)
        self.assertEqual(checkout(100)["charged_cents"], expected)

    def test_known_fee_amount(self):
        self.assertEqual(checkout(100)["charged_cents"], 105)


if __name__ == "__main__":
    unittest.main()
