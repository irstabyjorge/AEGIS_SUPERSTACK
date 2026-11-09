# PETS–AEGIS Device Identity Integration

## GitHub source
This module lives at `modules/device_identity/` in `irstabyjorge/AEGIS_SUPERSTACK`.

## Android / Termux
From the repository root:

```bash
pkg update
pkg install python git
python modules/device_identity/main.py list
python modules/device_identity/main.py report --format json --output reports/device_inventory.json
python -m unittest discover -s modules/device_identity/tests -v
```

If the repository is already cloned, do not clone it again. Pull the latest `main` branch before running.

## Hugging Face Space
A read-only Gradio Space scaffold is in `modules/device_identity/huggingface/`.

To publish it, create a new Gradio Space under an account or organization you control, then upload the *contents* of that folder to the Space repository root. The scaffold contains only historical device model names and classification labels. Do not make a public Space with private evidence or personal identifiers.

The connected Hugging Face session currently has read-only repository scopes; it cannot create or push a Space. Publication must be completed by an account administrator after granting appropriate write access or through the Hugging Face website.

## Data classification
All eight seeded entries are `HISTORICAL`, with `verified: false`. This records prior conversation mentions only. It does not prove ownership, current possession, unique hardware identity, or impersonation.
