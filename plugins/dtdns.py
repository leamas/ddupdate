"""
ddupdate plugin updating data on dtdns.com.

See: ddupdate(8)
See: https://www.dtdns.com/dtsite/updatespec

"""
from ddupdate.ddplugin import ServicePlugin, ServiceError
from ddupdate.ddplugin import get_response, get_netrc_auth


class DtdnsPlugin(ServicePlugin):
    """
    Update a dns entry on dtdns.com.

    Supports most address plugins including default-web-ip, default-if and
    ip-disabled. ipv6 is not supporterted. The number of hosts are limited
    for free accounts, see website.

    .netrc: Use a line like:
        machine www.dtdns.com login <username>  password <password>

    Options:
        none
    """

    _name = 'dtdns.com'
    _oneliner = 'Updates on https://www.dtdns.com'
    _url = "https://www.dtdns.com/api/autodns.cfm?id={0}&pw={1}"

    # pylint: disable=unused-variable

    def register(self, log, hostname, ip, options):
        """Implement ServicePlugin.register()."""
        user, password = get_netrc_auth('www.dtdns.com')
        url = self._url.format(hostname, password)
        if ip:
            url += "&ip=" + ip.v4
        try:
            html = get_response(log, url)
        except TimeoutError:
            # one more try...
            html = get_response(log, url)
        if 'points to' not in html:
            raise ServiceError("Bad update reply: " + html)
        log.info("Update completed: " + html)
