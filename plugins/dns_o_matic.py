"""
ddupdate plugin updating data on https://www.dnsomatic.com/.

See: ddupdate(8)
See: https://now-dns.com/?p=clients

"""
import base64
from urllib.parse import urlparse

from ddupdate.ddplugin import ServicePlugin, ServiceError, \
    get_response, get_netrc_auth


class DnsOMaticPlugin(ServicePlugin):
    """
    Update a dns entry on https://www.dnsomatic.com.

    The hostname is the configured hostname in dns-o-matic. Common usecase
    is to set hostname=all.dnsomatic.com which will  update all hosts.

    Only supports setting the address corresponding to default-web-ip or
    ip-disabled, service does not allow setting address to anything else.
    ipv6 is not supported.

    netrc: Use a line like
        machine updates.dnsomatic.com login <username> password <password>

    Options:
        None
    """

    _name = 'dns-o-matic.com'
    _oneliner = 'Updates on http://dnsomatic.com'
    _url = 'https://updates.dnsomatic.com/nic/update?hostname={0}'

    def register(self, log, hostname, ip, options):
        """Implement ServicePlugin.register()."""
        url = self._url.format(hostname)
        if ip:
            url += '&myip=' + ip.v4
        api_host = urlparse(url).hostname
        username, password = get_netrc_auth(api_host)
        user_pw = ('%s:%s' % (username, password))
        credentials = base64.b64encode(user_pw.encode('ascii'))
        auth_header = ('Authorization', 'Basic ' + credentials.decode("ascii"))
        reply = get_response(log, url, header=auth_header)
        if not ('good' in reply or 'nochg' in reply):
            raise ServiceError('Bad server reply: ' + reply)
