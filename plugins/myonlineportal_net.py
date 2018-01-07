"""
ddupdate plugin updating data on myonlineportal.net.

See: ddupdate(8)
See: http://myonlineportal.net/ddns_api
"""

from ddupdate.ddplugin import UpdatePlugin, UpdateError, \
    get_response, http_basic_auth_setup


class MyOnlinePortalPlugin(UpdatePlugin):
    """
    Updates DNS data for host on myonlineportal.net  .

    As usual, any host updated must first be defined in the web UI.
    Providing an ip address is optional but supported; the ip-disabled
    plugin can be used.

    netrc: Use a line like
        machine myonlineportal.net login <username> password <password>

    Options:
        None
    """

    _name = 'myonlineportal.net'
    _oneliner = 'Updates on http://myonlineportal.net/ [ipv6]'
    _url = 'https://myonlineportal.net/updateddns?hostname={0}'

    def register(self, log, hostname, ip, options):
        """Implement UpdatePlugin.register()."""
        url = self._url.format(hostname)
        if ip and ip.v4:
            url += "&ip=" + ip.v4
        if ip and ip.v6:
            url += "&ip6=" + ip.v6
        http_basic_auth_setup(url, 'myonlineportal.net')
        html = get_response(log, url, self._socket_to)
        key = html.split()[0]
        if key not in ['OK', 'good', 'nochg']:
            raise UpdateError("Bad server reply: " + html)
        log.info("Server reply: " + html)
