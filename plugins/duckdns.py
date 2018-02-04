"""
ddupdate plugin updating data on duckdns.org.

See: ddupdate(8)
See: https://www.duckdns.org/spec.jsp

"""
from ddupdate.ddplugin import ServicePlugin, ServiceError
from ddupdate.ddplugin import get_response, get_netrc_auth


class DuckdnsPlugin(ServicePlugin):
    """
    Update a dns entry on duckdns.org.

    As usual, any host updated must first be defined in the web UI.
    Supports most address plugins including default-web-ip, default-if
    and ip-disabled. ipv6 is supported

    Access to the service requires an API token. This is available in the
    website account.

    netrc: Use a line like
        machine www.duckdns.org password <API token from website>

    Options:
        None
    """

    _name = 'duckdns.org'
    _oneliner = 'Updates on http://duckdns.org'
    _url = "https://www.duckdns.org/update?domains={0}&token={1}"

    def register(self, log, hostname, ip, options):
        """Implement ServicePlugin.register()."""
        password = get_netrc_auth('www.duckdns.org')[1]
        host = hostname.split('.duckdns.org')[0]
        url = self._url.format(host, password)
        if ip and ip.v4:
            url += "&ip=" + ip.v4
        if ip and ip.v6:
            url += "&ipv6=" + ip.v6
        html = get_response(log, url)
        if html.strip() != "OK":
            raise ServiceError("Update error, got: %s", html)
