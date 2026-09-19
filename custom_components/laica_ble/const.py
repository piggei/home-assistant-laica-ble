"""Constants for the LAICA BLE integration."""

from typing import Final

DOMAIN: Final = "laica_ble"

CONF_SEX: Final = "sex"
CONF_BIRTH_DATE: Final = "birth_date"
CONF_HEIGHT_CM: Final = "height_cm"
CONF_SCALE_MODEL: Final = "scale_model"

SEX_MALE: Final = "male"
SEX_FEMALE: Final = "female"
SEX_VALUES: Final = (SEX_MALE, SEX_FEMALE)

DEFAULT_SCALE_MODEL: Final = "PS7002"

MANUFACTURER: Final = "LAICA"
PROTOCOL_NAME: Final = "YoHealth"

# Bluetooth Manufacturer Specific Data company identifier.
# NimBLE exposed the two company-id bytes as 02 A1, therefore Home Assistant /
# Bleak represents the integer key as little-endian 0xA102.
YOHEALTH_COMPANY_ID: Final = 0xA102

# Observed YoHealth measurement states on PS7002.
REALTIME_STATUS: Final = 0x80
STABLE_WEIGHT_STATUS: Final = 0x82
FINAL_STATUS: Final = 0x86

# Hold a stable weight-only frame briefly to give a full 0x86 body-composition
# frame priority when bare-foot electrode contact is available.
STABLE_WEIGHT_DELAY_SECONDS: Final = 2.5

# If a final frame is repeated continuously, emit it once. The parser is re-armed
# by any non-0x86 protocol frame. The timeout is a safety net if transition frames
# were missed by the Bluetooth scanner.
FINAL_REARM_TIMEOUT_SECONDS: Final = 30.0
