"""
ddupdate plugin updating data on changeip.com.

See: ddupdate(8)
See:
 http://www.changeip.com/accounts/knowledgebase.php?action=displayarticle&id=34
"""

from ddupdate.ddplugin import ServicePlugin, ServiceError
from ddupdate.ddplugin import http_basic_auth_setup, get_response


class ChangeAddressPlugin(ServicePlugin):
    """
    Update a dns entry on changeip.com.

    Does not require (but allows) an ip address, the ip-disabled plugin
    can be used.

    netrc: Use a line like
        machine nic.ChangeIP.com login <username>  password <password>

    Options:
        none
    """

    _name = 'changeip.com'
    _oneliner = 'Updates on http://changeip.com/'
    _url = "https://nic.ChangeIP.com/nic/update?&hostname={0}"

    def register(self, log, hostname, ip, options):
        """Implement ServicePlugin.register."""
        url = self._url.format(hostname)
        if ip:
            url += "&ip=" + ip.v4
        http_basic_auth_setup(url)
        html = get_response(log, url)
        if not'uccessful' in html:
            raise ServiceError("Bad update reply: " + html)
