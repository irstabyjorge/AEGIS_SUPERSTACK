import unittest
from unittest.mock import patch

from modules import password_audit


class PasswordAuditCommandTests(unittest.TestCase):
    @patch("modules.password_audit.subprocess.run")
    def test_run_args_uses_shell_false_and_preserves_argument_boundaries(self, run):
        run.return_value.stdout = "alice:x:1000:1000::/home/alice:/bin/bash\n"
        result = password_audit._run_args(["getent", "passwd", "alice; touch /tmp/not-run"])

        self.assertIn("alice", result)
        run.assert_called_once()
        args, kwargs = run.call_args
        self.assertEqual(args[0], ["getent", "passwd", "alice; touch /tmp/not-run"])
        self.assertIs(kwargs["shell"], False)

    @patch("modules.password_audit._run_args")
    @patch("modules.password_audit._run")
    def test_password_aging_uses_getent_argument_array(self, run, run_args):
        run.return_value = "alice:x:1000:1000:,,,:/home/alice:$6$hash:20000:99999::::\n"
        run_args.return_value = "alice:x:1000:1000:,,,:/home/alice:/bin/bash"

        result = password_audit.check_password_aging()

        run_args.assert_called_once_with(["getent", "passwd", "alice"])
        self.assertEqual(result["check"], "password_aging")
        self.assertTrue(any(item.get("issue") == "password_never_expires"
                            for item in result["findings"]))


if __name__ == "__main__":
    unittest.main()
