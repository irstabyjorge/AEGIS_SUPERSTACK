"""Normalized audio/transcript contracts; no recording or audio-provider I/O."""
from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Iterable

_LANGUAGE_TAG = re.compile(r"^[A-Za-z]{2,3}(?:-[A-Za-z0-9]{2,8})*$")


def normalize_language_tag(value: str) -> str:
    """Normalize a conservative BCP-47 subset; does not assert provider support."""
    if not isinstance(value, str) or not _LANGUAGE_TAG.fullmatch(value):
        raise ValueError("invalid_language_tag")
    parts = value.replace("_", "-").split("-")
    normalized = [parts[0].lower()]
    for part in parts[1:]:
        if len(part) == 4 and part.isalpha():
            normalized.append(part.title())
        elif (len(part) == 2 and part.isalpha()) or (len(part) == 3 and part.isdigit()):
            normalized.append(part.upper())
        else:
            normalized.append(part.lower())
    return "-".join(normalized)


@dataclass(frozen=True)
class TranscriptSegment:
    start_ms: int
    end_ms: int
    text: str
    speaker_id: str | None = None
    confidence: float | None = None

    def __post_init__(self):
        if not isinstance(self.start_ms, int) or self.start_ms < 0:
            raise ValueError("invalid_segment_start")
        if not isinstance(self.end_ms, int) or self.end_ms <= self.start_ms:
            raise ValueError("invalid_segment_end")
        if not isinstance(self.text, str) or not self.text.strip() or len(self.text) > 10000:
            raise ValueError("invalid_segment_text")
        if self.speaker_id is not None and (
            not isinstance(self.speaker_id, str) or len(self.speaker_id) > 64
        ):
            raise ValueError("invalid_speaker_id")
        if self.confidence is not None and (
            not isinstance(self.confidence, (int, float))
            or not 0.0 <= float(self.confidence) <= 1.0
        ):
            raise ValueError("invalid_segment_confidence")


@dataclass(frozen=True)
class TranscriptionResult:
    asset_ref: str
    source_language: str
    segments: tuple[TranscriptSegment, ...]
    provider_id: str
    model_id: str
    created_at: str
    source_sha256: str | None = None
    diarization_applied: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class TranslationResult:
    asset_ref: str
    source_language: str
    target_language: str
    segments: tuple[TranscriptSegment, ...]
    provider_id: str
    model_id: str
    created_at: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class AudioProviderDescriptor:
    provider_id: str
    tasks: tuple[str, ...]
    language_tags: tuple[str, ...]
    supports_streaming: bool = False
    supports_timestamps: bool = False
    supports_diarization: bool = False
    verified: bool = False


class AudioProviderRegistry:
    """Capability catalog only; it stores no credentials and makes no API calls."""

    def __init__(self):
        self._providers: dict[str, AudioProviderDescriptor] = {}

    def register(self, descriptor: AudioProviderDescriptor) -> None:
        if not descriptor.provider_id or descriptor.provider_id in self._providers:
            raise ValueError("provider_id_must_be_nonempty_and_unique")
        if not descriptor.tasks:
            raise ValueError("provider_must_declare_tasks")
        normalized_languages = tuple(
            normalize_language_tag(tag) for tag in descriptor.language_tags
        )
        normalized = AudioProviderDescriptor(
            provider_id=descriptor.provider_id,
            tasks=tuple(descriptor.tasks),
            language_tags=normalized_languages,
            supports_streaming=descriptor.supports_streaming,
            supports_timestamps=descriptor.supports_timestamps,
            supports_diarization=descriptor.supports_diarization,
            verified=descriptor.verified,
        )
        self._providers[descriptor.provider_id] = normalized

    def eligible(self, *, task: str, language_tag: str,
                 streaming: bool = False, diarization: bool = False) -> tuple[str, ...]:
        language = normalize_language_tag(language_tag)
        matches = []
        for provider in self._providers.values():
            if not provider.verified or task not in provider.tasks:
                continue
            if language not in provider.language_tags:
                continue
            if streaming and not provider.supports_streaming:
                continue
            if diarization and not provider.supports_diarization:
                continue
            matches.append(provider.provider_id)
        return tuple(sorted(matches))


def build_transcription(*, asset_ref: str, source_language: str,
                        segments: Iterable[TranscriptSegment], provider_id: str,
                        model_id: str, created_at: str,
                        source_sha256: str | None = None,
                        diarization_applied: bool = False) -> TranscriptionResult:
    if not isinstance(asset_ref, str) or not asset_ref.strip() or len(asset_ref) > 256:
        raise ValueError("invalid_asset_ref")
    if not isinstance(provider_id, str) or not provider_id.strip():
        raise ValueError("invalid_provider_id")
    if not isinstance(model_id, str) or not model_id.strip():
        raise ValueError("invalid_model_id")
    if not isinstance(created_at, str) or not created_at.strip():
        raise ValueError("invalid_created_at")
    language = normalize_language_tag(source_language)
    normalized_segments = tuple(segments)
    if any(not isinstance(segment, TranscriptSegment) for segment in normalized_segments):
        raise ValueError("segments_must_be_transcript_segments")
    if tuple(sorted(normalized_segments, key=lambda item: item.start_ms)) != normalized_segments:
        raise ValueError("segments_must_be_time_ordered")
    if source_sha256 is not None and not re.fullmatch(r"[0-9a-fA-F]{64}", source_sha256):
        raise ValueError("invalid_source_sha256")
    if not isinstance(diarization_applied, bool):
        raise ValueError("invalid_diarization_flag")
    return TranscriptionResult(
        asset_ref=asset_ref, source_language=language,
        segments=normalized_segments, provider_id=provider_id,
        model_id=model_id, created_at=created_at,
        source_sha256=source_sha256, diarization_applied=diarization_applied,
    )


def build_translation(*, asset_ref: str, source_language: str,
                      target_language: str, segments: Iterable[TranscriptSegment],
                      provider_id: str, model_id: str,
                      created_at: str) -> TranslationResult:
    source = normalize_language_tag(source_language)
    target = normalize_language_tag(target_language)
    if source == target:
        raise ValueError("source_and_target_languages_must_differ")
    result = build_transcription(
        asset_ref=asset_ref, source_language=source, segments=segments,
        provider_id=provider_id, model_id=model_id, created_at=created_at,
    )
    return TranslationResult(
        asset_ref=result.asset_ref, source_language=source,
        target_language=target, segments=result.segments,
        provider_id=result.provider_id, model_id=result.model_id,
        created_at=result.created_at,
    )
