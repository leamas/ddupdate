'''
ddupdate plugin updating data on duckdns.org.

See: ddupdate(8)

'''
from ddupdate.plugins_base import UpdatePlugin, UpdateError
from ddupdate.plugins_base import get_response, get_netrc_auth


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
    _oneliner = 'Updates DNS data on duckdns.org'
    _url = "https://www.duckdns.org/update?domains={0}&token={1}"

    # pylint: disable=unused-variable

    def run(self, config, log, ip=None):

        user, password = get_netrc_auth('www.duckdns.org')
        hostname = config.hostname.split('.duckdns.org')[0]
        url = self._url.format(hostname, password)
        if ip:
            url += "&ip=" + ip
        html = get_response(log, url)
        if html.strip() != "OK":
            raise UpdateError("Update error, got: %s", html)
