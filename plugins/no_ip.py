"""
ddupdate plugin updating data on no-ip.com.

See: ddupdate(8)
See: https://www.noip.com/integrate/request
"""

from ddupdate.ddplugin import UpdatePlugin
from ddupdate.ddplugin import http_basic_auth_setup, get_response


class NoIpPlugin(UpdatePlugin):
    """
    Update a dns entry on no-ip.com.

    Does not require (but allows) an ip address, the ip-disabled plugin can
    be used.

    netrc: Use a line like
        machine dynupdate.no-ip.com login <username>  password <password>

    Options:
        none
    """

    _name = 'no-ip.com'
    _oneliner = 'Updates on http://no-ip.com/'
    _url = "http://dynupdate.no-ip.com/nic/update?hostname={0}"

    def register(self, log, hostname, ip, options):
        """Implement UpdatePlugin.register()."""
        url = self._url.format(hostname)
        if ip:
            url += "&myip=" + ip.v4
        http_basic_auth_setup(url, 'dynupdate.no-ip.com')
        get_response(log, url, self._socket_to)
