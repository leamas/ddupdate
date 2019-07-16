"""
ddupdate plugin updating data on now-dns.com.

See: ddupdate(8)
See: https://now-dns.com/?p=clients

"""
import base64
import urllib.request
import urllib.error

from ddupdate.ddplugin import ServicePlugin, ServiceError, \
    http_basic_auth_setup, get_response


class NowDnsPlugin(ServicePlugin):
    """
    Update a dns entry on now-dns.com.

    As usual, any host updated must first be defined in the web UI.
    Supports most address plugins including default-web-ip, default-if
    and ip-disabled. ipv6 address are supported by the site, but not
    by this plugin.

    now-dns uses an odd authentication scheme without challenge. Using
    wget, the --auth-no-challenge is required. This code copes with this
    mess.

    netrc: Use a line like
        machine  now-dns.com user <username> password <password>

    Options:
        None
    """

    _name = 'now-dns.com'
    _oneliner = 'Updates on http://now-dns.com'
    _url = 'https://now-dns.com/update?hostname={0}'

    def register(self, log, hostname, ip, options):
        """Implement ServicePlugin.register()."""
        url = self._url.format(hostname)
        if ip:
            url += '&myip=' + ip.v4
        http_basic_auth_setup(url)
        html = get_response(log, request)
        if html not in ['good', 'nochg']:
            raise ServiceError('Bad server reply: ' + html)
