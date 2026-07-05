#!/usr/bin/env python3
"""Offline tests for team_mailboxes.py — pure resolution + env-driven credential lookup."""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import team_mailboxes as tm


class ResolveTests(unittest.TestCase):
    def test_display_name(self):
        self.assertEqual(tm.resolve("Nico")["email"], "nicolas@automatisierbar.ch")
        self.assertEqual(tm.resolve("Nico")["mailbox_name"], "nicolas")
        self.assertEqual(tm.resolve("Nico")["person"], "Nico")

    def test_aliases_localpart_and_case(self):
        for alias in ("nicolas", "NICOLAS", "nico", " Nico "):
            self.assertEqual(tm.resolve(alias)["email"], "nicolas@automatisierbar.ch")

    def test_all_five(self):
        self.assertEqual(tm.address("Joaquin"), "joaquin@automatisierbar.ch")
        self.assertEqual(tm.address("Tej"), "tej@automatisierbar.ch")
        self.assertEqual(tm.address("Patrik"), "patrik@automatisierbar.ch")
        self.assertEqual(tm.address("info"), "info@automatisierbar.ch")
        self.assertEqual(set(tm.all_mailboxes()),
                         {"Joaquin", "Tej", "Nico", "Patrik", "info"})

    def test_unknown_raises(self):
        with self.assertRaises(KeyError):
            tm.resolve("Markus")
        with self.assertRaises(KeyError):
            tm.resolve("")

    def test_draft_cfg_rebinds_identity(self):
        base = {"from": "joaquin@automatisierbar.ch", "mailbox_name": "joaquin",
                "sender": "Joaquin Gamonal", "cc": "tej@automatisierbar.ch", "phone": "x"}
        cfg = tm.draft_cfg("Nico", base)
        self.assertEqual(cfg["from"], "nicolas@automatisierbar.ch")
        self.assertEqual(cfg["mailbox_name"], "nicolas")
        self.assertEqual(cfg["sender"], "Nico")
        self.assertIn("mail_token_env", cfg)
        self.assertEqual(cfg["phone"], "x")          # untouched keys carried through
        self.assertEqual(base["from"], "joaquin@automatisierbar.ch")  # base not mutated


class CredentialTests(unittest.TestCase):
    def setUp(self):
        # Force env() to ignore any real .env so the tests are deterministic.
        self._orig_env = tm.env
        self._store = {}
        tm.env = lambda k, d=None: self._store.get(k, d)

    def tearDown(self):
        tm.env = self._orig_env

    def test_password_env_name_primary(self):
        self.assertEqual(tm.imap_password_env("Nico"), "NICO_IMAP_PASSWORD")
        self.assertEqual(tm.imap_password_env("Tej"), "TEJ_IMAP_PASSWORD")
        self.assertEqual(tm.imap_password_env("Patrik"), "PATRIK_IMAP_PASSWORD")

    def test_joaquin_falls_back_to_infomaniak(self):
        # No JOAQUIN_* set, but the legacy INFOMANIAK_* is → fallback prefix wins.
        self._store = {"INFOMANIAK_IMAP_PASSWORD": "secret", "INFOMANIAK_IMAP_USER": "joaquin@x"}
        self.assertEqual(tm.imap_password_env("Joaquin"), "INFOMANIAK_IMAP_PASSWORD")
        self.assertEqual(tm.imap_user("Joaquin"), "joaquin@x")
        self.assertTrue(tm.has_creds("Joaquin"))

    def test_dedicated_prefix_preferred_over_fallback(self):
        self._store = {"JOAQUIN_IMAP_PASSWORD": "dedicated",
                       "INFOMANIAK_IMAP_PASSWORD": "legacy"}
        self.assertEqual(tm.imap_password_env("Joaquin"), "JOAQUIN_IMAP_PASSWORD")
        self.assertEqual(tm.imap_password("Joaquin"), "dedicated")

    def test_has_creds_false_when_missing(self):
        self._store = {}
        self.assertFalse(tm.has_creds("Nico"))
        self.assertFalse(tm.has_creds("Tej"))

    def test_imap_user_defaults_to_address(self):
        self._store = {}
        self.assertEqual(tm.imap_user("Nico"), "nicolas@automatisierbar.ch")

    def test_mail_token_env(self):
        self._store = {}
        self.assertEqual(tm.mail_token_env("Nico"), "INFOMANIAK_MAIL_TOKEN")
        self._store = {"NICO_MAIL_TOKEN": "t"}
        self.assertEqual(tm.mail_token_env("Nico"), "NICO_MAIL_TOKEN")


if __name__ == "__main__":
    unittest.main(verbosity=2)
