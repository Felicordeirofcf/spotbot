import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "api"))

from signals import build_payload, config_from_query  # noqa: E402
from test_bot import FakeClient  # noqa: E402


class VercelFunctionTests(unittest.TestCase):
    def test_payload(self):
        cfg = config_from_query("")
        d = build_payload(FakeClient(), cfg)
        self.assertEqual(d["analyzed"], 1)
        self.assertEqual(d["signals"][0]["symbol"], "TESTUSDT")
        json.dumps(d)

    def test_query_validation(self):
        self.assertEqual(config_from_query("tp=3&sl=1").take_profit_pct, 3.0)
        with self.assertRaises(ValueError):
            config_from_query("tp=500")

    def test_vercel_json_valid(self):
        cfg = json.loads((ROOT / "vercel.json").read_text())
        self.assertEqual(cfg["regions"], ["gru1"])
        self.assertTrue((ROOT / cfg["functions"].popitem()[0]).exists())


if __name__ == "__main__":
    unittest.main()
