import unittest

from modules.pets.compatibility_switch import CompatibilitySwitch, RuntimeDescriptor
from modules.pets.platforms import PlatformProfile
from modules.pets.qbyte_format_scanner import scan_bytes
from modules.pets.universal_ir import build_operation


class QByteScannerTests(unittest.TestCase):
    def test_detects_pe_x64(self):
        sample = bytearray(256)
        sample[:2] = b"MZ"
        sample[0x3C:0x40] = (128).to_bytes(4, "little")
        sample[128:132] = b"PE\x00\x00"
        sample[132:134] = (0x8664).to_bytes(2, "little")
        result = scan_bytes(sample, "sample.exe")
        self.assertEqual(result.format_id, "pe_coff")
        self.assertEqual(result.architecture, "x86_64")
        self.assertEqual(result.platform_hint, "windows")

    def test_detects_elf_aarch64(self):
        sample = bytearray(64)
        sample[:4] = b"\x7fELF"
        sample[4] = 2
        sample[5] = 1
        sample[18:20] = (183).to_bytes(2, "little")
        result = scan_bytes(sample, "sample.elf")
        self.assertEqual(result.format_id, "elf")
        self.assertEqual(result.architecture, "aarch64")

    def test_detects_macho_arm64(self):
        sample = b"\xcf\xfa\xed\xfe" + (0x0100000C).to_bytes(4, "little") + b"\x00" * 32
        result = scan_bytes(sample, "sample")
        self.assertEqual(result.format_id, "mach_o")
        self.assertEqual(result.architecture, "aarch64")

    def test_detects_wasm_without_claiming_execution(self):
        result = scan_bytes(b"\x00asm\x01\x00\x00\x00")
        self.assertEqual(result.format_id, "wasm_core_module")
        self.assertTrue(result.inspection_only)

    def test_zip_is_not_assumed_to_be_apk(self):
        result = scan_bytes(b"PK\x03\x04" + b"\x00" * 12, "archive.zip")
        self.assertEqual(result.format_id, "zip_container")
        self.assertEqual(result.platform_hint, "archive")

    def test_unknown_format_stays_unknown(self):
        self.assertEqual(scan_bytes(b"not a binary").format_id, "unknown")


class UniversalIRTests(unittest.TestCase):
    def test_builds_multilingual_audio_operation_as_plan_only(self):
        operation = build_operation(
            operation="transcribe_audio",
            arguments={"asset_ref": "local-upload-001", "language": "es"},
            source_language="es",
            target_language="en",
            target_platforms=("linux", "wasm"),
            request_text="Transcribe this recording and translate it to English",
        )
        payload = operation.to_dict()
        self.assertEqual(payload["schema"], "PETS_UNIVERSAL_IR")
        self.assertEqual(payload["execution_mode"], "plan_only")
        self.assertTrue(payload["approval_required"])

    def test_rejects_unknown_operation(self):
        with self.assertRaises(ValueError):
            build_operation(operation="run_shell", arguments={"command": "echo unsafe"})

    def test_rejects_unknown_arguments(self):
        with self.assertRaises(ValueError):
            build_operation(operation="analyze_text",
                            arguments={"text": "hello", "shell_command": "ignored"})


class CompatibilitySwitchTests(unittest.TestCase):
    def setUp(self):
        self.host = PlatformProfile("linux", "x86_64", "CPython", "3.11", True)

    def test_unverified_runtime_is_never_selected(self):
        switch = CompatibilitySwitch([
            RuntimeDescriptor("wasmtime", ("wasm_core_module",), ("linux",),
                              ("x86_64",), verified=False, sandboxed=True)
        ])
        plan = switch.plan(scan_bytes(b"\x00asm\x01\x00\x00\x00"), self.host)
        self.assertEqual(plan["status"], "blocked_no_verified_route")
        self.assertFalse(plan["execution_performed"])

    def test_verified_sandboxed_runtime_is_selected_as_plan_only(self):
        switch = CompatibilitySwitch([
            RuntimeDescriptor("wasmtime", ("wasm_core_module",), ("linux",),
                              ("x86_64",), verified=True, sandboxed=True)
        ])
        plan = switch.plan(scan_bytes(b"\x00asm\x01\x00\x00\x00"), self.host)
        self.assertEqual(plan["runtime_id"], "wasmtime")
        self.assertEqual(plan["status"], "verified_runtime_candidate")
        self.assertFalse(plan["execution_performed"])

    def test_native_candidate_does_not_execute(self):
        sample = bytearray(256)
        sample[:2] = b"MZ"
        sample[0x3C:0x40] = (128).to_bytes(4, "little")
        sample[128:132] = b"PE\x00\x00"
        sample[132:134] = (0x8664).to_bytes(2, "little")
        plan = CompatibilitySwitch().plan(scan_bytes(sample), self.host)
        self.assertEqual(plan["status"], "blocked_no_verified_route")
        self.assertFalse(plan["execution_performed"])


if __name__ == "__main__":
    unittest.main()
