'''
Support for samsung AC.

@author: semjef
'''

import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.components.climate import ClimateDevice, PLATFORM_SCHEMA
from homeassistant.components.climate.const import (
    ATTR_FAN_MODE, ATTR_SWING_MODE, STATE_DRY, STATE_AUTO,
    STATE_COOL, STATE_FAN_ONLY, STATE_HEAT, SUPPORT_TARGET_TEMPERATURE,
    SUPPORT_ON_OFF, SUPPORT_OPERATION_MODE, SUPPORT_SWING_MODE, SUPPORT_FAN_MODE,
    ATTR_OPERATION_MODE)
from homeassistant.const import (
    CONF_IP_ADDRESS, CONF_TOKEN, CONF_PORT, ATTR_TEMPERATURE,
    STATE_ON, STATE_OFF, STATE_UNKNOWN,
    TEMP_CELSIUS, TEMP_FAHRENHEIT)
from custom_components.samsungac import CONF_CERT_FILE, samsungac_api_setup

_LOGGER = logging.getLogger(__name__)

SUPPORT_FLAGS = (SUPPORT_TARGET_TEMPERATURE |
                 SUPPORT_OPERATION_MODE |
                 SUPPORT_SWING_MODE |
                 SUPPORT_FAN_MODE |
                 SUPPORT_ON_OFF)

HA_STATE_TO_SAMSUNG = {
    STATE_AUTO: 'auto',
    STATE_COOL: 'cool',
    STATE_DRY: 'dry',
    STATE_FAN_ONLY: 'wind',
    STATE_HEAT: 'heat'
}

HA_FAN_TO_SAMSUNG = {
    'auto': 0,
    'low': 1,
    'mid': 2,
    'high': 3,
    'turbo': 4
}

HA_SWING_TO_SAMSUNG = {
    # TODO: need correct values
    'fix': 'fix',
    'swingud': 'swingud',
    'swinglr': 'swinglr',
    'rotation': 'rotation'
}

SAMSUNG_TO_HA_STATE = {c: s for s, c in HA_STATE_TO_SAMSUNG.items()}
SAMSUNG_TO_HA_FAN = {c: s for s, c in HA_FAN_TO_SAMSUNG.items()}
SAMSUNG_TO_HA_SWING = {c: s for s, c in HA_SWING_TO_SAMSUNG.items()}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_IP_ADDRESS): cv.string,
    vol.Required(CONF_PORT): cv.string,
    vol.Required(CONF_TOKEN): cv.string,
    vol.Required(CONF_CERT_FILE): cv.string
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    if discovery_info is not None:
        host = discovery_info.get(CONF_IP_ADDRESS)
        port = discovery_info.get(CONF_PORT)
        cert = discovery_info.get(CONF_CERT_FILE)
        token = discovery_info.get(CONF_TOKEN)
    else:
        host = config.get(CONF_IP_ADDRESS)
        port = config.get(CONF_PORT)
        cert = config.get(CONF_CERT_FILE)
        token = config.get(CONF_TOKEN)

    api = samsungac_api_setup(hass, host, port, cert, token)
    add_devices([SamsungClimate(api)], True)


class SamsungClimate(ClimateDevice):
    def __init__(self, api):
        self._api = api

        self._name = None
        self._is_on = None

        self._temperature_unit = None
        self._temperature_current = None
        self._temperature_desired = None
        self._temperature_min = None
        self._temperature_max = None

        self._current_operation = None
        self._current_fan = None
        self._current_swing = None

        self._list = {
            ATTR_OPERATION_MODE: list(
                map(str.title, set(HA_STATE_TO_SAMSUNG.values()))
            ),
            ATTR_FAN_MODE: list(
                map(str.title, set(HA_FAN_TO_SAMSUNG.keys()))
            ),
            ATTR_SWING_MODE: list(
                map(str.title, set(HA_SWING_TO_SAMSUNG.keys()))
            ),
        }

    @property
    def name(self):
        """Return the name, if any."""
        return self._name

    @property
    def state(self):
        """Return the current state."""
        if self.is_on is False:
            return STATE_OFF
        if self.current_operation:
            return self.current_operation
        if self.is_on:
            return STATE_ON
        return STATE_UNKNOWN

    @property
    def is_on(self):
        """Return true if on."""
        return self._is_on

    def turn_on(self):
        """Turn device on."""
        self._api.power('On')

    def turn_off(self):
        """Turn device off."""
        self._api.power('Off')

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_FLAGS

    @property
    def device_class(self):
        """Return the class of this device, from component DEVICE_CLASSES."""
        return 'AC'

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return self._temperature_unit

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return self._temperature_min

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return self._temperature_max

    @property
    def current_temperature(self):
        """Return the current temperature."""
        return self._temperature_current

    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._temperature_desired

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        return 1

    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        value = kwargs.get(ATTR_TEMPERATURE)
        if value is None:
            return
        try:
            temp = str(int(value))
        except ValueError:
            _LOGGER.error("Invalid temperature %s", value)
        self._api.set_temp(temp)

    @property
    def operation_list(self):
        """Return the list of available operation modes."""
        return self._list.get(ATTR_OPERATION_MODE)

    @property
    def fan_list(self):
        """Return the list of available fan modes."""
        return self._list.get(ATTR_FAN_MODE)

    @property
    def swing_list(self):
        """Return the list of available swing modes."""
        return self._list.get(ATTR_SWING_MODE)

    @property
    def current_operation(self):
        """Return current operation ie. heat, cool, idle."""
        if self._current_operation in SAMSUNG_TO_HA_STATE:
            return SAMSUNG_TO_HA_STATE[self._current_operation]
        else:
            return STATE_UNKNOWN

    @property
    def current_fan_mode(self):
        """Return the fan setting."""
        if self._current_fan in SAMSUNG_TO_HA_FAN:
            return SAMSUNG_TO_HA_FAN[self._current_fan]
        else:
            return STATE_UNKNOWN

    @property
    def current_swing_mode(self):
        """Return the fan setting."""
        if self._current_swing in SAMSUNG_TO_HA_SWING:
            return SAMSUNG_TO_HA_SWING[self._current_swing]
        else:
            return STATE_UNKNOWN

    def set_operation_mode(self, operation_mode):
        """Set new target operation mode."""
        self._api.set_mode(HA_STATE_TO_SAMSUNG[operation_mode.lower()])

    def set_fan_mode(self, fan_mode):
        """Set new target fan mode."""
        self._api.set_speed(HA_FAN_TO_SAMSUNG[fan_mode.lower()])

    def set_swing_mode(self, swing_mode):
        """Set new target swing operation."""
        self._api.set_direction(HA_SWING_TO_SAMSUNG[swing_mode.lower()])

    def update(self):
        data = self._api.get()
        self._name = data['Device']['name']

        self._is_on = data['Device']['Operation']['power'] == 'On'

        self._temperature_unit = (
            TEMP_CELSIUS if data['Device']['Temperatures'][0]['unit'] ==
            'Celsius' else TEMP_FAHRENHEIT)
        self._temperature_current = data['Device']['Temperatures'][0][
            'current']
        self._temperature_desired = data['Device']['Temperatures'][0][
            'desired']
        self._temperature_min = data['Device']['Temperatures'][0]['minimum']
        self._temperature_max = data['Device']['Temperatures'][0]['maximum']

        self._current_operation = data['Device']['Mode']['modes'][0].lower()

        self._current_swing = data['Device']['Wind']['direction'].lower()
        self._current_fan = int(data['Device']['Wind']['speedLevel'])
