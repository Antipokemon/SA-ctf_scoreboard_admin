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

    def test_admin_app_owns_questions_answers_and_hints(self):
        collections = (ROOT / "overrides/default/collections.conf").read_text()
        transforms = (ROOT / "overrides/default/transforms.conf").read_text()
        for name in ("ctf_questions", "ctf_answers", "ctf_hints"):
            self.assertIn(f"[{name}]", collections)
            self.assertIn(f"[{name}]", transforms)

    def test_imported_content_fields_are_exposed_by_lookups(self):
        collections = (ROOT / "overrides/default/collections.conf").read_text()
        transforms = (ROOT / "overrides/default/transforms.conf").read_text()

        for field in (
            "Subject",
            "Category",
            "ChallengeID",
            "PrimarySourcetype",
            "LearningObjective",
            "ReferenceSPL",
        ):
            self.assertIn(f"field.{field} = string", collections)
            self.assertIn(field, transforms)

        self.assertIn("field.AnswerType = string", collections)
        self.assertIn("fields_list = ctf_id, Number, Answer, AnswerType", transforms)

    def test_questions_are_exported_for_participant_read_access(self):
        meta = (ROOT / "metadata/default.meta").read_text()
        self.assertIn("[collections/ctf_questions]", meta)
        self.assertIn("ctf_competitor", meta)
        self.assertIn("[transforms/ctf_questions]", meta)
        self.assertIn("export = system", meta)

    def test_builder_merges_question_metadata(self):
        build = (ROOT / "scripts/build.sh").read_text()
        self.assertIn('cat "$ROOT/metadata/default.meta" >> "$APP/metadata/default.meta"', build)

    def test_app_version(self):
        cfg = configparser.ConfigParser()
        cfg.read(ROOT / "overrides/default/app.conf")
        self.assertRegex(cfg["launcher"]["version"], r"^10\.4\.\d+$")


if __name__ == "__main__":
    unittest.main()
