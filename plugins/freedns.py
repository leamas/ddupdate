"""
ddupdate plugin updating data on freedns.afraid.org.

See: ddupdate(8)
See: https://linuxaria.com/howto/dynamic-dns-with-bash-afraid-org
"""

from ddupdate.ddplugin import ServicePlugin, ServiceError
from ddupdate.ddplugin import get_response, get_netrc_auth


class FreednsPlugin(ServicePlugin):
    """
    Updates DNS data for host on freedns.afraid.org.

    Freedns allows settings the IP address using an address plugin or
    just using the address as seen from the internet using the ip-disabled
    plugin. Ipv6 is supported.

    netrc: Use a line like
        machine freedns.afraid.org login <username> password <password>
    Options:
        None
    """

    _name = 'freedns.afraid.org'
    _oneliner = 'Updates on https://freedns.afraid.org'
    _url = 'https://sync.afraid.org/u/?u={0}&p={1}&h={2}'

    def register(self, log, hostname, ip, options):
        """
        Based on http://freedns.afraid.org/api/, needs _url below  to update.
        """
        user, password = get_netrc_auth('freedns.afraid.org')
        url = self._url.format(user, password, hostname)
        if ip and ip.v6:
            url += "&ip=" + str(ip.v6)
        elif ip and ip.v4:
            url += "&ip=" + str(ip.v4)
        html = get_response(log, url)
        if not ('Updated' in html or 'skipping' in html):
            raise ServiceError("Error updating %s" % hostname)
