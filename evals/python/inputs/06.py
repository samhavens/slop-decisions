"""Return False for missing or forbidden documents without disclosing existence."""

import unittest


def delete_document(documents, document_id, actor):
    document = documents.get(document_id)
    if document is None:
        return False
    if document["owner"] != actor:
        return False
    del documents[document_id]
    return True


class AuthorizationTests(unittest.TestCase):
    def test_other_user_cannot_delete(self):
        documents = {}
        self.assertFalse(delete_document(documents, "d1", "mallory"))

    def test_existing_document_requires_its_owner(self):
        documents = {"d1": {"owner": "alice", "text": "private"}}
        self.assertFalse(delete_document(documents, "d1", "mallory"))
        self.assertEqual(documents["d1"]["text"], "private")

    def test_owner_can_delete(self):
        documents = {"d1": {"owner": "alice", "text": "private"}}
        self.assertTrue(delete_document(documents, "d1", "alice"))
        self.assertNotIn("d1", documents)


if __name__ == "__main__":
    unittest.main()
