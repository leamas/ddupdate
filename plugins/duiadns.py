'''
ddupdate plugin updating data on duiadns.com.

See: ddupdate(8)

'''
from html.parser import HTMLParser

from ddupdate.plugins_base import UpdatePlugin, UpdateError
from ddupdate.plugins_base import get_response, get_netrc_auth


class DuiadnsParser(HTMLParser):
    ''' Dig out ip address and hostname in server HTML reply. '''

    def error(self, message):
        raise UpdateError("HTML parser error: " + message)

    def __init__(self):
        HTMLParser.__init__(self)
        self.data = {}

    def handle_data(self, data):
        if data.strip() == '':
            return
        words = data.split()
        if len(words) == 2:
            self.data[words[0]] = words[1]
        else:
            self.data['error'] = data


class DuiadnsPlugin(UpdatePlugin):
    '''
    Update a dns entry on duiadnscom. As usual, any host updated must
    first be defined in the web UI. Providing an ip address is optional
    but supported; the ip-disabled plugin can be used.

    Access to the service requires an API token. This is available in the
    website account.

    The documentation is partially broken, but the code here seems to
    work. In particular, using the recommended @IP provokes a 500
    error. Overall, the server seems fragile and small errors provokes
    500 replies rather than expected error messages.

    Also, it returns a needlessly complicated HTML-formatted reply.

    This site is one of few supporting ipv6 addresses.

    netrc: Use a line like
        machine ip.duiadns.net password <API token from website>

    Options:
        None
    '''
    _name = 'duiadns'
    _oneliner = 'Updates DNS data on duiadns.com'
    _url = 'https://ip.duiadns.net/dynamic.duia?host={0}&password={1}'

    # pylint: disable=unused-variable

    def run(self, config, log, ip=None):

        user, password = get_netrc_auth('ip.duiadns.net')
        url = self._url.format(config.hostname, password)
        if ip:
            url += "&ip4=" + ip
        html = get_response(log, url)
        parser = DuiadnsParser()
        parser.feed(html)
        if 'error' in parser.data or 'Ipv4' not in parser.data:
            raise UpdateError('Cannot parse server reply (see debug log)')
        log.info('New ip address: ' + parser.data['Ipv4'])
