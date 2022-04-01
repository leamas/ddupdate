"""
ddupdate plugin updating data on desec.io.

See: ddupdate(8)
See: https://desec.readthedocs.io/en/latest/dyndns/update-api.html
"""

from ddupdate.ddplugin import ServicePlugin
from ddupdate.ddplugin import http_basic_auth_setup, get_response
from ddupdate.ddplugin import get_netrc_auth


class DesecPlugin(ServicePlugin):
    """
    Update a dns entry on desec.io

    Supports most address plugins including default-web-ip, default-if and
    ip-disabled. ipv6 is supported.

    netrc: Use a line like
        machine update.dedyn.io login <username>  password <password>

    Options:
        none
    """

    _name = 'desec.io'
    _oneliner = 'Updates on http://desec.io/'
    _url = "https://update.dedyn.io/?hostname={0}"

    def register(self, log, hostname, ip, options):
        """Implement ServicePlugin.register()."""
        url = self._url.format(hostname)
        if ip.v4:
            url += "&myipv4=" + ip.v4
        if ip.v6:
            url += "&myipv6=" + ip.v6
        username, password = get_netrc_auth(hostname)
        hdr = ('Authorization', 'Token ' + password )
        reply = get_response(log, url, header  = hdr )
        if not ('good' in reply or 'throttled' in reply):
            raise ServiceError("Cannot update address: " + reply)

