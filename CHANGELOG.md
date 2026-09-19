# Changelog

## 0.1.0-dev.6

Consolidation release before `0.1.0`.

- Added privacy-preserving Home Assistant diagnostics.
- Added pytest regression tests for protocol, algorithm, final-frame gate and profile date parsing.
- Added GitHub Actions for Ruff, pytest, self-test, compile/JSON checks, hassfest and HACS validation.
- Moved birth-date parsing to a Home Assistant-independent helper module for direct testing.
- Removed measurement/device-compatibility issue forms from this repository and linked those requests to the dedicated research repository.
- No BLE protocol, final-frame policy or YoHealth formula changes.

## 0.1.0-dev.5 - 2026-09-19

- Prioritize Body weight by creating/publishing it before all other measurement entities.
- Reordered body-composition entities into a more natural presentation sequence.
- Mark Impedance as a Home Assistant diagnostic entity while keeping it enabled by default.
- Disable Body age by default; users can enable it from the entity registry if desired.
- No BLE protocol or YoHealth calculation changes.

## 0.1.0-dev.4

- Fixed Home Assistant entity translations to use the current `entity.sensor` schema.
- Renamed the main scale measurement from generic `Weight` to `Body weight` (`Peso corporeo`).
- Bone mass now has its own explicit translated name instead of falling back to the generic weight device-class label.
- Improved body-composition entity labels (`Muscle mass`, etc.).
- No protocol or YoHealth calculation changes.

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
