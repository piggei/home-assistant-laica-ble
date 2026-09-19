# Changelog

## 0.1.0 - 2026-09-20

First stable release, promoted without runtime changes from the validated
`0.1.0-dev.10` baseline.

Validated on a real **LAICA PS7002** with a clean Home Assistant installation:

- automatic Bluetooth discovery from YoHealth Company ID `0xA102` / prefix `09 FF`;
- first-session weight-only discovery and measurement from stable `0x82` when
  electrode contact is unavailable;
- later full `0x86` measurement correctly adds/updates BIA-derived entities;
- complete barefoot measurement path with weight, impedance and recovered
  YoHealth body-composition metrics;
- profile configuration and profile editing;
- Body age disabled by default;
- removal and Bluetooth rediscovery of the same scale;
- no duplicate physical scale device after a clean remove/reinstall cycle.

Release preparation changes are metadata/documentation only: manifest version,
release wording, issue-template version, changelog, and packaging cleanup. The
Python runtime implementation is unchanged from `0.1.0-dev.10`.

## 0.1.0-dev.10 - 2026-09-20

Lifecycle hardening based on clean remove/reinstall testing of `0.1.0-dev.9`.

- Trigger Bluetooth rediscovery of the configured scale address when a LAICA BLE
  config entry is removed, following the current Home Assistant Bluetooth API
  guidance.
- Keep measurement parsing, session handling, entities, profile logic and the
  recovered YoHealth formulas unchanged from `0.1.0-dev.9`.
- Add a static regression test proving that Body age remains disabled by default.
- Document the difference between the HACS repository-management device and the
  physical LAICA scale device, plus the effect of an ignored discovery entry.
- Correct the README protocol summary for `0x80` / `0x82` / `0x86` states and
  remove the ambiguous claim about HACS installing an unpublished default branch.

## 0.1.0-dev.9 - 2026-09-20

Discovery hardening based on the validated `0.1.0-dev.8` baseline.

- Automatic and manual discovery now identify YoHealth devices from Company ID
  `0xA102` plus the public `09 FF` header only.
- Measurement parsing remains unchanged and still requires the complete payload,
  terminator, and valid checksum before any measurement is accepted.
- Added regression tests proving that discovery can accept an identifying partial
  advertisement while the measurement parser rejects it as incomplete.
- No changes to session handling, `0x80`/`0x82`/`0x86` behavior, entities, profile
  handling, or recovered YoHealth body-composition formulas.

## 0.1.0-dev.8 - 2026-09-19

Weight-only measurement support based on direct PS7002 footwear testing.

- Accept stable status `0x82` as a weight-only measurement after a 2.5 second hold-off.
- Give complete `0x86` measurements priority and cancel a pending `0x82` candidate.
- Keep `0x80` as an in-progress state that never updates entities.
- Suppress repeated `0x82` advertisements so one weighing produces one weight-only update.
- Never calculate or overwrite BIA-derived metrics from a `0x82` measurement.
- Added regression tests for `0x82` hold/cancel/re-arm session behavior.
- Extended privacy-safe diagnostics with stable-weight counters and policy metadata.
- No changes to the recovered YoHealth calculation formulas.

## 0.1.0-dev.7 - 2026-09-19

CI/quality cleanup release following the first full validation run.

- Fixed Ruff import ordering and removed unused imports.
- Updated `Mapping` to import from `collections.abc`.
- Fixed the remaining Ruff line-length violation.
- Reordered `manifest.json` keys to satisfy Home Assistant `hassfest`.
- No BLE protocol, entity behavior, final-frame policy, profile handling, or YoHealth formula changes.

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
