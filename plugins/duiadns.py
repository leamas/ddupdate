"""
ddupdate plugin updating data on duiadns.com.

See: ddupdate(8)
See: https://www.duiadns.net/duiadns-url-update

"""
from html.parser import HTMLParser

from ddupdate.ddplugin import ServicePlugin, ServiceError
from ddupdate.ddplugin import get_response, get_netrc_auth


class DuiadnsParser(HTMLParser):
    """Dig out ip address and hostname in server HTML reply."""

    def error(self, message):
        """Implement HTMLParser.error()."""
        raise ServiceError("HTML parser error: " + message)

    def __init__(self):
        """Default constructor."""
        HTMLParser.__init__(self)
        self.data = {}

    def handle_data(self, data):
        """Implement HTMLParser.handle_data()."""
        if data.strip() == '':
            return
        words = data.split()
        if len(words) == 2:
            self.data[words[0]] = words[1]
        else:
            self.data['error'] = data


class DuiadnsPlugin(ServicePlugin):
    """
    Update a dns entry on duiadns.com.

    As usual, any host updated must first be defined in the web UI. Although
    the server supports auto-detection of addresses this plugin does not;
    the ip-disabled plugin can not be used. ipv6 is supported

    Access to the service requires an API token. This is available in the
    website account.

    The documentation is partially broken, but the code here seems to
    work. In particular, using the recommended @IP provokes a 500
    error. Overall, the server seems fragile and small errors provokes
    500 replies rather than expected error messages.

    Also, it returns a needlessly complicated HTML-formatted reply.

    netrc: Use a line like
        machine ip.duiadns.net password <API token from website>

    Options:
        None
    """

    _name = 'duiadns.net'
    _oneliner = 'Updates on https://www.duiadns.net'
    _url = 'https://ip.duiadns.net/dynamic.duia?host={0}&password={1}'

    def register(self, log, hostname, ip, options):
        """Implement ServicePlugin.register()."""
        password = get_netrc_auth('ip.duiadns.net')[1]
        url = self._url.format(hostname, password)
        if not ip:
            log.warn("This plugin requires an ip address.")
        if ip and ip.v4:
            url += "&ip4=" + ip.v4
        if ip and ip.v6:
            url += "&ip6=" + ip.v6
        html = get_response(log, url)
        parser = DuiadnsParser()
        parser.feed(html)
        if 'error' in parser.data or 'Ipv4' not in parser.data:
            raise ServiceError('Cannot parse server reply (see debug log)')
        log.info('New ip address: ' + parser.data['Ipv4'])
