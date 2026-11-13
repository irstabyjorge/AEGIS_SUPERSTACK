# PETS Audio and Language Contracts

Status: normalized metadata and provider-capability contracts implemented; no audio provider is connected and no recording is stored or transmitted by this module.

## Goals

- Carry the user's requested language and detected source language explicitly.
- Preserve transcript segment timestamps and optional speaker labels.
- Keep original audio as a caller-managed asset reference rather than copying audio into the evidence ledger.
- Treat provider language coverage as an explicit capability declaration, not a universal assumption.
- Keep transcription, translation and summarization as distinct operations.

## Contracts

`modules/pets/audio_contracts.py` provides:
- A conservative BCP-47-style language-tag normalizer.
- Transcript segments with millisecond offsets, optional speaker IDs and confidence.
- Transcription and translation result structures.
- An explicit audio-provider capability registry.

A provider is selectable only when its descriptor is marked verified and declares the exact task, language tag and requested features (streaming/diarization). No credentials, audio upload, API calls, voice cloning or audio playback are implemented.

## Recommended processing path

1. User explicitly supplies an audio/video asset.
2. Record a local opaque asset reference and optional SHA-256 digest.
3. Select a verified provider for the requested task and language.
4. Preserve original transcript segments and timestamps.
5. Store translation as a separate output; never overwrite the source transcript.
6. Record provider/model identifiers and timestamps in the provenance ledger.
7. Ask before sharing or transmitting any recording or transcript.

## Provider notes

OpenAI's current audio documentation distinguishes file transcription, low-latency streaming transcription and Realtime translation. These are separate capabilities and should be represented separately in provider descriptors. Model language coverage and quality vary; a language tag being syntactically valid does not mean every model supports it equally well.
