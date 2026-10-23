"""Tests for the FreeStyle Libre 2 CSV reader."""

import unittest
from pathlib import Path

from readers.libre import read_libre_csv, get_libre_summary


FIXTURE = Path(__file__).parent / "fixtures" / "libre_sample.csv"


class TestLibreReader(unittest.TestCase):
    """Smoke tests for read_libre_csv and get_libre_summary."""

    def test_read_session_structure(self):
        data = read_libre_csv(str(FIXTURE))
        self.assertEqual(data["version"], "1.2")
        self.assertEqual(data["tool"]["id"], "freestyle-libre-2")
        self.assertEqual(data["agent"]["id"], "glucose-monitor")
        self.assertTrue(data["id"].startswith("libre-"))

    def test_read_entries(self):
        data = read_libre_csv(str(FIXTURE))
        entries = data["entries"]
        self.assertEqual(len(entries), 4)
        for entry in entries:
            self.assertEqual(entry["type"], "observation")
            self.assertIn(entry["source"], {"sensor", "user"})
            self.assertIn("timestamp", entry)
            self.assertIn("data", entry)
            self.assertIn("reading_type", entry["data"])
            self.assertIn("source_raw", entry["data"])

    def test_source_mapping(self):
        data = read_libre_csv(str(FIXTURE))
        sources = {e["data"]["source_raw"]: e["source"] for e in data["entries"]}
        self.assertEqual(sources["Sensor"], "sensor")
        self.assertEqual(sources["Manual"], "user")

    def test_status_classification(self):
        data = read_libre_csv(str(FIXTURE))
        statuses = {e["data"]["value"]: e["status"] for e in data["entries"]}
        self.assertEqual(statuses[3.5], "low")
        self.assertEqual(statuses[5.5], "normal")
        self.assertEqual(statuses[6.0], "normal")
        self.assertEqual(statuses[11.2], "high")

    def test_metrics(self):
        data = read_libre_csv(str(FIXTURE))
        metrics = data["metrics"]
        self.assertEqual(metrics["total_readings"], 4)
        self.assertEqual(metrics["avg_glucose"], 6.55)
        self.assertEqual(metrics["min_glucose"], 3.5)
        self.assertEqual(metrics["max_glucose"], 11.2)
        self.assertEqual(metrics["time_in_range"], 50.0)
        self.assertEqual(metrics["hypo_pct"], 25.0)
        self.assertEqual(metrics["hyper_pct"], 25.0)
        self.assertEqual(metrics["days"], 1)
        self.assertEqual(metrics["readings_per_day"], 4.0)

    def test_summary_contains_key_lines(self):
        data = read_libre_csv(str(FIXTURE))
        summary = get_libre_summary(data)
        self.assertIn("FreeStyle Libre 2 Summary", summary)
        self.assertIn("Total readings: 4", summary)
        self.assertIn("Time in Range (3.9-10.0): 50.0%", summary)


if __name__ == "__main__":
    unittest.main()
