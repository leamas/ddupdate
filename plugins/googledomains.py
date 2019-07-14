"""
ddupdate plugin updating data on domains.google.com.

See: ddupdate(8)
See: https://support.google.com/domains/answer/6147083?hl=en

"""
import urllib.parse
import urllib.request
from ddupdate.ddplugin import ServiceError, ServicePlugin, \
    get_response, http_basic_auth_setup


class GoogleDomainsPlugin(ServicePlugin):
    """
    Update a DNS entry on domains.google.com.

    .netrc: Use a line like:
        machine domains.google.com login <username> password <password>

    Options:
        none
    """

    _name = "domains.google.com"
    _oneliner = "Updates on https://domains.google.com"
    _url = "https://domains.google.com/nic/update"

    def register(self, log, hostname, ip, options):
        """Implement ServicePlugin.register()."""
        query = {
            'hostname': hostname,
        }

        # IP address is optional for IPv4
        if ip:
            query['myip'] = ip.v6 or ip.v4

        url="{}?{}".format(self._url, urllib.parse.urlencode(query))
        http_basic_auth_setup(url)
        request = urllib.request.Request(url=url, method='POST')
        html = get_response(log, request)

        code = html.split()[0]
        if code not in ['good', 'nochg']:
            raise ServiceError("Bad server reply: " + html)
