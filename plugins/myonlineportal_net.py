"""
ddupdate plugin updating data on myonlineportal.net.

See: ddupdate(8)
See: http://myonlineportal.net/ddns_api
"""

from ddupdate.ddplugin import ServicePlugin, ServiceError, \
    get_response, http_basic_auth_setup


class MyOnlinePortalPlugin(ServicePlugin):
    """
    Updates DNS data for host on myonlineportal.net  .

    As usual, any host updated must first be defined in the web UI.
    Supports most address plugins including default-web-ip, default-if and
    ip-disabled. ipv6 is  supported.

    netrc: Use a line like
        machine myonlineportal.net login <username> password <password>

    Options:
        None
    """

    _name = 'myonlineportal.net'
    _oneliner = 'Updates on http://myonlineportal.net/'
    _url = 'https://myonlineportal.net/updateddns?hostname={0}'

    def register(self, log, hostname, ip, options):
        """Implement ServicePlugin.register()."""
        url = self._url.format(hostname)
        if ip and ip.v4:
            url += "&ip=" + ip.v4
        if ip and ip.v6:
            url += "&ip6=" + ip.v6
        http_basic_auth_setup(url)
        html = get_response(log, url)
        key = html.split()[0]
        if key not in ['OK', 'good', 'nochg']:
            raise ServiceError("Bad server reply: " + html)
        log.info("Server reply: " + html)
