'''
Support for samsung AR09MSPXBWKNER.

@author: semjef
'''

import logging
from os import path
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.util.temperature import convert as convert_temperature
from homeassistant.components.climate import (
    ATTR_TARGET_TEMP_HIGH, ATTR_TARGET_TEMP_LOW, DOMAIN,
    ClimateDevice, PLATFORM_SCHEMA, STATE_DRY, STATE_AUTO,
    STATE_COOL, STATE_FAN_ONLY, STATE_HEAT, SUPPORT_TARGET_TEMPERATURE,
    SUPPORT_TARGET_TEMPERATURE_HIGH, SUPPORT_TARGET_TEMPERATURE_LOW,
    SUPPORT_OPERATION_MODE, SUPPORT_SWING_MODE, SUPPORT_FAN_MODE)
from homeassistant.const import (
    CONF_IP_ADDRESS, CONF_TOKEN, CONF_PORT, ATTR_ENTITY_ID, ATTR_TEMPERATURE,
    CONF_SCAN_INTERVAL, STATE_ON, STATE_OFF, STATE_UNKNOWN,
    TEMP_CELSIUS, TEMP_FAHRENHEIT)

REQUIREMENTS = ['samsungac==0.1']
_LOGGER = logging.getLogger(__name__)

SUPPORT_FLAGS = (SUPPORT_TARGET_TEMPERATURE |
                 SUPPORT_TARGET_TEMPERATURE_HIGH |
                 SUPPORT_TARGET_TEMPERATURE_LOW |
                 SUPPORT_OPERATION_MODE |
                 SUPPORT_SWING_MODE |
                 SUPPORT_FAN_MODE)

CONF_CERT_FILE = 'cert'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_IP_ADDRESS): cv.string,
    vol.Required(CONF_PORT): cv.string,
    vol.Required(CONF_TOKEN): cv.string,
    vol.Required(CONF_CERT_FILE): cv.string
})


def setup_platform(hass, config, add_devices, discovery_info=None):
    import samsungac

    host = config.get(CONF_IP_ADDRESS)
    port = config.get(CONF_PORT)
    cert = config.get(CONF_CERT_FILE)
    token = config.get(CONF_TOKEN)

    api = samsungac.Entity(host, port, cert, token)
    add_devices([SamsungClimate(api)], True)


class SamsungClimate(ClimateDevice):
    def __init__(self, api):
        self._api = api

        self._name = None

        self._temperature_unit = None
        self._temperature_current = None
        self._temperature_desired = None
        self._temperature_min = None
        self._temperature_max = None

        self._current_operation = None

    @property
    def name(self):
        """Return the name of the lyric, if any."""
        return self._name

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
    def current_operation(self):
        """Return current operation ie. heat, cool, idle."""
        if self._current_operation in [STATE_AUTO, STATE_COOL, STATE_DRY,
                                       STATE_FAN_ONLY, STATE_HEAT, STATE_OFF]:
            return self._current_operation
        else:
            return STATE_UNKNOWN

    def update(self):
        data = self._api.get()
        self._name = data['Device']['name']

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
