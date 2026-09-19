# LAICA BLE for Home Assistant

Experimental local Bluetooth integration for LAICA smart body-composition scales
using the **YoHealth** advertising protocol.

Current release: **0.1.0-dev.10**

The integration was developed and directly validated with a **LAICA PS7002**.
Compatibility with other LAICA/YoHealth models is an explicit research goal, but
must be confirmed model by model.

## What it does

The scale broadcasts measurements as non-connectable BLE advertisements. Home
Assistant receives the advertisements locally; no cloud account, GATT connection,
or LAICA app is required for normal operation.

The integration:

1. discovers compatible YoHealth advertisements;
2. validates the protocol header, terminator and checksum;
3. accepts complete status `0x86`, or a deferred stable `0x82` as weight-only;
4. decodes weight and, for complete measurements, impedance;
5. calculates the recovered YoHealth body-composition fields locally from the
   configured profile;
6. retains the last measurement while the scale is sleeping/offline.

### Entities

| Sensor | Source |
|---|---|
| Weight | BLE frame |
| Impedance | BLE frame |
| BMI | recovered YoHealth algorithm |
| Body fat | recovered YoHealth algorithm |
| Body water | recovered YoHealth algorithm |
| Muscle | recovered YoHealth algorithm |
| Bone mass | recovered YoHealth algorithm |
| Visceral fat | recovered YoHealth algorithm |
| Body age | recovered YoHealth algorithm |
| Basal metabolic rate | recovered YoHealth algorithm |

Body-composition sensors are created after the first final `0x86` frame containing
a valid impedance value. A stable `0x82` measurement is accepted as weight-only
after a short hold-off. Likewise, if a final `0x86` frame has no usable impedance,
only weight is updated. Previous body-composition values are retained.

## Important architectural limitation: one person per scale entry

The scale does **not** transmit the identity of the person/profile. Person
selection exists in the companion app, not in the scale BLE protocol.

For that reason a configured LAICA BLE scale has one local calculation profile:

- sex used by the historical LAICA/YoHealth algorithm;
- date of birth;
- height.

Weight itself is valid for anybody using the scale, but calculated body
composition belongs to the configured profile only.

The date of birth and profile values stay in the local Home Assistant config
entry and are not sent anywhere by this integration.

## Measurement-state policy

PS7002 captures show `0x80` while measurement is in progress, `0x82` when the
weight is stable, and `0x86` for a complete body-composition result. Real-world
testing with footwear confirmed that a valid stable weight can stop at `0x82`
when electrode contact is unavailable.

The integration therefore holds the first stable `0x82` candidate for **2.5
seconds**. If `0x86` arrives during that window, the pending `0x82` is cancelled
and only the complete measurement is published. If no `0x86` arrives, the stable
`0x82` weight is published once as a weight-only measurement. `0x80` never updates
entities and re-arms the next weighing session.

Body-composition entities are never recalculated from `0x82`; they keep their
last valid `0x86` values.

## Installation

### HACS (recommended for development installs)

The repository is structured as a HACS custom integration. To install it from
GitHub without copying files manually:

1. Open **HACS** in Home Assistant.
2. Open the menu in the top-right corner and choose **Custom repositories**.
3. Enter this repository URL and select **Integration** as the category.
4. Add the repository, open **LAICA BLE**, and choose **Download**.
5. Restart Home Assistant when HACS requests it.
6. Start a weighing so that the scale advertises over BLE.
7. Go to **Settings -> Devices & services**. When the scale advertises, Home Assistant
   should automatically show the discovered **LAICA BLE** device.
8. Open the discovery card and enter the local profile values and scale model.

The repository contains `hacs.json` and the HACS brand assets required for a
custom integration repository. Development builds used for HACS testing are
published as explicit GitHub Releases so the installed version is unambiguous.

### Manual

1. Copy `custom_components/laica_ble` into your Home Assistant configuration:

   ```text
   /config/custom_components/laica_ble
   ```

2. Restart Home Assistant.
3. Make sure Home Assistant has a working Bluetooth adapter or Bluetooth proxy.
4. Start a weighing so the scale begins advertising.
5. When the scale advertises, Home Assistant should automatically discover
   **LAICA BLE** under **Settings -> Devices & services**.
6. Open the discovery card and enter the local profile values and scale model.

No YAML configuration is required.

## Removal and rediscovery

When a configured LAICA BLE entry is removed, the integration asks Home
Assistant's Bluetooth manager to rediscover the scale address immediately. This
avoids requiring a Home Assistant restart before the same scale can be set up
again.

If discovery does not reappear, check **Settings -> Devices & services** for an
ignored LAICA BLE discovery and restore it before troubleshooting the BLE parser.
An ignored discovery is intentionally suppressed by Home Assistant.

HACS also creates its own repository-management device named **LAICA BLE**. That
HACS device is separate from the physical **LAICA PS7002** device created by this
integration and does not represent a second scale.

## Profile changes

Use **Settings -> Devices & services -> LAICA BLE -> Configure** to update date
of birth, height, sex branch or model. The date of birth can be typed as
`DD/MM/YYYY` or `YYYY-MM-DD`; it is stored internally in ISO format. The integration
reloads automatically, and age is calculated from the date of birth at measurement
time.

## Protocol at a glance

Home Assistant/Bleak exposes Company ID `0xA102` separately from the 12-byte
payload:

```text
09 FF WW WW ZZ ZZ SS FF FF MM CC AA
```

- `WW WW`: weight raw, big-endian;
- `ZZ ZZ`: health/impedance raw, big-endian (`FFFF` = unavailable);
- `SS`: status (`80` = in progress, `82` = stable weight, `86` = final body-composition result);
- `MM`: mode/precision (`21` on the validated PS7002);
- `CC`: checksum;
- `AA`: terminator.

See [docs/PROTOCOL.md](docs/PROTOCOL.md) and
[docs/ALGORITHM.md](docs/ALGORITHM.md).

## Compatibility status

| Model | Protocol | Algorithm | Status |
|---|---|---|---|
| LAICA PS7002 | directly captured | directly compared with app | **validated** |
| LAICA PS7200L | historical YoHealth evidence | historical implementation source | strong evidence, needs new HA test |
| Other LAICA models | unknown | unknown | reports wanted |

For support of additional LAICA/YoHealth devices, protocol captures, algorithm
validation, and compatibility reports, use the dedicated research repository:

https://github.com/piggei/laica-ps7002-ble-research

Issues in this repository should focus on the Home Assistant integration itself.


## Diagnostics

Home Assistant diagnostics are available from the LAICA BLE integration/device menu.
The exported diagnostics intentionally redact the Bluetooth address and all profile
fields (birth date, height and sex branch), and do not include weight, impedance
values or raw BLE payloads. They contain only protocol state useful for debugging.

## Automated validation

The repository includes `pytest` regression tests for the YoHealth parser, final-frame
gate, profile date parsing and recovered body-composition algorithm. GitHub Actions
also run Ruff, the legacy self-test, Python compilation, JSON validation, Home
Assistant `hassfest`, and HACS repository validation on pushes and pull requests.

## Safety / interpretation

Body-composition values from consumer BIA scales are estimates. This project
reproduces the historical vendor algorithm for interoperability and research; it
is not intended for diagnosis or medical decision-making.

## Development status

This consolidation build keeps the validated BLE/parser/algorithm behavior unchanged and adds diagnostics, regression tests and repository validation before the first stable `0.1.0` release. Automatic discovery, profile editing and real PS7002 measurements have been verified in Home Assistant.

## License and provenance

Project code and original documentation are released under the **MIT License**.
No proprietary LAICA/YoHealth library, APK, or decompiled source is distributed
in this repository. See [NOTICE.md](NOTICE.md).

### Debug logging

For troubleshooting, temporarily add:

```yaml
logger:
  logs:
    custom_components.laica_ble: debug
```

The integration logs accepted final frame metadata, not the configured date of
birth or other profile details.


## Entity presentation

**Body weight** is treated as the primary measurement and is created first. Impedance is enabled as a diagnostic entity. Body age is disabled by default and can be enabled from the entity registry. Home Assistant controls the final order shown on the device page.
