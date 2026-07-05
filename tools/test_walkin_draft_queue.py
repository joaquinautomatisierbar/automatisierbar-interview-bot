#!/usr/bin/env python3
"""Offline tests for walkin_draft_queue.py — enqueue, pending ordering, flock claim, stats."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class QueueTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="wq-test-")
        os.environ["WALKIN_DRAFT_QUEUE_DIR"] = self.dir
        # fresh import each test so queue_dir() re-reads the env
        for m in ("walkin_draft_queue",):
            sys.modules.pop(m, None)
        import walkin_draft_queue as q
        self.q = q

    def tearDown(self):
        os.environ.pop("WALKIN_DRAFT_QUEUE_DIR", None)

    def test_enqueue_and_read(self):
        job = self.q.enqueue_job({"company": "Muster Treuhand AG", "entering_person": "Nico",
                                  "cc": ["tej@automatisierbar.ch"], "notes": "x"})
        self.assertEqual(job["status"], "pending")
        self.assertEqual(job["attempts"], 0)
        self.assertIn("muster-treuhand-ag", job["job_id"])
        self.assertEqual(len(self.q.list_jobs()), 1)
        self.assertEqual(self.q.list_jobs()[0]["entering_person"], "Nico")

    def test_pending_excludes_terminal(self):
        a = self.q.enqueue_job({"company": "A"})
        b = self.q.enqueue_job({"company": "B"})
        self.q.update_job(a["job_id"], status="drafted")
        pend = self.q.pending_jobs()
        self.assertEqual([j["company"] for j in pend], ["B"])

    def test_pending_excludes_attempt_cap(self):
        a = self.q.enqueue_job({"company": "A"})
        self.q.update_job(a["job_id"], attempts=self.q.MAX_ATTEMPTS)
        self.assertEqual(self.q.pending_jobs(), [])

    def test_claim_is_exclusive(self):
        job = self.q.enqueue_job({"company": "A"})
        fd1 = self.q.claim(job["job_id"])
        self.assertIsNotNone(fd1)
        fd2 = self.q.claim(job["job_id"])
        self.assertIsNone(fd2, "second claim must fail while the first is held")
        self.q.release(fd1)
        fd3 = self.q.claim(job["job_id"])
        self.assertIsNotNone(fd3, "claim succeeds again after release")
        self.q.release(fd3)

    def test_update_job(self):
        job = self.q.enqueue_job({"company": "A"})
        self.q.update_job(job["job_id"], status="processing", sector="Treuhand")
        j = self.q.list_jobs()[0]
        self.assertEqual(j["status"], "processing")
        self.assertEqual(j["sector"], "Treuhand")

    def test_stats(self):
        self.q.enqueue_job({"company": "A"})
        b = self.q.enqueue_job({"company": "B"})
        self.q.update_job(b["job_id"], status="failed")
        s = self.q.job_stats()
        self.assertEqual(s["total"], 2)
        self.assertEqual(s["pending"], 1)
        self.assertEqual(s["failed"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
