"""

ddupdate plugin updating data on dnspark.com.

See: ddupdate(8)
See: https://dnspark.zendesk.com/hc/en-us/articles/
        216322723-Dynamic-DNS-API-Documentation
"""

from ddupdate.ddplugin import ServicePlugin, ServiceError
from ddupdate.ddplugin import http_basic_auth_setup, get_response


class DnsparkPlugin(ServicePlugin):
    """
    Update a dns entry on dnspark.com.

    Supports most address plugins including default-web-ip, default-if and
    ip-disabled. ipv6 is not supported.

    You need to own a domain and delegate it to dnspark to use the service,
    nothing like myhost.dnspark.net is supported.

    Note that the dynamic dns user and password is a separate set of
    credentials created in the web interface.

    netrc: Use a line like
        machine control.dnspark.com login <username>  password <password>

    Options:
        none
    """

    _name = 'dnspark.com'
    _oneliner = 'Updates on https://dnspark.com/'
    _url = "https://control.dnspark.com/api/dynamic/update.php?hostname={0}"

    def register(self, log, hostname, ip, options):
        """Implement ServicePlugin.register()."""
        url = self._url.format(hostname)
        if ip and ip.v4:
            url += "&ip=" + ip.v4
        http_basic_auth_setup(url)
        reply = get_response(log, url).strip()
        if reply not in ['ok', 'nochange']:
            raise ServiceError("Unexpected update reply: " + reply)
