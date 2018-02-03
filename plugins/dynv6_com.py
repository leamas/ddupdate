"""
ddupdate plugin updating data on dynv6.

See: ddupdate(8)
See: https://dynv6.com/docs/apis

"""
from ddupdate.ddplugin import ServicePlugin, ServiceError
from ddupdate.ddplugin import get_response, get_netrc_auth


class Dynv6Plugin(ServicePlugin):
    """
    Update a dns entry on dynv6.com.

    As usual, any host updated must first be defined in the web UI.
    Supports most address plugins including default-web-ip, default-if
    and ip-disabled. dynv6 also supports ipv6 addresses.

    Access to the service requires an API token. This is available in the
    website account.

    netrc: Use a line like
        machine dynv6.com password <API token from website>

    Options:
        None
    """

    _name = 'dynv6.com'
    _oneliner = 'Updates on http://dynv6.com'
    _url = "https://dynv6.com/api/update?hostname={0}&token={1}"

    def register(self, log, hostname, ip, options):
        """Implement ServicePlugin.register()."""
        password = get_netrc_auth('dynv6.com')[1]
        url = self._url.format(hostname, password)
        if ip and ip.v4:
            url += "&ipv4=" + ip.v4
        if ip and ip.v6:
            url += "&ipv6=" + ip.v6
        html = get_response(log, url)
        if not ('updated' in html or 'unchanged' in html):
            raise ServiceError("Update error, got: %s", html)
