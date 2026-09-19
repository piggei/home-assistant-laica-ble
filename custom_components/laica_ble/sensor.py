"""Sensors for LAICA BLE scales."""

from __future__ import annotations

from typing import Any, override

from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothDataProcessor,
    PassiveBluetoothDataUpdate,
    PassiveBluetoothEntityKey,
    PassiveBluetoothProcessorEntity,
)
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import UnitOfMass, UnitOfRatio, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import CONF_SCALE_MODEL, MANUFACTURER, PROTOCOL_NAME
from .device import LaicaMeasurementUpdate

OHM = "Ω"
KCAL_PER_DAY = "kcal/day"

KEY_WEIGHT = "weight"
KEY_IMPEDANCE = "impedance"
KEY_BMI = "bmi"
KEY_BODY_FAT = "body_fat"
KEY_WATER = "body_water"
KEY_MUSCLE = "muscle"
KEY_BONE = "bone_mass"
KEY_VISCERAL_FAT = "visceral_fat"
KEY_BODY_AGE = "body_age"
KEY_BMR = "bmr"

SENSOR_DESCRIPTIONS: dict[str, SensorEntityDescription] = {
    # Keep the primary measurement first. Home Assistant does not expose a
    # supported "display order" API for the device page, but creating the
    # principal sensor first gives the frontend the best possible hint.
    KEY_WEIGHT: SensorEntityDescription(
        key=KEY_WEIGHT,
        translation_key="body_weight",
        device_class=SensorDeviceClass.WEIGHT,
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    KEY_BMI: SensorEntityDescription(
        key=KEY_BMI,
        translation_key=KEY_BMI,
        icon="mdi:human",
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    KEY_BODY_FAT: SensorEntityDescription(
        key=KEY_BODY_FAT,
        translation_key=KEY_BODY_FAT,
        icon="mdi:percent",
        native_unit_of_measurement=UnitOfRatio.PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    KEY_WATER: SensorEntityDescription(
        key=KEY_WATER,
        translation_key=KEY_WATER,
        icon="mdi:water-percent",
        native_unit_of_measurement=UnitOfRatio.PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    KEY_MUSCLE: SensorEntityDescription(
        key=KEY_MUSCLE,
        translation_key=KEY_MUSCLE,
        icon="mdi:arm-flex",
        native_unit_of_measurement=UnitOfRatio.PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    KEY_BONE: SensorEntityDescription(
        key=KEY_BONE,
        translation_key=KEY_BONE,
        icon="mdi:bone",
        device_class=SensorDeviceClass.WEIGHT,
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=2,
    ),
    KEY_VISCERAL_FAT: SensorEntityDescription(
        key=KEY_VISCERAL_FAT,
        translation_key=KEY_VISCERAL_FAT,
        icon="mdi:percent-circle-outline",
        native_unit_of_measurement=UnitOfRatio.PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    KEY_BMR: SensorEntityDescription(
        key=KEY_BMR,
        translation_key=KEY_BMR,
        icon="mdi:fire",
        native_unit_of_measurement=KCAL_PER_DAY,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
    KEY_BODY_AGE: SensorEntityDescription(
        key=KEY_BODY_AGE,
        translation_key=KEY_BODY_AGE,
        icon="mdi:calendar-account",
        native_unit_of_measurement=UnitOfTime.YEARS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        entity_registry_enabled_default=False,
    ),
    KEY_IMPEDANCE: SensorEntityDescription(
        key=KEY_IMPEDANCE,
        translation_key=KEY_IMPEDANCE,
        icon="mdi:omega",
        native_unit_of_measurement=OHM,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
}


def _display_name(model: str) -> str:
    model = model.strip()
    if model.lower().startswith("laica"):
        return model
    return f"LAICA {model}"


def measurement_to_bluetooth_update(
    update: LaicaMeasurementUpdate | None,
    *,
    model: str,
) -> PassiveBluetoothDataUpdate[float | int]:
    """Convert an accepted weighing into Home Assistant entity data."""
    if update is None:
        return PassiveBluetoothDataUpdate()

    device_info = DeviceInfo(
        manufacturer=MANUFACTURER,
        model=model,
        name=_display_name(model),
    )

    entity_data: dict[PassiveBluetoothEntityKey, float | int] = {}
    entity_descriptions: dict[
        PassiveBluetoothEntityKey, SensorEntityDescription
    ] = {}

    def add(key: str, value: float | int) -> None:
        entity_key = PassiveBluetoothEntityKey(key, None)
        entity_data[entity_key] = value
        entity_descriptions[entity_key] = SENSOR_DESCRIPTIONS[key]

    # A final 0x86 frame always publishes the final weight.
    add(KEY_WEIGHT, update.frame.weight_kg)

    # If a final frame has no impedance (e.g. a future confirmed socks/no-BIA
    # case), only weight is updated. Existing body-composition entities retain
    # their last valid measurement instead of being overwritten with nonsense.
    if update.frame.impedance is not None and update.metrics is not None:
        metrics = update.metrics
        # Publish the user-facing body-composition values in the same logical
        # order used in the documentation. Impedance is added last and marked
        # diagnostic so it appears separately from normal measurements.
        add(KEY_BMI, metrics.bmi)
        add(KEY_BODY_FAT, metrics.body_fat_pct)
        add(KEY_WATER, metrics.water_pct)
        add(KEY_MUSCLE, metrics.muscle_pct)
        add(KEY_BONE, metrics.bone_mass_kg)
        add(KEY_VISCERAL_FAT, metrics.visceral_fat_pct)
        add(KEY_BMR, metrics.bmr_kcal_per_day)
        add(KEY_BODY_AGE, metrics.body_age)
        add(KEY_IMPEDANCE, update.frame.impedance)

    return PassiveBluetoothDataUpdate(
        devices={None: device_info},
        entity_descriptions=entity_descriptions,
        entity_data=entity_data,
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up LAICA BLE sensors."""
    coordinator = entry.runtime_data
    model = str(entry.options[CONF_SCALE_MODEL])

    processor: PassiveBluetoothDataProcessor[
        float | int, LaicaMeasurementUpdate | None
    ] = PassiveBluetoothDataProcessor(
        lambda update: measurement_to_bluetooth_update(update, model=model)
    )

    entry.async_on_unload(
        processor.async_add_entities_listener(LaicaBluetoothSensor, async_add_entities)
    )
    entry.async_on_unload(
        coordinator.async_register_processor(processor, SensorEntityDescription)
    )


class LaicaBluetoothSensor(PassiveBluetoothProcessorEntity, SensorEntity):
    """Representation of a LAICA BLE measurement sensor."""

    @property
    @override
    def native_value(self) -> float | int | None:
        """Return the latest retained measurement value."""
        return self.processor.entity_data.get(self.entity_key)

    @property
    @override
    def available(self) -> bool:
        """Keep last weighing available while the battery scale is sleeping.

        Smart scales advertise only during a weighing. Tying availability to
        current BLE visibility would make all entities unavailable almost all
        the time, which is not useful for retained measurement sensors.
        """
        return self.entity_key in self.processor.entity_data
