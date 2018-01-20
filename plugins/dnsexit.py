"""
ddupdate plugin updating data on dnsexit.com.

See: ddupdate(8)
See: http://downloads.dnsexit.com/ipUpdateDev.doc
"""

from ddupdate.ddplugin import ServicePlugin, ServiceError
from ddupdate.ddplugin import get_response, get_netrc_auth


class DnsexitPlugin(ServicePlugin):
    """
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
    """

    _name = 'dnsexit.com'
    _oneliner = 'Updates on https://www.dnsexit.com'

    _update_host = 'http://update.dnsexit.com'
    _url = '{0}/RemoteUpdate.sv?login={1}&password={2}&host={3}'
    _ip_warning = \
        "service is not known to provide an address, use another ip plugin"

    def register(self, log, hostname, ip, options):
        """Implement AddressPlugin.get_ip()."""
        if not ip:
            log.warn(self._ip_warning)
        user, password = get_netrc_auth('update.dnsexit.com')
        url = self._url.format(
            self._update_host, user, password, hostname)
        if ip:
            url += "&myip=" + ip.v4
        # if debugging:
        #     url += "&force=Y" # override 8 minutes server limit
        html = get_response(log, url).split('\n')
        if '200' not in html[0]:
            raise ServiceError("Bad HTML response: " + html)
        code = html[1].split('=')[0]
        if int(code) > 1:
            raise ServiceError("Bad update response: " + html[1])
        log.info("Response: " + html[1])
