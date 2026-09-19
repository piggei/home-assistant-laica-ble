# Recovered YoHealth body-composition algorithm

## Inputs

The historical native `getHealth()` logic consumes:

- sex branch (`male` / `female`);
- age in whole years;
- height in cm;
- weight in kg;
- raw BLE health/impedance value.

Home Assistant stores date of birth rather than a fixed age and calculates age
at measurement time.

## Internal lean-mass estimate

With `sex_native = 0` for male and `1` for female:

```text
lean =
    0.00067 * height_cm^2
  + 2.0
  + 0.53 * weight_kg
  - 0.00095 * impedance
  - 3.0 * sex_native
  - 0.05 * age
```

## BMI

```text
BMI = weight_kg / (height_m^2)
```

## Body fat

```text
fat_fraction = (weight_kg - lean) / weight_kg
```

If `fat_fraction < 0.10`:

```text
fat_fraction = fat_fraction + 0.7 * (0.10 - fat_fraction)
```

The user-facing result is `fat_fraction * 100`.

## Body water

```text
water_fraction = 0.73 * lean / weight_kg
water_percent  = water_fraction * 100
```

## Muscle

Male branch:

```text
muscle_percent =
  (7.78 * height_cm + 334 - 9.8 * age) / weight_kg + 24.4
```

Female branch:

```text
muscle_percent =
  (7.74 * height_cm - 318 - 9.8 * age) / weight_kg + 24.4
```

## Bone mass

The native output emitted `30 * bone_mass`; the historical Android consumer
divided field 4 by 30 and named it `boneMass`.

```text
bone_mass =
    0.0077200001 * weight_kg
  + 0.0045 * height_cm
  + 1.95
  - 0.00636 * age
  - 0.000232 * impedance
```

Female branch:

```text
bone_mass *= 0.75
```

## Visceral fat

The native field was a fraction, multiplied by 100 by the Android app:

```text
male:   visceral_fat_percent = fat_fraction * 0.45 * 100
female: visceral_fat_percent = fat_fraction * 0.20 * 100
```

## BMR

Male:

```text
BMR = round(13.7 * weight_kg + 5.0 * height_cm - 6.8 * age + 66)
```

Female:

```text
BMR = round(9.6 * weight_kg + 1.8 * height_cm - 4.7 * age + 655)
```

The implementation reproduces the positive-value C `round()` behavior with
`floor(x + 0.5)`.

## Body age

```text
if age < 20:       age
elif BMI > 28:     age + 15
elif BMI > 26:     age + 12
elif BMI > 25:     age + 7
elif BMI > 23:     age + 4
elif age < 30:     18
elif age <= 44:    age - 12
else:              age - 16
```

## Reference vector

Validated reference:

```text
male
age       55
height    175 cm
weight    80.7 kg
impedance 665
```

Recovered output:

```text
BMI          26.351020...
body fat     23.286245... %
water        56.001041... %
muscle       38.730855... %
bone mass    2.856424... kg
visceral fat 10.478810... %
body age     67
BMR          1673 kcal/day
```

The first PS7002 validation sessions matched the companion application's exposed
BMI/body-fat/water/muscle/BMR values. Bone mass, visceral fat and body age were
identified from the historical Android field mapping even when not exposed by
the current app UI.
