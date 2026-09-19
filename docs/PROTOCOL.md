# YoHealth BLE protocol used by the LAICA PS7002

## Evidence status

The byte layout below was recovered from real PS7002 BLE captures and
cross-checked against historical YoHealth/PS7200L reverse-engineering material.

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

- `11..19`: weight-only family;
- `21..29`: body-composition family;
- units digit `1`: divide weight raw by 10;
- units digit `2`: divide weight raw by 100.

The integration supports precision digits 1 and 2, with `/10` as a conservative
fallback for an unknown mode.

### Impedance / health

```text
02 99 = 0x0299 = 665
```

`FFFF` is observed when a usable body-composition measurement is unavailable and
is treated as missing impedance. `0000` is also rejected as unavailable.

### Status and publication policy

Observed PS7002 transitions include:

- `0x80`: realtime / measurement in progress;
- `0x82`: stable weight;
- `0x86`: complete/final body-composition result.

Direct footwear testing showed that a valid weighing can end at `0x82` when the
user is not making electrical contact with the electrodes. Release `0.1.0` and later
therefore use this policy:

1. `0x80` never updates entities and re-arms a new weighing session.
2. The first `0x82` is retained as a stable weight-only candidate for 2.5
   seconds. Repeated `0x82` advertisements update the candidate frame but do not
   restart the timer indefinitely.
3. If `0x86` arrives during the hold-off, the pending `0x82` is cancelled and
   only `0x86` is published.
4. If no `0x86` arrives, the pending `0x82` is published once as weight-only.
5. A valid `0x86` is published immediately. If its impedance field is unavailable,
   only weight is updated.
6. Body-composition values are calculated only from `0x86` with usable
   impedance; incomplete measurements never overwrite the previous BIA-derived
   values.

This gives one normal complete update for barefoot measurements while still
supporting weight-only measurements with footwear or unavailable electrode
contact.

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

## Session and duplicate handling

The scale repeats advertisements during a weighing. The integration combines two
small session gates:

- the final-frame gate suppresses repeated `0x86` advertisements and has a
  30-second safety re-arm timeout if transition frames are missed;
- the stable-weight gate schedules at most one deferred `0x82` weight-only
  publication per weighing session and is re-armed by the next `0x80`.

A complete `0x86` always cancels a pending stable-weight timer, so the normal
`0x80 -> 0x82 -> 0x86` sequence produces a single complete measurement rather
than a weight-only update followed by a second full update.

## Scope

The protocol behavior above is directly validated on LAICA PS7002. Historical
YoHealth material provides evidence for related devices, but additional models
must be validated individually before they are claimed as supported.

Compatibility work, new captures, and protocol questions belong in the technical
research repository:

https://github.com/piggei/laica-ps7002-ble-research
