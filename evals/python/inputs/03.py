"""Public input boundary: normalize strings and reject other runtime values."""

import unittest


def normalize_slug(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError("slug must be text")
    return value.strip().lower()


class SlugTests(unittest.TestCase):
    def test_rejects_non_text_input(self):
        for value in (None, 42, [], {}):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "must be text"):
                normalize_slug(value)

    def test_normalizes_text(self):
        self.assertEqual(normalize_slug("  Billing  "), "billing")


if __name__ == "__main__":
    unittest.main()
