import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import eventlog


class EventLogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "events.jsonl"
        self.log = eventlog.EventLog(self.path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_emit(self):
        event = self.log.emit("login", "victor", ip="127.0.0.1")
        self.assertEqual(event["type"], "login")
        self.assertEqual(event["ip"], "127.0.0.1")
        self.assertEqual(list(self.log.query()), [event])

    def test_query_empty(self):
        self.assertEqual(list(self.log.query()), [])

    def test_filters(self):
        self.log.emit("login", "victor")
        self.log.emit("logout", "victor")
        self.log.emit("login", "alice")
        self.assertEqual(len(list(self.log.query(event_type="login"))), 2)
        self.assertEqual(len(list(self.log.query(actor="alice"))), 1)

    def test_malformed_line_skipped(self):
        self.log.emit("login", "victor")
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write("not json\n")
        self.assertEqual(len(list(self.log.query())), 1)

    def test_stats(self):
        self.log.emit("login", "a")
        self.log.emit("login", "b")
        stats = self.log.stats()
        self.assertEqual(stats["total"], 2)
        self.assertEqual(stats["by_type"], {"login": 2})

    def test_rotate(self):
        self.log.emit("login", "a")
        archived = self.log.rotate(keep=3)
        self.assertTrue(archived)
        self.assertFalse(self.path.exists())

    def test_rotate_keep_validation(self):
        with self.assertRaises(ValueError):
            self.log.rotate(keep=0)

    def test_cli(self):
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = eventlog.main(["--path", str(self.path), "emit", "login", "victor"])
            stats_code = eventlog.main(["--path", str(self.path), "stats"])
        self.assertEqual(code, 0)
        self.assertEqual(stats_code, 0)
        self.assertIn('"total": 1', buf.getvalue())


if __name__ == "__main__":
    unittest.main()
