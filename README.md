# LAICA BLE for Home Assistant

Local Bluetooth integration for LAICA smart body-composition scales using the
**YoHealth** advertising protocol.

Current release: **0.1.0**

The integration has been developed and directly validated with a **LAICA
PS7002**. Compatibility with other LAICA/YoHealth models must be confirmed model
by model; see [Device compatibility and protocol research](#device-compatibility-and-protocol-research).

## Features

The scale broadcasts measurements as non-connectable BLE advertisements. Home
Assistant receives them locally; no cloud account, GATT connection, pairing, or
LAICA app is required for normal operation.

LAICA BLE:

1. discovers compatible YoHealth advertisements;
2. validates the protocol header, terminator and checksum;
3. handles `0x80` as measurement-in-progress, deferred `0x82` as stable
   weight-only, and `0x86` as the complete/final measurement;
4. decodes weight and, when available, impedance;
5. calculates the recovered YoHealth body-composition fields locally from the
   configured profile;
6. retains the last measurement while the scale is sleeping/offline.

### Entities

| Sensor | Source | Default presentation |
|---|---|---|
| Body weight | BLE frame | enabled |
| BMI | recovered YoHealth algorithm | enabled |
| Body fat | recovered YoHealth algorithm | enabled |
| Body water | recovered YoHealth algorithm | enabled |
| Muscle mass | recovered YoHealth algorithm | enabled |
| Bone mass | recovered YoHealth algorithm | enabled |
| Visceral fat | recovered YoHealth algorithm | enabled |
| Basal metabolic rate | recovered YoHealth algorithm | enabled |
| Body age | recovered YoHealth algorithm | disabled by default |
| Impedance | BLE frame | enabled, diagnostic entity |

Body-composition entities are created after the first complete `0x86` frame with
a usable impedance value. A stable `0x82` measurement is accepted as
**weight-only** after a short hold-off. Likewise, if a final `0x86` frame has no
usable impedance, only the weight is updated. Previous body-composition values
are retained rather than being recalculated from an incomplete measurement.

Home Assistant controls the final ordering of entities on the device page. The
integration creates Body weight first, but the frontend may still display it in
a different position.

## Important limitation: one person per scale entry

The scale does **not** transmit the identity of the person/profile. Person
selection exists in the companion app, not in the scale BLE protocol.

For that reason, each configured LAICA BLE scale has one local calculation
profile:

- sex branch used by the historical LAICA/YoHealth algorithm;
- date of birth;
- height.

Weight itself is valid for anybody using the scale, but calculated body
composition belongs to the configured profile only.

The profile values remain in the local Home Assistant config entry and are not
sent anywhere by this integration.

## Measurement-state policy

Direct PS7002 captures show:

- `0x80`: measurement in progress;
- `0x82`: stable weight;
- `0x86`: complete/final body-composition result.

Real-world testing with footwear confirmed that a valid stable weight can stop
at `0x82` when electrode contact is unavailable.

The integration therefore holds the first stable `0x82` candidate for **2.5
seconds**. If `0x86` arrives during that window, the pending `0x82` is cancelled
and only the complete measurement is published. If no `0x86` arrives, the
stable `0x82` weight is published once as a weight-only measurement. `0x80`
never updates entities and re-arms the next weighing session.

Body-composition entities are never recalculated from `0x82`; they retain their
last valid `0x86` values.

## Requirements

- Home Assistant with Bluetooth support, or a working Bluetooth proxy;
- the scale within BLE reception range of Home Assistant/a proxy;
- for HACS installation, HACS already installed in Home Assistant. If needed, see
  the official HACS documentation at https://hacs.xyz/.

The integration is passive and does not connect to the scale.

## Installation

### HACS custom repository (recommended)

This project is distributed as a **HACS custom integration repository**. It does
not need to be present in the default HACS catalog.

Repository URL:

```text
https://github.com/piggei/home-assistant-laica-ble
```

Installation procedure:

1. Open **HACS** in Home Assistant and enter **Integrations**.
2. Open the menu in the upper-right corner and choose **Custom repositories**.
3. Add `https://github.com/piggei/home-assistant-laica-ble` and select
   **Integration** as the category.
4. Open **LAICA BLE** in HACS and choose **Download**.
5. Select the latest stable release and complete the installation.
6. Restart Home Assistant when requested.
7. Start a weighing so the scale begins advertising over BLE.
8. Open **Settings -> Devices & services**. Home Assistant should show the
   discovered **LAICA BLE** scale.
9. Open the discovery card and enter the local profile values and the scale
   model.

No YAML configuration is required.

Project releases are published at:

https://github.com/piggei/home-assistant-laica-ble/releases

### Manual installation

1. Download the desired release archive from the repository Releases page.
2. Copy the directory `custom_components/laica_ble` into the Home Assistant
   configuration directory so the final path is:

   ```text
   /config/custom_components/laica_ble
   ```

3. Restart Home Assistant.
4. Make sure Home Assistant has a working Bluetooth adapter or Bluetooth proxy.
5. Start a weighing so the scale begins advertising.
6. Open **Settings -> Devices & services** and configure the automatically
   discovered **LAICA BLE** device.

If the device is not shown automatically, keep the scale awake/advertising and
use **Add integration -> LAICA BLE** to select a currently advertising compatible
scale.

## Configuration and profile changes

Use **Settings -> Devices & services -> LAICA BLE -> Configure** to update the
profile without removing the integration.

You can change:

- sex branch;
- date of birth;
- height;
- scale model.

The date of birth accepts `DD/MM/YYYY` or `YYYY-MM-DD` and is stored internally
in ISO format. The integration reloads automatically. Age is recalculated from
the date of birth at measurement time.

## Protocol at a glance

Home Assistant/Bleak exposes Company ID `0xA102` separately from the 12-byte
payload:

```text
09 FF WW WW ZZ ZZ SS FF FF MM CC AA
```

- `WW WW`: weight raw, big-endian;
- `ZZ ZZ`: health/impedance raw, big-endian (`FFFF` = unavailable);
- `SS`: status (`80` = in progress, `82` = stable weight, `86` = complete);
- `MM`: mode/precision (`21` on the validated PS7002);
- `CC`: checksum;
- `AA`: terminator.

See [docs/PROTOCOL.md](docs/PROTOCOL.md) for the BLE framing and
[docs/ALGORITHM.md](docs/ALGORITHM.md) for the recovered body-composition
calculation.

## Compatibility

| Model | Protocol evidence | Algorithm evidence | Status |
|---|---|---|---|
| LAICA PS7002 | direct captures | direct comparison with app | **validated** |
| LAICA PS7200L | historical YoHealth evidence | historical implementation source | strong evidence; new Home Assistant validation wanted |
| Other LAICA/YoHealth models | unknown | unknown | reports wanted |

The PS7002 is the only model directly validated with this Home Assistant
integration at release `0.1.0`. Do not assume compatibility solely from the LAICA
brand or product appearance.

## Support and issue routing

For **Home Assistant integration problems**—installation, discovery after a
known-compatible advertisement, entity behavior, configuration, diagnostics, or
integration exceptions—open an issue here:

https://github.com/piggei/home-assistant-laica-ble/issues

For **scale/protocol research**—support for a new LAICA model, BLE captures,
unknown packet formats/status values, compatibility reports, or validation of
body-composition results—use the dedicated technical repository:

https://github.com/piggei/laica-ps7002-ble-research

This separation keeps Home Assistant software bugs distinct from reverse-
engineering and hardware-compatibility work.

## Diagnostics

Home Assistant diagnostics are available from the LAICA BLE integration/device
menu. The exported diagnostics intentionally redact the Bluetooth address and
profile fields (birth date, height and sex branch), and do not include weight,
impedance values, or raw BLE payloads. They contain only protocol state useful
for debugging.

## Debug logging

For troubleshooting, temporarily add:

```yaml
logger:
  logs:
    custom_components.laica_ble: debug
```

The integration logs accepted measurement metadata, not the configured date of
birth or other profile details.

## Validation

The repository includes regression tests for:

- YoHealth frame parsing and checksum validation;
- complete `0x86` measurements;
- deferred `0x82` weight-only measurements and cancellation by `0x86`;
- duplicate/session handling;
- profile date parsing and age rollover;
- recovered YoHealth body-composition calculations.

GitHub Actions run Ruff, pytest, the standalone self-test, Python compilation,
JSON validation, Home Assistant `hassfest`, and HACS repository validation on
pushes and pull requests.

The final `0.1.0` release preserves the validated BLE protocol behavior and
recovered YoHealth formulas used during development.

## Safety / interpretation

Body-composition values from consumer BIA scales are estimates. This project
reproduces the historical vendor algorithm for interoperability and research; it
is not intended for diagnosis or medical decision-making.

## License and provenance

Project code and original documentation are released under the **MIT License**.
No proprietary LAICA/YoHealth library, APK, firmware, or decompiled proprietary
source is distributed in this repository. See [NOTICE.md](NOTICE.md).

This is an independent interoperability project and is not affiliated with or
endorsed by LAICA.
