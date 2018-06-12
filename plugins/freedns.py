"""
ddupdate plugin updating data on freedns.afraid.org.

See: ddupdate(8)
See: https://linuxaria.com/howto/dynamic-dns-with-bash-afraid-org
"""

import hashlib

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
    _url = 'https://freedns.afraid.org/api/?action=getdyndns&sha={0}'

    def register(self, log, hostname, ip, options):
        """
        Based on http://freedns.afraid.org/api/, needs _url below  to update.

        The sha parameter is sha1sum of login|password.  This returns a list
        of host|currentIP|updateURL lines.  Pick the line that matches myhost,
        and fetch the URL.  word 'Updated' for success, 'fail' for failure.
        """
        def build_shasum():
            """Compute sha1sum('user|password') used in url."""
            user, password = get_netrc_auth('freedns.afraid.org')
            token = "{0}|{1}".format(user, password)
            return hashlib.sha1(token.encode()).hexdigest()

        shasum = build_shasum()
        url = self._url.format(shasum)
        if ip and ip.v6:
            url += "&address=" + str(ip.v6)
        elif ip and ip.v4:
            url += "&address=" + str(ip.v4)
        html = get_response(log, url)
        update_url = None
        for line in html.split("\n"):
            log.debug("Got line: " + line)
            tokens = line.split("|")
            if tokens[0] == hostname:
                update_url = tokens[2]
                break
        if not update_url:
            raise ServiceError(
                "Cannot see %s being set up at this account" % hostname)
        log.debug("Contacting freedns for update on %s", update_url)
        get_response(log, update_url)
