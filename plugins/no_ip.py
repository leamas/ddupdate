'''
ddupdate plugin updating data on no-ip.com.

See: ddupdate(8)
'''

from ddupdate.plugins_base import UpdatePlugin
from ddupdate.plugins_base import http_basic_auth_setup, get_response


class NoIpPlugin(UpdatePlugin):
    '''
    Update a dns entry on no-ip.com. Does nto require (but allows) an
    ip address, the ip-disabled plugin can be used.

    netrc: Use a line like
        machine dynupdate.no-ip.com login <username>  password <password>

    Options:
        none
    '''
    _name = 'no-ip'
    _oneliner = 'Updates DNS data on no-ip.com'
    _url = "http://dynupdate.no-ip.com/nic/update?hostname={0}"

    def run(self, config, log, ip=None):

        url = self._url.format(config.hostname)
        if ip:
            url += "&myip=" + ip
        http_basic_auth_setup(url, 'dynupdate.no-ip.com')
        get_response(log, url)
