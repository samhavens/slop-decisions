"""Saving an account must persist it for a later database connection."""

import sqlite3
import tempfile
import unittest
from pathlib import Path


class Accounts:
    def __init__(self, path):
        self.path = path

    def save(self, account_id, name):
        with sqlite3.connect(self.path) as db:
            db.execute("INSERT OR REPLACE INTO accounts VALUES (?, ?)", (account_id, name))


class AccountTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "accounts.sqlite"
        with sqlite3.connect(self.path) as db:
            db.execute("CREATE TABLE accounts (id TEXT PRIMARY KEY, name TEXT)")
        self.accounts = Accounts(self.path)

    def test_saves_account(self):
        with sqlite3.connect(self.path) as db:
            db.execute("INSERT INTO accounts VALUES (?, ?)", ("a1", "Ada"))
        self.accounts.save("a1", "Ada")
        with sqlite3.connect(self.path) as db:
            row = db.execute("SELECT name FROM accounts WHERE id = ?", ("a1",)).fetchone()
        self.assertEqual(row, ("Ada",))

    def test_new_account_survives_reopening_database(self):
        self.accounts.save("a2", "Grace")
        with sqlite3.connect(self.path) as db:
            row = db.execute("SELECT name FROM accounts WHERE id = ?", ("a2",)).fetchone()
        self.assertEqual(row, ("Grace",))


if __name__ == "__main__":
    unittest.main()
