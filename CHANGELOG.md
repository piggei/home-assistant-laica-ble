# Changelog

## 0.1.0-dev.3 - 2026-09-19

- Replaced the Home Assistant calendar date selector with a text field accepting `DD/MM/YYYY` and `YYYY-MM-DD`.
- Normalize stored birth dates to ISO format.
- Keep automatic Bluetooth discovery as the primary setup path after successful PS7002 validation.
- Added integration-local brand assets under `custom_components/laica_ble/brand/`.
- Removed the repository-maintainer URL note from the public README.
- Direct new-device, protocol, and compatibility research to `piggei/laica-ps7002-ble-research`.
- Keep `*Zone.Identifier` ignored.

## 0.1.0-dev.2 - 2026-09-19

HACS packaging update.

- Added root `hacs.json` so the repository can be added to HACS as a custom integration.
- Added HACS brand icon assets.
- Added HACS installation instructions to the README.
- Added `*Zone.Identifier` to `.gitignore` for Windows/WSL extracted-file metadata.
- Removed generated Python cache files from the distribution.

## 0.1.0-dev.1 - 2026-09-19

Initial Home Assistant custom-integration development build.

- Passive BLE discovery for YoHealth Company ID `0xA102` / header `09 FF`.
- Protocol header, terminator and checksum validation.
- Conservative final-frame policy: entity updates only from status `0x86`.
- Session duplicate suppression for repeated final advertisements.
- Final weight decoding with YoHealth mode precision support.
- Impedance decoding when available.
- Recovered body-composition calculations: BMI, body fat, water, muscle, bone
  mass, visceral fat, body age and BMR.
- One local profile per configured scale: sex branch, date of birth, height.
- Automatic age calculation at weighing time.
- Bluetooth passive processor architecture modeled on current Home Assistant BLE
  integrations.
- Last measurements remain available while the battery scale is sleeping.
- English and Italian UI translations.
