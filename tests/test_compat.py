from pathlib import Path
import configparser
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CompatibilityTests(unittest.TestCase):
    def test_commands_use_legacy_protocol_and_supported_python(self):
        cfg = configparser.ConfigParser()
        cfg.read(ROOT / "overrides/default/commands.conf")
        for name in ("stagecontent", "checkqaccess", "toggleqaccess"):
            self.assertEqual(cfg[name]["chunked"].lower(), "false")
            self.assertEqual(cfg[name]["python.required"], "3.9,3.13")
            self.assertEqual(cfg[name]["generating"].lower(), "true")

    def test_no_vendored_sdk_imports_in_commands(self):
        for path in (ROOT / "overrides/bin").glob("*.py"):
            text = path.read_text()
            self.assertNotIn("from splunklib", text, path.name)
            self.assertNotIn("import splunklib", text, path.name)
            self.assertNotIn("httplib2", text, path.name)
            self.assertNotIn("import ConfigParser", text, path.name)

    def test_no_python2_print_statements(self):
        for path in (ROOT / "overrides/bin").glob("*.py"):
            text = path.read_text()
            self.assertNotIn('print "', text, path.name)
            self.assertNotIn("urllib.url", text, path.name)

    def test_dead_whois_redis_transform_removed(self):
        text = (ROOT / "overrides/default/transforms.conf").read_text()
        self.assertNotIn("whoisLookupRedis", text)
        self.assertIn("python.version = python3", text)

    def test_builder_pins_upstream(self):
        commit = (ROOT / "UPSTREAM_COMMIT").read_text().strip()
        self.assertEqual(commit, "7a694a52faed46160dd4e0cebf76dece149f066e")
        build = (ROOT / "scripts/build.sh").read_text()
        self.assertIn("${UPSTREAM_COMMIT}.tar.gz", build)

    def test_builder_removes_old_sdk(self):
        build = (ROOT / "scripts/build.sh").read_text()
        self.assertIn('rm -rf "$APP/bin/splunklib"', build)

    def test_simplexml_patcher_targets_dashboard_and_form(self):
        text = (ROOT / "scripts/patch_simplexml.py").read_text()
        self.assertIn("dashboard|form", text)
        self.assertIn('version="1.1"', text)

    def test_app_version(self):
        cfg = configparser.ConfigParser()
        cfg.read(ROOT / "overrides/default/app.conf")
        self.assertEqual(cfg["launcher"]["version"], "10.4.2")


if __name__ == "__main__":
    unittest.main()
