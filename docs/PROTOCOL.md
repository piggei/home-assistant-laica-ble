# YoHealth BLE protocol used by the LAICA PS7002

## Evidence status

The byte layout below was recovered from real PS7002 BLE captures and cross-
checked against historical YoHealth/PS7200L reverse-engineering material.

The Home Assistant integration uses only fields needed for deterministic local
operation and validates every accepted frame checksum.

## Manufacturer data representation

A raw BLE Manufacturer Specific Data element observed with NimBLE included:

```text
02 A1 09 FF 03 27 02 99 86 FF FF 21 15 AA
```

NimBLE includes the two Company ID bytes (`02 A1`). Bleak/Home Assistant instead
uses the little-endian Company ID as the dictionary key:

```text
manufacturer_id = 0xA102
payload          = 09 FF 03 27 02 99 86 FF FF 21 15 AA
```

The Home Assistant manifest therefore matches:

```json
{
  "connectable": false,
  "manufacturer_id": 41218,
  "manufacturer_data_start": [9, 255]
}
```

## Payload layout

```text
Offset  Size  Meaning
0       2     Header: 09 FF
2       2     Weight raw, big-endian
4       2     Health / impedance raw, big-endian
6       1     Status
7       2     Unknown / reserved (observed FF FF)
9       1     Device mode / weight precision
10      1     Checksum
11      1     Terminator AA
```

### Weight

Validated PS7002 mode byte is `0x21` and weight is raw/10:

```text
03 27 = 0x0327 = 807 -> 80.7 kg
```

Historical application logic treated the mode byte as BCD-like:

- 11..19: weight-only family;
- 21..29: body-composition family;
- units digit 1: divide weight raw by 10;
- units digit 2: divide weight raw by 100.

The integration supports precision digits 1 and 2, with /10 as conservative
fallback for an unknown mode.

### Impedance / health

```text
02 99 = 0x0299 = 665
```

`FFFF` is observed before a valid body-composition measurement and is treated as
unavailable. `0000` is also rejected as unavailable.

### Status

Observed PS7002 transitions include:

- `0x80`: realtime/in-progress;
- `0x82`: stable weight/no-body-composition candidate;
- `0x86`: final body-composition result.

For v0.1.x, Home Assistant publishes **only `0x86`**. `0x80` and `0x82` are used
only to re-arm duplicate suppression for the next weighing.

If future captures show `0x86` with `FFFF` impedance (for example socks/no
contact), the current implementation safely publishes only the final weight.
If the scale instead stops at `0x82`, no entity is updated in v0.1.x by design.

## Checksum

For the 14-byte NimBLE representation:

```text
checksum = sum(bytes[0..11]) & 0xFF
```

For Home Assistant's 12-byte post-Company-ID payload:

```text
checksum = (0x02 + 0xA1 + sum(payload[0..9])) & 0xFF
expected = payload[10]
```

Reference frame:

```text
02 A1 09 FF 03 27 02 99 86 FF FF 21 15 AA
```

produces checksum `0x15`.

## Duplicate handling

A final frame is broadcast repeatedly for several seconds. The integration emits
one logical measurement per session:

1. first valid `0x86` -> accepted;
2. repeated `0x86` -> ignored;
3. any valid non-`0x86` frame -> re-arm;
4. a 30-second timeout also re-arms if transition advertisements were missed.
