'''
ddupdate plugin updating data on now-dns.com.

See: ddupdate(8)

'''
from netrc import netrc
import base64
import urllib.request
import urllib.error

from ddupdate.plugins_base import UpdatePlugin, UpdateError


class NowDnsPlugin(UpdatePlugin):
    '''
    Update a dns entry on now-dns.com. As usual, any host updated must
    first be defined in the web UI. Providing an ip address is optional
    but supported; the ip-disabled plugin can be used.

    now-dns uses an odd authentication without challenge. Using wget,
    the --auth-no-challenge  is required. This code copes with this
    mess.

    netrc: Use a line like
        machine  now-dns.com user <username> password <password>

    Options:
        None
    '''
    _name = 'now-dns'
    _oneliner = 'Updates DNS data on now-dns.com'
    _url = 'https://now-dns.com/update?hostname={0}'

    def run(self, config, log, ip=None):

        auth = netrc().authenticators('now-dns.com')
        if not auth or not auth[2]:
            raise UpdateError(
                "No password for now-dns.com found in .netrc")
        url = self._url.format(config.hostname)
        if ip:
            url += '&myip=' + ip
        credentials = '%s:%s' % (auth[0], auth[2])
        encoded_credentials = base64.b64encode(credentials.encode('ascii'))
        req = urllib.request.Request(url)
        req.add_header('Authorization',
                       'Basic %s' % encoded_credentials.decode("ascii"))
        try:
            with urllib.request.urlopen(req) as response:
                code = response.getcode()
                html = response.read().decode('ascii').strip()
        except urllib.error.HTTPError as err:
            raise UpdateError("Error reading %s :%s" % (url, err))
        if code != 200:
            raise UpdateError('Bad server reply code: ' + code)
        if html not in ['good', 'nochg']:
            raise UpdateError('Bad server reply: ' + html)
        log.info("Server reply: " + html)
