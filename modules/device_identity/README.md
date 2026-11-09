# PETS–AEGIS Device Identity Registry

A privacy-first, defensive inventory for devices explicitly associated with the project owner.

## Scope and safety

- Imports only historical device model references documented in prior project conversations.
- Keeps historical records distinct from user-confirmed records.
- Does not scan networks, enumerate nearby devices, collect MAC/IMEI/serial numbers, track people, or identify anonymous users.
- Does not accept CURP, RFC, government-ID images, passwords, recovery codes, or biometric data.
- Evidence hashing is local and read-only; SHA-256 establishes file integrity, not authorship or ownership.

## Classification

- `HISTORICAL`: device model mentioned in prior conversation; not independently verified.
- `USER_CONFIRMED`: the user confirms the device through its own settings or physical possession.
- `INDEPENDENTLY_VERIFIED`: requires separate reliable evidence and a documented verification method.

## Historical seed inventory

Eight models are included from prior conversation records. No unique hardware identifiers or dates are inferred.

## Run on Android / Termux or desktop Python

Requires Python 3.9+ and uses only the standard library.

```bash
python main.py list
python main.py report --format json
python main.py report --format html --output reports/device_inventory.html
python main.py hash-evidence /path/to/a/copied/evidence-file
```

The module does not modify evidence files. Reports are generated locally. Keep reports private because later user-confirmed entries may contain sensitive device context.

## Integrating into AEGIS

Import with:

```python
from modules.device_identity import load_registry, build_report
```

This module is standalone and does not activate background services or network collection.
