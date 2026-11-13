# PETS/AEGIS cross-platform architecture

Status: architecture and portable runtime profile implemented on the development branch. Native bridges remain separate deliverables and are not claimed to be installed or tested merely because a target appears in the matrix.

## Shared core

The Python core owns domain logic: evidence provenance, policy evaluation, report generation, schemas, and provider-neutral interfaces. It must not depend on a desktop UI, device-specific SDK, privileged OS APIs, or a particular CPU.

## Target matrix

| Target | Intended integration | Current status |
|---|---|---|
| Linux desktop/server | Python service/CLI; systemd package later | Runtime profile and adapter contract only |
| Windows | Python service/CLI; signed installer later | Adapter contract only |
| macOS | Python service/CLI; signed app wrapper later | Adapter contract only |
| Android phones/tablets | Termux/local bridge or native Android wrapper | Existing bridge source; build/install not verified |
| iPhone/iPad | Native Swift/SwiftUI wrapper using a narrow local API | Not implemented |
| ARM single-board computers | Linux ARM64/ARMv7 runtime | Targeted, not board-tested |
| RISC-V boards | Linux RISC-V runtime where Python dependencies exist | Targeted, not board-tested |
| IoT/embedded | Explicit gateway integration using documented MQTT/HTTPS interfaces | Not implemented; no device discovery or control by default |
| Motherboards/firmware | Host OS management interfaces only, where vendor-supported | No direct firmware flashing or hardware-level access |

## Hardware abstraction

The core consumes normalized, user-approved records and capabilities. A platform adapter translates supported host APIs into those records. An IoT gateway should use allowlisted broker endpoints, topic allowlists, TLS, scoped credentials, rate limits, and read-only telemetry subscriptions by default. Actuation is a separate opt-in capability and is not part of this baseline.

Motherboards are not a single application platform. PETS runs on the host OS installed on a computer or board; it does not execute directly on a motherboard. Firmware/UEFI management requires vendor-specific tooling and explicit physical authorization and is excluded from the generic adapter.

## Apple distinction

macOS can run the Python core. iOS/iPadOS generally require a native Swift application because background execution, filesystem access, signing, and sandbox rules differ. The Apple bridge should communicate with the core through a documented, authenticated local API or an explicitly selected file exchange. It must not bypass Apple sandbox or permission controls.

## Security invariants

- No automatic device enumeration, scanning, pairing, or control.
- No hidden persistence, stealth collection, radio interception, or jamming.
- Explicit operator selection and OS permission for each data source.
- Read-only by default; write/actuation interfaces are separate and disabled.
- No credentials in source, manifests, logs, or evidence payloads.
- Keep personal data local unless the operator explicitly approves export.
- Every adapter declares supported platforms, capabilities, provenance, and tests.

## Validation status

modules/pets/platforms.py detects the current runtime and provides an explicit adapter registry. Unit tests cover the profile and registry. This is not proof of compatibility on every OS, CPU, board, or IoT device. CI matrix execution and native-device tests must pass before a target can be marked validated.
