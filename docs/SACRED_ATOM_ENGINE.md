# Sacred Atom Engine — PETS/AEGIS

## Meaning and boundary

The Sacred Atom is implemented as an engineering and knowledge-organization metaphor: a human-defined center (purpose, policy and consent) with multidirectional layers for knowledge, reasoning, validation, approved execution and presentation. It does not establish subjective experience, self-awareness or independent consciousness in software.

## Implemented engine

- Validated directed acyclic geometry with a required center node.
- Explicit component allowlist and dependency resolution for an assembly plan.
- Assembly planning does not import, execute, install or download component code.
- UI-neutral GUI state model for desktop, web and native mobile wrappers.
- Compute backend contract, deterministic CPU backend, and optional injected GPU backend with automatic CPU fallback when the GPU backend fails.
- Safe baseline capabilities are limited to read, analyze and report. Privileged actions require separate policy and approval layers.

## GPU integration

The engine does not assume a GPU vendor or silently install drivers. A platform-specific backend can be supplied only after its runtime is installed and validated. If absent or failing, the CPU backend remains available. GPU presence is not inferred from a machine name or advertised as verified without a backend health check.

## GUI integration

`SacredAtomGUIState` is a presentation model, not a finished graphical application. Qt, web, SwiftUI and Android front ends can render the same status object while retaining their platform permission and sandbox rules.

## Safety and provenance

No self-modifying code, arbitrary plugin execution, automatic firmware changes, hidden device discovery, or unapproved external actions. Every component must be registered, trusted, versioned and dependency-checked before an assembly plan is emitted.

## Validation

Unit tests cover geometry, allowlisting, dependency order, CPU fallback and invalid compute operations. Passing tests do not imply GPU hardware acceleration or native GUI availability on a target device.
