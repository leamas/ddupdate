"""
ddupdate plugin updating data on Hurricane Electric a k a he.com.

See: ddupdate(8)
See: https://dns.he.net/docs.html

"""

from ddupdate.ddplugin import ServicePlugin, get_netrc_auth, get_response


class FreednsIoPlugin(ServicePlugin):
    """
    Updates DNS data for host on Hurricane Electric's site he.com.

    As usual, any host updated must first be defined in the web UI.
    Supports most address plugins including default-web-ip, default-if
    and ip-disabled. Ipv6 is supported.

    Hurricane uses a separate password/key for each host, generated in
    the web interface. Updating both ipv4 and ipv6 is supported by
    hurricane, but this plugin uses ipv6 if such an address is available,
    othwerwise it falls back to using ipv4.

    netrc: Use a line like
        machine <hostname> password <key>

    Options:
        None
    """

    _name = 'hurricane_electric'
    _oneliner = 'Updates on https://he.com'
    _url = 'https://dyn.dns.he.net/nic/update'

    def register(self, log, hostname, ip, options):
        """Implement ServicePlugin.register."""
        password = get_netrc_auth(hostname)[1]
        data = {'password': password, 'hostname': hostname}
        if ip and ip.v6:
            data['myip'] = ip.v6
        elif ip and ip.v4:
            data['myip'] = ip.v4
        html = get_response(log, self._url, data=data)
        log.info("Server reply: " + html)
