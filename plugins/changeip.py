"""
ddupdate plugin updating data on changeip.com.

See: ddupdate(8)
See:
 http://www.changeip.com/accounts/knowledgebase.php?action=displayarticle&id=34
"""

from ddupdate.ddplugin import UpdatePlugin, UpdateError
from ddupdate.ddplugin import http_basic_auth_setup, get_response


class ChangeIpPlugin(UpdatePlugin):
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
        """Implement UpdatePlugin.register."""
        url = self._url.format(hostname)
        if ip:
            url += "&ip=" + ip.v4
        http_basic_auth_setup(url, 'nic.ChangeIP.com')
        html = get_response(log, url, self._socket_to)
        if not'uccessful' in html:
            raise UpdateError("Bad update reply: " + html)
