'''
ddupdate plugin to retrieve address.

See: ddupdate(8)
'''

import urllib.request
import re

from plugins.plugins_base import IpPlugin, IpLookupError


class DefaultWebPlugin(IpPlugin):
    ''' Get the external address as seen from the web. Relies on
    dyndns.org, falling back to ipify.org and ifconfig.co.

    Options used: none
    '''
    _name = 'default-web-ip'
    _oneliner = 'Obtain external address as seen from the net'

    def run(self, config, log, ip=None):

        def check_url(url):
            ''' Get reply from host and decode '''
            log.debug('trying ' + url)
            with urllib.request.urlopen(url) as response:
                if response.getcode() != 200:
                    log.debug("Bad response at %s (ignored)" % url)
                    return None
                html = response.read().decode('ascii')
            log.debug("Got response: %s", html)
            pat = re.compile(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}")
            m = pat.search(html)
            if m:
                return html[m.start(): m.end()]
            log.debug("Cannot parse address reply")
            return None

        ip = check_url('http://checkip.dyndns.org/')
        if ip:
            return ip
        log.info("Falling back to ipify.org")
        ip = check_url('https://api.ipify.org?format=json')
        if ip:
            return ip
        log.info("Falling back to ifconfig.co")
        ip = check_url('wget https://ifconfig.co')
        if ip:
            return ip
        raise IpLookupError(
            "Cannot obtain ip address (dyndns.org and ipify.org tried)")
