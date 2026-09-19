# LAICA BLE for Home Assistant

Experimental local Bluetooth integration for LAICA smart body-composition scales
using the **YoHealth** advertising protocol.

Current release: **0.1.0-dev.1**

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
3. **only accepts final status `0x86`** in this first release;
4. decodes final weight and, when present, impedance;
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

Body-composition sensors are created after the first final frame containing a
valid impedance value. If a final `0x86` frame is received without impedance,
only weight is updated and previous body-composition values are retained.

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

## Conservative final-frame policy

PS7002 captures showed states including `0x80`, `0x82` and `0x86`. To avoid
publishing realtime or partially settled values, **v0.1.x deliberately ignores
`0x80` and `0x82` for entity updates**. They are observed only to identify a new
weighing session.

A future release may optionally accept `0x82` for weight-only measurements after
we have captured and documented behavior with socks/shoes or failed electrode
contact.

## Installation

### Manual

1. Copy `custom_components/laica_ble` into your Home Assistant configuration:

   ```text
   /config/custom_components/laica_ble
   ```

2. Restart Home Assistant.
3. Make sure Home Assistant has a working Bluetooth adapter or Bluetooth proxy.
4. Start a weighing so the scale begins advertising.
5. Home Assistant should discover **LAICA BLE** automatically. Alternatively go
   to **Settings -> Devices & services -> Add integration -> LAICA BLE** while
   the scale is advertising.
6. Enter the local profile values and the scale model.

No YAML configuration is required.

## Profile changes

Use **Settings -> Devices & services -> LAICA BLE -> Configure** to update date
of birth, height, sex branch or model. The integration reloads automatically.
Age is calculated from the date of birth at measurement time.

## Protocol at a glance

Home Assistant/Bleak exposes Company ID `0xA102` separately from the 12-byte
payload:

```text
09 FF WW WW ZZ ZZ SS FF FF MM CC AA
```

- `WW WW`: weight raw, big-endian;
- `ZZ ZZ`: health/impedance raw, big-endian (`FFFF` = unavailable);
- `SS`: status (`86` = accepted final status in this release);
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

Please use the GitHub issue forms for additional models and comparison samples.

## Safety / interpretation

Body-composition values from consumer BIA scales are estimates. This project
reproduces the historical vendor algorithm for interoperability and research; it
is not intended for diagnosis or medical decision-making.

## Development status

This first custom-integration build targets current Home Assistant Bluetooth
processor/config-flow APIs. It is intentionally a development release: the next
step is live validation on a real Home Assistant installation with the PS7002.

## License and provenance

Project code and original documentation are released under the **MIT License**.
No proprietary LAICA/YoHealth library, APK, or decompiled source is distributed
in this repository. See [NOTICE.md](NOTICE.md).

### Repository URL note

This development archive assumes the repository name
`piggei/home-assistant-laica-ble` in `manifest.json`. If you choose a different
GitHub repository name, change only the `documentation` and `issue_tracker` URLs
in `custom_components/laica_ble/manifest.json` before publishing.

### Debug logging

For troubleshooting, temporarily add:

```yaml
logger:
  logs:
    custom_components.laica_ble: debug
```

The integration logs accepted final frame metadata, not the configured date of
birth or other profile details.
