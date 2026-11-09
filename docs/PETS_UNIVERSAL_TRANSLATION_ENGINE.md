# PETS Universal Translation & Execution Engine (UTE)

Status: initial format scanner, JSON IR validator and plan-only compatibility switch implemented on the development branch. No binary is executed or translated by this release.

## Design

UTE separates three languages:

1. Human language: the user's request in Spanish or another supported language.
2. Universal Intermediate Representation (IR): a validated, provider-neutral JSON task contract.
3. Platform/runtime interface: a selected native API or sandboxed runtime, only when a verified adapter exists.

The human-language layer describes intent; it does not replace CPU instructions, OS APIs, ABIs, libraries or executable formats.

## QBYTE scanner

`modules/pets/qbyte_format_scanner.py` reads at most 64 KiB from one explicitly supplied regular file. It recognizes PE/COFF, ELF, Mach-O, WebAssembly core modules, ZIP containers and selected source-script signatures/extensions. It records architecture and confidence where the header supports it.

It does not recursively search directories, extract archives, install dependencies, execute code, inspect private devices or claim that a ZIP is an APK without manifest inspection.

## Universal IR

`modules/pets/universal_ir.py` defines a small allowlist of structured operations for file-header inspection, text analysis, audio transcription, text/audio translation, recording summaries and report generation. It validates argument types and size and emits JSON-compatible tasks with `execution_mode=plan_only` and `approval_required=true`.

It intentionally excludes shell execution, arbitrary code, binary payloads, automatic installation, device control and deployment.

## Compatibility switch

`modules/pets/compatibility_switch.py` selects only explicitly registered runtimes whose format, host platform and architecture match and whose descriptor is both verified and sandboxed. Native-loader matches are only candidates; dependencies, ABI, signatures and application permissions still require review.

No execution, installation, emulation or binary rewriting occurs. Unknown or incompatible formats remain blocked with an explicit reason.

## Recommended portable execution layer

WebAssembly with the WASI Component Model is the preferred first portability experiment for new components. WASI 0.3 is the current stable release, while WASI 0.2 remains widely implemented by toolchains. Start with the subset supported by the chosen runtime and add a runtime only after version, sandbox limits, imports, filesystem/network grants and test evidence are recorded.

LLVM is a compiler infrastructure for source/IR lowering and target code generation. It is not a general-purpose translator for arbitrary opaque PE, Mach-O or ELF executables.

## Validation boundaries

- Format recognition is not proof of safe code.
- A compatible host is not proof of satisfied dependencies.
- An IR task is not an executable binary.
- A runtime candidate is not an installed or verified runtime.
- No automatic self-modification or plugin execution.
- All plans remain reviewable and non-executing until a separate, tested sandboxed executor is designed and approved.
