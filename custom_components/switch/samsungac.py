'''
Support for samsung AC.

@author: semjef
'''

import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.components.switch import (
    SwitchDevice, PLATFORM_SCHEMA)
from homeassistant.const import (
    CONF_IP_ADDRESS, CONF_TOKEN, CONF_PORT)
from custom_components.samsungac import CONF_CERT_FILE, samsungac_api_setup

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
    add_devices([SamsungWindSwitch(api), SamsungSpiSwitch(api)], True)


class SamsungWindSwitch(SwitchDevice):
    def __init__(self, api):
        self._api = api

        self._name = None
        self._is_on = None

    @property
    def name(self):
        """Return the name of the device if any."""
        return self._name

    @property
    def is_on(self):
        """Return true if on."""
        return self._is_on

    def turn_on(self):
        """Turn device on."""
        self._api.wind(True)

    def turn_off(self):
        """Turn device off."""
        self._api.wind(False)

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        if self._is_on:
            return 'mdi:power-on'
        return 'mdi:power-off'

    def update(self):
        data = self._api.get()
        self._name = "{} Wind".format(data['Device']['name'])
        self._is_on = ('Comode_Nano' in data['Device']['Mode']['options'] and
                       data['Device']['Operation']['power'] == 'On')


class SamsungSpiSwitch(SwitchDevice):
    def __init__(self, api):
        self._api = api

        self._name = None
        self._is_on = None

    @property
    def name(self):
        """Return the name of the device if any."""
        return self._name

    @property
    def is_on(self):
        """Return true if on."""
        return self._is_on

    def turn_on(self):
        """Turn device on."""
        self._api.spi(True)

    def turn_off(self):
        """Turn device off."""
        self._api.spi(False)

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        if self._is_on:
            return 'mdi:power-on'
        return 'mdi:power-off'

    def update(self):
        data = self._api.get()
        self._name = "{} Spi".format(data['Device']['name'])
        self._is_on = ('Spi_On' in data['Device']['Mode']['options'] and
                       data['Device']['Operation']['power'] == 'On')
