import unittest

from app.schemas.user import UserLogin, UserRegister, normalize_email


class TestEmailNormalization(unittest.TestCase):
    def test_normalize_email_strips_and_lowercases(self):
        self.assertEqual(normalize_email("  CaseUser@Example.COM "), "caseuser@example.com")

    def test_register_schema_normalizes_email(self):
        body = UserRegister(
            username="alice",
            email="Alice@Example.COM",
            password="password123",
        )
        self.assertEqual(body.email, "alice@example.com")

    def test_login_schema_normalizes_email(self):
        body = UserLogin(email="Bob@Example.COM", password="password123")
        self.assertEqual(body.email, "bob@example.com")

    def test_register_rejects_short_password(self):
        with self.assertRaises(Exception):
            UserRegister(username="alice", email="a@b.com", password="short")


class TestPasswordHashRoundtrip(unittest.TestCase):
    def test_hash_and_verify(self):
        from app.core.security import hash_password, verify_password

        hashed = hash_password("correct-horse")
        self.assertTrue(verify_password("correct-horse", hashed))
        self.assertFalse(verify_password("wrong-password", hashed))


if __name__ == "__main__":
    unittest.main()
