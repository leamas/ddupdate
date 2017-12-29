'''
ddupdate plugin updating data on freedns.io

See: ddupdate(8)
'''

from ddupdate.plugins_base import UpdatePlugin, get_netrc_auth, get_response


class FreednsIoPlugin(UpdatePlugin):
    '''
    Updates DNS data for host on freedns.io. As usual, any host updated must
    first be defined in the web UI. Providing an ip address is optional
    but supported; the ip-disabled plugin can be used.

    The service offers more functionality not exposed here: ipv6
    addresses, TXT and MX records, etc. See https://freedns.io/api
    It should be straight-forward to add options supporting this.

    netrc: Use a line like
        machine freedns.io login <username> password <password>

    Options:
        None
    '''
    _name = 'freedns.io'
    _oneliner = 'Updates DNS data on freedns.io'
    _url = 'https://freedns.io/request'

    def run(self, config, log, ip=None):

        user, password = get_netrc_auth('freedns.io')

        data = {
            'username': user,
            'password': password,
            'host': config.hostname.split('.freedns.io')[0],
            'record': 'A'
        }
        if ip:
            data['value'] = ip
        html = get_response(log, self._url, data)
        log.info("Server reply: " + html)
