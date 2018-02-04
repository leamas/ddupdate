"""
ddupdate plugin updating data on dynu.com.

See: ddupdate(8)
See: https://www.dynu.com/Resources/API/Documentation

"""
import hashlib
from ddupdate.ddplugin import ServicePlugin, get_response, get_netrc_auth


class DynuPlugin(ServicePlugin):
    """
    Update a dns entry on dynu.com.

    Supports most address plugins including default-wep-ip, default-if
    and ip-disabled. ipv6 is supported.

    .netrc: Use a line like:
        machine api.dynu.com login <username> password <password>

    Options:
        none
    """

    _name = 'dynu.com'
    _oneliner = 'Updates on https://www.dynu.com/en-US/DynamicDNS'
    _url = "http://api.dynu.com" \
        + "/nic/update?hostname={0}&username={1}&password={2}"

    def register(self, log, hostname, ip, options):
        """Implement ServicePlugin.register()."""
        user, password = get_netrc_auth('api.dynu.com')
        pw_hash = hashlib.md5(password.encode()).hexdigest()
        url = self._url.format(hostname, user, pw_hash)
        if ip and ip.v4:
            url += "&myip=" + ip.v4
        if ip and ip.v6:
            url += "&myipv6=" + ip.v6
        get_response(log, url)
