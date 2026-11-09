import unittest

from modules.pets.audio_contracts import (
    AudioProviderDescriptor,
    AudioProviderRegistry,
    TranscriptSegment,
    build_transcription,
    build_translation,
    normalize_language_tag,
)


class AudioLanguageContractTests(unittest.TestCase):
    def test_normalizes_bcp47_style_tags(self):
        self.assertEqual(normalize_language_tag("es-mx"), "es-MX")
        self.assertEqual(normalize_language_tag("zh-hans-cn"), "zh-Hans-CN")

    def test_rejects_invalid_language_tag(self):
        with self.assertRaises(ValueError):
            normalize_language_tag("not a language")

    def test_transcription_preserves_timestamps_and_speakers(self):
        segments = (
            TranscriptSegment(0, 1200, "Buenos días", "speaker-1", 0.97),
            TranscriptSegment(1300, 2400, "¿Cómo estás?", "speaker-2", 0.94),
        )
        result = build_transcription(
            asset_ref="upload-token-1", source_language="es-MX",
            segments=segments, provider_id="provider-fixture",
            model_id="model-fixture", created_at="2026-11-09T12:00:00Z",
            source_sha256="a" * 64, diarization_applied=True,
        )
        self.assertEqual(result.source_language, "es-MX")
        self.assertEqual(result.segments[1].start_ms, 1300)
        self.assertEqual(result.segments[1].speaker_id, "speaker-2")

    def test_translation_requires_different_languages(self):
        segment = TranscriptSegment(0, 1000, "Hello")
        with self.assertRaises(ValueError):
            build_translation(
                asset_ref="asset", source_language="en", target_language="en",
                segments=(segment,), provider_id="fixture",
                model_id="fixture", created_at="2026-11-09T12:00:00Z",
            )

    def test_provider_must_be_verified_and_exact_language_supported(self):
        registry = AudioProviderRegistry()
        registry.register(AudioProviderDescriptor(
            "unverified", ("transcribe",), ("es",), verified=False
        ))
        registry.register(AudioProviderDescriptor(
            "verified-es", ("transcribe",), ("es",), verified=True,
            supports_streaming=True, supports_timestamps=True,
        ))
        self.assertEqual(
            registry.eligible(task="transcribe", language_tag="es",
                               streaming=True),
            ("verified-es",),
        )
        self.assertEqual(
            registry.eligible(task="transcribe", language_tag="es-MX"),
            (),
        )


if __name__ == "__main__":
    unittest.main()
