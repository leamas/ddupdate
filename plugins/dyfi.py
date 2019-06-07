"""
ddupdate plugin updating data on dy.fi.

See: ddupdate(8)
See: https://www.dy.fi/page/specification

"""

from ddupdate.ddplugin import ServicePlugin, ServiceError
from ddupdate.ddplugin import http_basic_auth_setup, get_response


class DyFiPlugin(ServicePlugin):
    """
    Update a dns entry on dy.fi.

    Does not support setting arbitrary ip address. The ip-disabled plugin
    should be used, and the address set is as seen from dy.fi.

    netrc: Use a line like
        machine www.dy.fi login <username>  password <password>

    Options:
        none
    """

    _name = 'dy.fi'
    _oneliner = 'Updates on https://www.dy.fi/'
    _url = 'https://www.dy.fi/nic/update?hostname={0}'
    _ip_cache_ttl = 7200 # 5 days

    def register(self, log, hostname, ip, options):
        """Implement ServicePlugin.register."""
        url = self._url.format(hostname)
        http_basic_auth_setup(url)
        html = get_response(log, url)
        if html.split()[0] not in ['nochg', 'good']:
            raise ServiceError("Bad update reply: " + html)
