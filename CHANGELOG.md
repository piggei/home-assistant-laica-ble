# Changelog

## 0.1.1-build2 - 2026-09-20

Internal discovery diagnostic build; not intended as a public HACS release.

- Fixed custom-integration runtime localization by using only
  `translations/en.json` and `translations/it.json`; removed Core-only
  `strings.json`.
- Added translated field descriptions to the manual scan confirmation control.
- Manual discovery now keeps Home Assistant scanners in ACTIVE mode for the full
  15-second wait window.
- During that window every non-connectable BLE advertisement is logged at DEBUG.
- YoHealth-like advertisements are also logged at INFO, together with a final scan
  summary, so useful diagnostics are available with the normal Home Assistant log
  level.
- Discovery logs remain privacy-reduced: only name/address, company IDs, payload
  lengths and the first two payload bytes are reported. Weight/impedance payload
  contents and profile data are not logged.
- No changes to measurement parsing, `0x80`/`0x82`/`0x86` handling, entities, or
  recovered YoHealth formulas.

## 0.1.1-build1 - 2026-09-19

Internal discovery diagnostic build; not intended as a public HACS release.

- Split setup discovery matching from strict measurement validation: configuration
  now identifies a YoHealth scale from Company ID `0xA102` plus header `09 FF`,
  while runtime measurement frames still require full length, terminator and
  checksum validation.
- This avoids aborting Bluetooth discovery when the first advertisement seen while
  the scale wakes is transient or incomplete.
- Reworked the manual setup fallback into an explicit user-visible search action.
- Manual search performs Home Assistant's one-shot scan, checks the shared cache,
  and then waits up to 15 seconds for a live compatible advertisement.
- Added privacy-reduced DEBUG discovery logging (device name/address, company ID,
  payload length and two-byte prefix only; no weight/impedance payload bytes).
- Added regression tests proving that transient YoHealth advertisements are valid
  for discovery but are still rejected as measurements.
- No changes to measurement state handling or recovered YoHealth formulas.

## 0.1.1 - 2026-09-19

Discovery/reinstallation reliability release.

- Added `async_remove_entry()` Bluetooth rediscovery so a removed scale becomes
  eligible for setup again without requiring a Home Assistant restart.
- Reworked manual setup so **Add integration -> LAICA BLE** first checks the
  Bluetooth cache and, when empty, offers a retryable scan step instead of
  aborting with `no_devices_found`.
- The retry step requests Home Assistant's official one-shot active scan and then
  rechecks compatible non-connectable YoHealth advertisements.
- Added English and Italian UI text for the scan/retry flow.
- Updated HACS/manual installation, fresh-install, removal/reinstallation and
  troubleshooting documentation.
- Updated release references and issue-template version to `0.1.1`.
- No changes to YoHealth packet parsing, `0x80`/`0x82`/`0x86` measurement policy,
  entity calculations, or recovered body-composition formulas.

## 0.1.0 - 2026-09-19

First stable release of the LAICA BLE Home Assistant integration.

- Promoted the validated `0.1.0-dev.8` behavior to stable without changing the BLE parser or recovered YoHealth formulas.
- Supports automatic passive BLE discovery of validated YoHealth advertisements.
- Supports complete `0x86` body-composition measurements and deferred `0x82` weight-only measurements.
- Keeps body-composition values unchanged when a weighing has no usable impedance.
- Includes editable local profile data, English/Italian translations, privacy-safe diagnostics, and HACS/manual installation.
- Documents the one-person-per-scale-entry limitation and the distinction between Home Assistant integration issues and scale/protocol research.
- Final documentation audit updated installation instructions, protocol-state documentation, support links, and release references.
- CI baseline: pytest, Ruff, Python compilation, JSON validation, Home Assistant `hassfest`, and HACS validation.

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

## 0.1.0-dev.6 - 2026-09-19

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

## 0.1.0-dev.4 - 2026-09-19

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
