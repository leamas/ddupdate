''' ddclient plugin base classes and common code. '''

import inspect
import os.path

import urllib.request
from urllib.parse import urlencode

from socket import timeout as timeoutError
from netrc import netrc


def http_basic_auth_setup(url, host):
    ''' Setup urllib to provide user/pw from netrc on url. '''
    user, password = get_netrc_auth(host)
    pwmgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    pwmgr.add_password(None, url, user, password)
    auth_handler = urllib.request.HTTPBasicAuthHandler(pwmgr)
    opener = urllib.request.build_opener(auth_handler)
    urllib.request.install_opener(opener)


def dict_of_opts(options):
    ''' Convert list of options to a dict. '''
    if not options:
        return {}
    result = {}
    for opt in options:
        if '=' in opt:
            key, value = opt.split('=')
            result[key] = value
        else:
            result[opt] = True
    return result


def get_response(log, url, to=120, data=None):
    '''
    Read from url and return html. If data is not None, this makes
    a http post request wuth the data, a dict, as form data. Otherwise,
    it is a http get.

    Raises UpdateError if return code is != 200 or timeout.
    '''
    log.debug("Trying url: %s", url)
    form_data = urlencode(data).encode() if data else None
    if data:
        log.debug("Posting data: " + form_data.decode('ascii'))
    try:
        with urllib.request.urlopen(url, form_data, timeout=to) as response:
            code = response.getcode()
            html = response.read().decode('ascii')
    except timeoutError:
        raise UpdateError("Timeout reading %s" % url)
    except urllib.error.HTTPError as err:
        raise UpdateError("Error reading %s :%s" % (url, err))
    log.debug("Got response (%d) : %s", code, html)
    if code != 200:
        raise UpdateError("Cannot update, response code: %d", code)
    return html


def get_netrc_auth(machine):
    ''' Return a (user, password) tuple based on ~/-netrc or /etc/netrc. '''
    if os.path.exists(os.path.expanduser('~/.netrc')):
        path = os.path.expanduser('~/.netrc')
    elif os.path.exists('/etc/netrc'):
        path = '/etc/netrc'
    auth = netrc(path).authenticators(machine)
    if not auth[2]:
        raise UpdateError("No password found for " + machine)
    return auth[0], auth[2]


class IpAddr(object):
    ''' An (ip4, ipv6) collection. '''

    def __init__(self, ipv4=None, ipv6=None):
        self.v4 = ipv4
        self.v6 = ipv6

    def str(self):
        ''' Standard str() returns a printable representation. '''
        s1 = self.v4 if self.v4 else 'None'
        s2 = self.v6 if self.v6 else 'None'
        return '[%s, %s]' % (s1, s2)

    def __eq__(self, obj):
        if not isinstance(obj, IpAddr):
            return False
        return obj.v4 == self.v4 and obj.v6 == self.v6

    def __hash__(self):
        return hash(self.v4, self.v6)

    def empty(self):
        ''' Check if any address is set. '''
        return self.v4 is None and self.v6 is None

    def parse_ifconfig_output(self, text):
        ''' Parse ifconfig <dev> or ip address show dev <dev> output. '''
        use_next4 = False
        use_next6 = False
        for word in text.split():
            if use_next4:
                self.v4 = word.split('/')[0]
            if use_next6:
                self.v6 = word.split('/')[0]
            use_next4 = word == 'inet'
            use_next6 = word == 'inet6'
        if self.empty():
            raise IpLookupError("Cannot find address for %s, giving up", text)


class IpLookupError(Exception):
    """ General error in IpPlugin """

    def __init__(self, value, exitcode=1, silent=False):
        Exception.__init__(self, value)
        self.value = value
        self.exitcode = exitcode
        self.silent = silent
        self.show_logs = True

    def __str__(self):
        """ Represent the error. """
        return repr(self.value)


class UpdateError(IpLookupError):
    """ General error in UpdatePlugin """
    pass


class AbstractPlugin(object):
    ''' Abstract base for all plugins. '''

    _name = None
    _oneliner = 'No info found'
    __version__ = '0.0.6'

    def oneliner(self):
        ''' Return oneliner describing the plugin. '''
        return self._oneliner

    def info(self):
        ''' Return full, formatted user info; in particular, options
        used.
        '''
        return inspect.getdoc(self)

    def name(self):
        ''' Returns short name (no spaces). Returning None implies
        not-a-plugin.
        '''
        return self._name

    def version(self):
        ''' Return plugin version. '''
        return self.__version__

    # pylint: disable=unused-argument,no-self-use
    def sourcefile(self):
        ''' Return module sourcefile. '''
        return __file__


class IpPlugin(AbstractPlugin):
    ''' An abstract plugin obtaining the ip address. '''

    def get_ip(self, log, options):
        ''' Given the list of --option options and a log, return
            an IpAddr or None. Raises IpLookupError on errors.
        '''
        raise NotImplementedError("Attempt to invoke abstract get_ip()")


class UpdatePlugin(AbstractPlugin):
    ''' An abstract plugin doing the actual update work using a service. '''

    _ip_cache_ttl = 120    # 2 hours, address cache timeout
    _socket_to = 120       # 2 min, timeout reading host

    def __init__(self):
        AbstractPlugin.__init__(self)

    def ip_cache_ttl(self):
        ''' Return time when ip cache expires, in minutes from creation.
        '''
        return self._ip_cache_ttl

    def register(self, log, hostname, ip, options):
        ''' Given configuration, address and log do the actual update.
            Parameters:
              - log: standard python log instance
              - hostname - string, the DNS name to register
              - ip: Address to register
              - opts: list of --option values.
            Raises:
              - UpdateError on errors.
        '''
        raise NotImplementedError("Attempt to invoke abstract register()")
