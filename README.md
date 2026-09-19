# LAICA BLE for Home Assistant

Local Bluetooth integration for LAICA smart body-composition scales using the
**YoHealth** advertising protocol.

Current internal validation build: **0.1.1-build3**  
Latest public stable release: **0.1.1**  
Planned next public release after validation: **0.1.2**

> `0.1.1-build3` is intentionally an internal test build. Do not publish it as a
> GitHub/HACS release. For validation, copy the integration manually into Home
> Assistant. This avoids HACS version metadata becoming part of the discovery
> test.

The integration has been developed and directly validated with a **LAICA
PS7002**. Compatibility with other LAICA/YoHealth models must be confirmed model
by model.

## Features

The scale broadcasts measurements over BLE. Home Assistant receives them
locally; no cloud account, pairing, GATT connection, or LAICA app is required
for normal operation.

LAICA BLE:

1. discovers compatible YoHealth advertisements;
2. validates measurement framing, terminator and checksum;
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
usable impedance. A stable `0x82` measurement is accepted as **weight-only**
after a short hold-off. Likewise, if a final `0x86` frame has no usable
impedance, only body weight is updated. Previous body-composition values are not
recalculated from an incomplete measurement.

Home Assistant controls the final ordering of entities on the device page. The
integration creates Body weight first, but the frontend may display it elsewhere.

## Important limitation: one person per scale entry

The scale does **not** transmit the identity of the person/profile. Person
selection exists in the companion app, not in the BLE measurement protocol.

Each configured scale therefore has one local calculation profile containing:

- sex branch used by the historical LAICA/YoHealth algorithm;
- date of birth;
- height.

Weight itself is valid for anybody using the scale, but calculated body
composition belongs to the configured profile only. These values remain local to
Home Assistant.

## Measurement-state policy

Direct PS7002 captures and real-world tests show:

- `0x80`: measurement in progress;
- `0x82`: stable weight;
- `0x86`: complete/final body-composition result.

The integration holds the first stable `0x82` candidate for **2.5 seconds**. If
`0x86` arrives during that window, the pending `0x82` is cancelled and only the
complete measurement is published. If no `0x86` arrives, the stable weight is
published once as a weight-only measurement. `0x80` never updates entities and
re-arms the next weighing session.

This behavior has been directly tested both barefoot and while wearing slippers.

## Requirements

- Home Assistant with Bluetooth support, or a working Bluetooth proxy;
- the scale within BLE reception range of Home Assistant/a proxy;
- HACS only if using the normal stable-release installation path.

The integration is passive and does not connect to the scale.

## Stable installation with HACS

The public repository can be installed as a HACS custom integration:

```text
https://github.com/piggei/home-assistant-laica-ble
```

1. Open **HACS -> Integrations**.
2. Open the upper-right menu and choose **Custom repositories**.
3. Add the repository URL above and select **Integration**.
4. Open **LAICA BLE** and choose **Download**.
5. Install the latest stable release.
6. Restart Home Assistant.
7. Start a weighing so the scale begins advertising.
8. Open **Settings -> Devices & services**. Home Assistant should normally offer
   the discovered LAICA BLE device automatically.
9. Open it and enter the local profile values and scale model.

No YAML configuration is required.

Public releases:

https://github.com/piggei/home-assistant-laica-ble/releases

## Internal build3 installation for validation

For `0.1.1-build3`, **do not use HACS**. Copy only:

```text
custom_components/laica_ble
```

to:

```text
/config/custom_components/laica_ble
```

then restart Home Assistant. This test method deliberately keeps HACS out of the
setup path.

If a previous LAICA BLE config entry exists, remove that config entry first from
**Settings -> Devices & services**. If HACS still has the public repository
installed, it can remain installed while testing only if it does not overwrite
the manually copied directory; otherwise remove the HACS download after the
Home Assistant config entry/discovery flow has been cleared.

## Discovery behavior

LAICA/YoHealth scales advertise only while awake, so start a weighing when
performing first setup.

`0.1.1-build3` deliberately returns to the simple setup flow used by the last
verified development build, with one important discovery correction learned from
the diagnostic build:

- Home Assistant's manifest matcher recognizes Company ID `0xA102` and prefix
  `09 FF`;
- the config flow uses the same public Company ID/header signature to identify a
  scale during discovery;
- a complete checksum-valid measurement is **not** required merely to identify
  the device, because the first packet seen while the scale wakes can be a
  transient measurement frame;
- actual measurements remain strictly validated by `protocol.py` before they can
  update entities.

### Automatic discovery

This is the preferred path. Start a weighing and wait for Home Assistant to show
LAICA BLE under **Settings -> Devices & services**. Opening the discovery card
goes directly to the profile form.

### Manual Add Integration fallback

Start the weighing **before** opening:

**Settings -> Devices & services -> Add integration -> LAICA BLE**

The manual flow reads Home Assistant's shared Bluetooth cache:

- if one compatible scale is present, it goes directly to the profile form;
- if more than one is present, it shows a scale picker;
- if none is present, it exits with a clear “no device found” message. Keep the
  scale awake and try again.

There is intentionally **no custom 15-second scanner, no `scan_now` field, and no
pairing/connect operation** in build3.

### Removal and rediscovery

When a configured LAICA BLE entry is removed, the integration asks Home
Assistant to make its Bluetooth address eligible for rediscovery. Start another
weighing afterwards to trigger a fresh discovery.

## Configuration and profile changes

Use **Settings -> Devices & services -> LAICA BLE -> Configure** to update the
profile without removing the integration.

You can change:

- sex branch;
- date of birth;
- height;
- scale model.

Date of birth accepts `DD/MM/YYYY` or `YYYY-MM-DD` and is stored internally in
ISO format. Age is recalculated at measurement time.

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

See [docs/PROTOCOL.md](docs/PROTOCOL.md) and
[docs/ALGORITHM.md](docs/ALGORITHM.md).

## Compatibility

| Model | Protocol evidence | Algorithm evidence | Status |
|---|---|---|---|
| LAICA PS7002 | direct captures | direct comparison with app | **validated** |
| LAICA PS7200L | historical YoHealth evidence | historical implementation source | strong evidence; HA validation wanted |
| Other LAICA/YoHealth models | unknown | unknown | reports wanted |

The PS7002 is the only model directly validated with this Home Assistant
integration. Do not infer compatibility solely from the LAICA brand or product
appearance.

## Support and issue routing

For **Home Assistant integration problems**—installation, discovery, entity
behavior, configuration, diagnostics, or integration exceptions—use:

https://github.com/piggei/home-assistant-laica-ble/issues

For **scale/protocol research**—additional LAICA models, BLE captures, unknown
packet formats/status values, compatibility reports, or measurement-validation
work—use:

https://github.com/piggei/laica-ps7002-ble-research

## Diagnostics and debug logging

Home Assistant diagnostics are available from the LAICA BLE integration/device
menu. They redact the Bluetooth address and profile fields and do not include
weight, impedance, or raw BLE payloads.

For troubleshooting, temporarily enable:

```yaml
logger:
  logs:
    custom_components.laica_ble: debug
```

Build3 logs only meaningful config-flow transitions. It does not dump every BLE
advertisement and does not log weight, impedance, full manufacturer payloads, or
profile data.

Runtime translation files are stored only in:

```text
custom_components/laica_ble/translations/
```

The package intentionally does not ship `strings.json`, which is a Home
Assistant Core build-time mechanism rather than the runtime source for custom
integrations.

## Validation

The repository contains regression tests for:

- YoHealth frame parsing and checksum validation;
- complete `0x86` measurements;
- deferred `0x82` weight-only measurements and cancellation by `0x86`;
- duplicate/session handling;
- discovery signature versus strict measurement validation;
- profile date parsing and age rollover;
- recovered YoHealth body-composition calculations;
- custom-integration translation packaging.

GitHub Actions run Ruff, pytest, the standalone self-test, Python compilation,
JSON validation, Home Assistant `hassfest`, and HACS validation on repository
pushes and pull requests.

`0.1.1-build3` does **not** modify measurement parsing, the `0x80` / `0x82` /
`0x86` session policy, sensors, or the recovered YoHealth formulas.

## Safety / interpretation

Body-composition values from consumer BIA scales are estimates. This project
reproduces the historical vendor algorithm for interoperability and research; it
is not intended for diagnosis or medical decision-making.

## License and provenance

Project code and original documentation are released under the **MIT License**.
No proprietary LAICA/YoHealth library, APK, firmware, or decompiled proprietary
source is distributed. See [NOTICE.md](NOTICE.md).

This is an independent interoperability project and is not affiliated with or
endorsed by LAICA.
