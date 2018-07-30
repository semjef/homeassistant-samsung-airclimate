'''
Support for samsung AR09MSPXBWKNER.

@author: semjef
'''

import logging

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.const import (
    CONF_IP_ADDRESS, CONF_TOKEN, CONF_PORT)
from homeassistant.helpers.discovery import load_platform

REQUIREMENTS = [
    'https://github.com/semjef/samsungac/archive/0.6.6.zip#samsungac==0.6.6']

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'samsungac'

CONF_ACS = 'acs'
CONF_CERT_FILE = 'cert'

COMPONENT_TYPES = ['climate', 'sensor']

AC_CONFIG = vol.Schema({
    vol.Required(CONF_IP_ADDRESS): cv.string,
    vol.Required(CONF_PORT, default=8888): cv.port,
    vol.Required(CONF_TOKEN): cv.string,
    vol.Required(CONF_CERT_FILE): cv.string
})


def _fix_conf_defaults(config):
    """Update some configuration defaults."""
    return config


CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Optional(CONF_ACS, default={}):
            vol.All(cv.ensure_list, [AC_CONFIG], [_fix_conf_defaults])
    })
}, extra=vol.ALLOW_EXTRA)


def setup(hass, config):
    for ent in config.get(DOMAIN, {}).get(CONF_ACS, []):
        for component in COMPONENT_TYPES:
            load_platform(hass, component, DOMAIN, ent, config)


def samsungac_api_setup(hass, host, port, cert, token):
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}

    api = hass.data[DOMAIN].get(host)
    if api is None:
        import samsungac

        api = samsungac.Entity(host, port, cert, token)
    return api
