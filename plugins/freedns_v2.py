"""
ddupdate plugin updating data on freedns.afraid.org api v2 random token.

See: ddupdate(8)
See: https://freedns.afraid.org
See: https://freedns.afraid.org/dynamic/v2/ (needs login)
"""

from ddupdate.ddplugin import ServicePlugin, ServiceError
from ddupdate.ddplugin import get_response, get_netrc_auth


class FreednsV2Plugin(ServicePlugin):
    """
    Updates DNS data for host on freedns.afraid.org with API v2 token.

    Freedns allows settings the IP address using an address plugin or
    just using the address as seen from the internet using the ip-disabled
    plugin. Ipv6 is supported. V2 api uses a random token which is simpler
    and more secure, your credentials or domains are never exposed.

    Login to freedns.afraid.org, switch to v2 API and add your domain to be
    updated with v2, select 'randomized token' update style and take note
    of the update url for your domain, it should be like:

        https://sync.afraid.org/u/{API-v2-token}/

    Copy the token part of the url and use it as password in .netrc file.
    Since ddupdate-config currently doesn't support services with multiple
    hostnames, you must edit .netrc file by hand in the meanwhile.

    Netrc: use lines with this *non-standard* format (no braces):
        machine {your.hostname}@sync.afraid.org password {API-v2-token}

    Options:
        None
    """
    # descriptive name, i see no need to set as url because _onliner already tells
    _name = 'sync.afraid.org'
    _oneliner = 'Updates on https://sync.afraid.org/u/{API-v2-token}/'
    _url = 'https://{0}sync.afraid.org/u/{1}/'

    def register(self, log, hostname, ip, options):
        """
        Based on  https://freedns.afraid.org/dynamic/v2/, needs _url below
        to update.

        The {1} parameter is a randomized update token, generated specificly
        for each domain(s) when enabled for api v2. The server automatically
        detects public source IP, but optionally you can provide it.
        """
        password = get_netrc_auth(hostname + '@sync.afraid.org')[1]
        url = ''
        if ip and ip.v6:
            url = self._url.format('v6.', password) + '?address=' + str(ip.v6)
        else:
            url = self._url.format(''   , password)
            if ip and ip.v4:
                url += '?address=' + str(ip.v4)
        log.debug("Contacting freedns for update v2 on %s", url)
        html = get_response(log, url)
        if html.startswith("Couldn't "):
            raise ServiceError("Update error, got: " + html)
