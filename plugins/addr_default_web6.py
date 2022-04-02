"""
ddupdate plugin to retrieve ipv6 address as seen from internet.

See: ddupdate(8)
"""

import urllib.request
import urllib.error
import re

from ddupdate.ddplugin import AddressPlugin, AddressError, IpAddr

TIMEOUT = 20


class DefaultWeb6Plugin(AddressPlugin):
    """
    Get the external ipv6 address as seen from the web.

    Relies on now-dns.com, falling back to ipv6.whatismyip.akamai.com
    and ifcfg.me.

    Options used: none
    """

    _name = 'default-web-ip6'
    _oneliner = 'Obtain external ipv6 address as seen from the net'

    def get_ip(self, log, options):
        """Implement AddressPlugin.get_ip()."""
        def check_url(url):
            """Get reply from host and decode."""
            log.debug('trying ' + url)
            try:
                with urllib.request.urlopen(url, None, TIMEOUT) as response:
                    if response.getcode() != 200:
                        log.debug("Bad response at %s (ignored)" % url)
                        return None
                    html = response.read().decode()
            except urllib.error.URLError as err:
                log.debug("Got URLError: %s", err)
                return None
            log.debug("Got response: %s", html)
            pat = re.compile(r'[:0-9a-f]{12,}(\s|\Z)')
            match = pat.search(html)
            if match:
                return html[match.start(): match.end()]
            log.debug("Cannot parse ipv6 address reply")
            return None

        urls = [
            'https://now-dns.com/ip',
            'http://ipv6.whatismyip.akamai.com',
            'https://ifcfg.me/'
        ]
        for ix, url in enumerate(urls):
            log.info('Trying: %s', url)
            ip = check_url(url)
            if ip:
                return IpAddr(None, ip)
            if ix + 1 < len(urls):
                log.info("Falling back to %s", urls[ix + 1])
        raise AddressError(
            "Cannot obtain ip6 address (%s, %s and %s tried)"
            % tuple(urls))
