'''
ddupdate plugin updating data on system-ns.com.

See: ddupdate(8)

'''
import json
from netrc import netrc

from ddupdate.plugins_base import UpdatePlugin, UpdateError, get_response


class SystemNsPlugin(UpdatePlugin):
    '''
    Update a dns entry on system-ns.com. As usual, any host updated must
    first be defined in the web UI. Providing an ip address is optional
    but supported; the ip-disabled plugin can be used.

    Access to the service requires an API token. This is available in the
    website account.

    netrc: Use a line like
        machine  system-ns.com password <API token from website>

    Options:
        None
    '''
    _name = 'system-ns'
    _oneliner = 'Updates DNS data on system-ns.com'
    _apihost = 'https://system-ns.com/api'
    _url = '{0}?type=dynamic&domain={1}&command=set&token={2}'

    def run(self, config, log, ip=None):

        auth = netrc().authenticators('system-ns.com')
        if not auth or not auth[2]:
            raise UpdateError(
                "No password token for system-ns found in .netrc")
        url = self._url.format(self._apihost, config.hostname, auth[2])
        if ip:
            url += "&ip=" + ip
        html = get_response(log, url)
        reply = json.loads(html)
        if reply['code'] > 2:
            raise UpdateError('Bad reply code {0}, message: {1}'.format(
                reply['code'], reply['msg']))
        log.info("Server reply: " + reply['msg'])
