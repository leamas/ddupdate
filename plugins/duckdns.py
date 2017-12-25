'''
ddupdate plugin updating data on duckdns.org.

See: ddupdate(8)

'''
from netrc import netrc

from plugins.plugins_base import UpdatePlugin, UpdateError, get_response


class DuckdnsPlugin(UpdatePlugin):
    '''
    Update a dns entry on duckdns.org. As usual, any host updated must
    first be defined in the web UI. Providing an ip address is optional
    but supported; the ip-disabled plugin can be used.

    Access to the service requires an API token. This is available in the
    website account.

    netrc: Use a line like
        machine www.duckdns.org password <API token from website>

    Options:
        None
    '''
    _name = 'duckdns'
    _oneliner = 'Update DNS data on duckdns.org'
    _url = "https://www.duckdns.org/update?domains={0}&token={1}"

    def run(self, config, log, ip=None):

        auth = netrc().authenticators('www.duckdns.org')
        if not auth or not auth[2]:
            raise UpdateError(
                "No password/token for www.duckdns.org found in .netrc")
        hostname = config.hostname.split('.duckdns.org')[0]
        url = self._url.format(hostname, auth[2])
        if ip:
            url += "&ip=" + ip
        html = get_response(log, url)
        if html.strip() != "OK":
            raise UpdateError("Update error, got: %s", html)
