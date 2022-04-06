"""
ddupdate plugin updating data on dnshome.de.

See: ddupdate(8)
See: https://www.dnshome.de/
"""

import urllib.request
import urllib.error
import ipaddress
from typing import AnyStr, Optional
from enum import Enum
from logging import Logger

from ddupdate.ddplugin import AddressPlugin, IpAddr

TIMEOUT = 20


class DeDnshomeAddressURL(Enum):
    """Enumeration of the available *.dnshome.de ip-resolver urls."""

    IP4 = 'https://ip4.dnshome.de'
    IP6 = 'https://ip6.dnshome.de'


class DeDnshomeWebPlugin(AddressPlugin):
    """Get the external IPv4 and/or IPv6 address as seen from ip.dnshome.de.

    Depending on the type of your connection one or the other address may
    be `None`.  Also the presence of an IPv4 address does not guarantee that
    inbound connections can be instantiated from external endpoints (see:
    DS-Lite and IPv6 tunneling).

    Relies on [ip4|ip6].dnshome.de

    Options used:
        none
    """

    _name = 'ip.dnshome.de'
    _oneliner = 'Obtain IPv4 and/or IPv6 address as seen by dnshome.de'

    @staticmethod
    def extract_ip(data: AnyStr) -> IpAddr:
        """Extracts the IPs from data.

        Expects `data` to be an UTF-8 string holding either an single
        IPv4 or an IPv6 address.

        Args:
            data: Data to extract the IP from

        Returns:
            An `IpAddr` which may hold the IPv4 or IPv6 Address found.
        """
        try:
            ip = ipaddress.ip_address(data.strip())

            if isinstance(ip, ipaddress.IPv4Address):
                return IpAddr(ip.exploded, None)
            if isinstance(ip, ipaddress.IPv6Address):
                return IpAddr(None, ip.exploded)
            return IpAddr(None, None)
        except ValueError:
            return IpAddr(None, None)

    @staticmethod
    def load_ip(log: Logger, url: str) -> Optional[IpAddr]:
        """Loads the external IP from an remote Endpoint (url).

        Expects the Endpoint to respond with an UTF-8-String containing the IP.

        Args:
            log: Logger
            url: URL to Load the IP from

        Returns:
            An `IPAddr` holding the IPv4 and/or IPv6 Address found or `None`.
        """
        log.debug('loading ip from %s' % url)

        try:
            with urllib.request.urlopen(url, None, TIMEOUT) as response:
                body = response.read().decode()
        except urllib.error.URLError as err:
            log.debug("Got URLError: %s", err)
            return None

        log.debug("Got response: %s", body)

        result = DeDnshomeWebPlugin.extract_ip(body)

        if result.empty():
            log.debug("Cannot parse IPv4/IPv6 address from response")
            return None

        return result

    def get_ip(self, log: Logger, options: [str]) -> Optional[IpAddr]:
        """Implements AddressPlugin.get_ip()."""
        urls = [DeDnshomeAddressURL.IP4, DeDnshomeAddressURL.IP6]
        ip = IpAddr(None, None)

        for url in urls:
            result = DeDnshomeWebPlugin.load_ip(log, url.value)
            if result:
                if not ip.v4 and result.v4:
                    ip.v4 = result.v4
                if not ip.v6 and result.v6:
                    ip.v6 = result.v6
        log.debug("Returning ip: " + str(ip))
        return ip if not ip.empty() else None
