"""
ddupdate plugin updating data on dynu.com.

See: ddupdate(8)
See: https://www.dynu.com/Resources/API/Documentation

"""
import base64
from urllib.parse import urlparse

from ddupdate.ddplugin import ServicePlugin, ServiceError
from ddupdate.ddplugin import get_response, get_netrc_auth


class DynuPlugin(ServicePlugin):
    """
    Update a dns entry on dynu.com.

    Supports most address plugins including default-wep-ip, default-if
    and ip-disabled. ipv6 is supported.

    .netrc: Use a line like:
        machine api.dynu.com login <username> password <password>

    Options:
        none

    See: https://www.dynu.com/en-US/DynamicDNS/IP-Update-Protocol
    """

    _name = 'dynu.com'
    _oneliner = 'Updates on https://www.dynu.com/en-US/DynamicDNS'
    _url = "https://api.dynu.com/nic/update?host={0}"

    def register(self, log, hostname, ip, options):
        """Implement ServicePlugin.register()."""
        url = self._url.format(hostname)
        api_host = urlparse(url).hostname
        username, password = get_netrc_auth(api_host)
        user_pw = ('%s:%s' % (username, password))
        credentials = base64.b64encode(user_pw.encode('ascii'))
        auth_header = ('Authorization', 'Basic ' + credentials.decode("ascii"))
        if ip and ip.v4:
            url += "&myip=" + ip.v4
        if ip and ip.v6:
            url += "&myipv6=" + ip.v6
        reply = get_response(log, url, header=auth_header)
        if not ('good' in reply or 'nochg' in reply):
            raise ServiceError("Update error: " + reply)
