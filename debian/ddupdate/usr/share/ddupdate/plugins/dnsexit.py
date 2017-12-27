'''
ddupdate plugin updating data on dnsexit.com.

See: ddupdate(8)
'''
from netrc import netrc

from plugins.plugins_base import UpdatePlugin, UpdateError, get_response


class DnsexitPlugin(UpdatePlugin):
    '''
    Updates DNS data for host on dnsexit.com.

    The documentation is not clear whether dnsexit can update data
    without given an ip address. The safe route is to avoid the
    ip-disabled plugin for this service.

    The password used is transferred in the url. Contrary to the docs,
    dnsexit actually seems to support https. This plugin uses this, so
    it should be reasonably safe. The service recommends setting up a
    separate password to be used when updating.

    According to the docs the correct way is to interrogate dnsexit.com
    for update urls. However, we don't, we just assume the url is fixed.

    netrc: Use a line like
        machine update.dnsexit.com login <username> password <password>
    Options:
        None
    '''
    _name = 'dnsexit'
    _oneliner = 'Updates host on www.dnsexit.com'

    _update_host = 'http://update.dnsexit.com'
    _url = '{0}/RemoteUpdate.sv?login={1}&password={2}&host={3}'
    _ip_warning = \
        "service is not known to provide an address, use another ip plugin"

    def run(self, config, log, ip=None):
        if not ip:
            log.warn(self._ip_warning)
        auth = netrc().authenticators('update.dnsexit.com')
        if not auth:
            raise UpdateError(
                "No user/password for update.dnsexit.com found in .netrc")
        url = self._url.format(
            self._update_host, auth[0], auth[2], config.hostname)
        if ip:
            url += "&myip=" + ip
        # if debugging:
        #     url += "&force=Y" # override 8 minutes server limit
        html = get_response(log, url).split('\n')
        if '200' not in html[0]:
            raise UpdateError("Bad HTML response: " + html)
        code = html[1].split('=')[0]
        if int(code) > 1:
            raise UpdateError("Bad update response: " + html[1])
        log.info("Response: " + html[1])
