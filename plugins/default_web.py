"""
ddupdate plugin to retrieve address as seen from internet.

See: ddupdate(8)
"""

import urllib.request
import re

from ddupdate.ddplugin import AddressPlugin, AddressError, IpAddr


_URLS = [
    'http://checkip.dyndns.org/',
    'https://api.ipify.org?format=json',
    'https://ifconfig.co'
]


class DefaultWebPlugin(AddressPlugin):
    """
    Get the external address as seen from the web.

    Relies on urls defined in _URLS, trying each in turn when running
    into trouble.

    Options used: none
    """

    _name = 'default-web-ip'
    _oneliner = 'Obtain external address as seen from the net'

    def get_ip(self, log, options):
        """Implement AddressPlugin.get_ip()."""
        def check_url(url):
            """Get reply from host and decode."""
            log.debug('trying ' + url)
            try:
                with urllib.request.urlopen(url) as response:
                    if response.getcode() != 200:
                        log.debug("Bad response at %s (ignored)" % url)
                        return None
                    html = response.read().decode('ascii')
            except (urllib.error.HTTPError, urllib.error.URLError) as err:
                raise AddressError("Error reading %s :%s" % (url, err))
            log.debug("Got response: %s", html)
            pat = re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
            match = pat.search(html)
            if match:
                return html[match.start(): match.end()]
            log.debug("Cannot parse address reply")
            return None

        for ix, url in enumerate(_URLS):
            ip = check_url(url)
            if ip:
                return IpAddr(ip)
            if ix + 1 < len(_URLS):
                log.info("Falling back to %s", _URLS[ix + 1])
        raise AddressError(
            "Cannot obtain ip address (%s, %s and %s tried)" % tuple(_URLS))
