import unittest
from unittest.mock import patch, Mock

from modules import vuln_scanner, ioc_scanner


class ShellFreeScannerTests(unittest.TestCase):
    @patch("modules.vuln_scanner.subprocess.run")
    def test_vulnerability_runner_uses_argv_and_disables_shell(self, run):
        run.return_value = Mock(stdout="ok\n", returncode=0)
        self.assertEqual(vuln_scanner._run(["ufw", "status"]), "ok")
        self.assertEqual(run.call_args.kwargs["shell"], False)
        self.assertEqual(run.call_args.args[0], ["ufw", "status"])

    def test_vulnerability_runner_rejects_command_string(self):
        self.assertEqual(vuln_scanner._run("echo unsafe"), "")

    @patch("modules.ioc_scanner.subprocess.run")
    def test_ioc_runner_uses_argv_and_disables_shell(self, run):
        run.return_value = Mock(stdout="ok\n", returncode=0)
        self.assertEqual(ioc_scanner._run(["iptables", "-L"]), "ok")
        self.assertEqual(run.call_args.kwargs["shell"], False)
        self.assertEqual(run.call_args.args[0], ["iptables", "-L"])

    def test_ioc_runner_rejects_command_string(self):
        self.assertEqual(ioc_scanner._run("echo unsafe"), "")

    def test_process_scan_fails_safely_without_optional_dependency(self):
        import sys
        with patch.dict(sys.modules, {"psutil": None}):
            result = ioc_scanner.check_suspicious_processes()
        self.assertEqual(result["total_flagged"], 0)
        self.assertEqual(result["severity"], 3)
        self.assertIn("warning", result)

    @patch("modules.ioc_scanner._cron_lines", return_value=["# comment", "0 1 * * * /usr/bin/backup"])
    @patch("modules.ioc_scanner.Path")
    def test_cron_scan_does_not_flag_benign_cron_line(self, path_mock, cron_mock):
        # Keep filesystem-dependent persistence checks out of this assertion.
        path_mock.return_value.exists.return_value = False
        path_mock.return_value.is_file.return_value = False
        path_mock.return_value.is_dir.return_value = False
        result = ioc_scanner.check_persistence_mechanisms()
        self.assertEqual(result["total_flagged"], 0)


if __name__ == "__main__":
    unittest.main()
