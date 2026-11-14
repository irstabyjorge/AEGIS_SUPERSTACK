import unittest
from unittest.mock import patch

from modules import forensics


class ForensicsCommandTests(unittest.TestCase):
    @patch("modules.forensics.subprocess.run")
    def test_run_args_uses_shell_false(self, run):
        run.return_value.stdout = "/etc/example.conf\n"
        result = forensics._run_args(["find", "/etc", "-type", "f"])

        self.assertEqual(result, "/etc/example.conf")
        args, kwargs = run.call_args
        self.assertEqual(args[0], ["find", "/etc", "-type", "f"])
        self.assertIs(kwargs["shell"], False)

    def test_timeline_rejects_invalid_hours(self):
        for value in (0, -1, 8761, True, "24", 1.5):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    forensics.analyze_recent_file_changes(value)

    @patch("modules.forensics.os.stat")
    @patch("modules.forensics._run_args")
    def test_timeline_uses_argument_array_and_caps_each_directory(self, run_args, stat):
        run_args.return_value = "/etc/a\n/etc/b\n"
        stat.return_value.st_mtime = 1
        stat.return_value.st_size = 12
        stat.return_value.st_uid = 0
        stat.return_value.st_mode = 0o100644

        result = forensics.analyze_recent_file_changes(24)

        self.assertEqual(result["hours_scanned"], 24)
        self.assertEqual(run_args.call_args.args[0][:4], ["find", "/etc", "-type", "f"])
        self.assertEqual(result["total_changed"], 12)


if __name__ == "__main__":
    unittest.main()
