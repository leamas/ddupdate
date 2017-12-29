''' ddclient plugin base classes and common code. '''

import inspect
import os.path
import urllib.request

from urllib.parse import urlencode

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


def get_response(log, url, data=None):
    '''
    Read from url and return html. If data is not None, this makes
    a http post request wuth the data, a dict, as form data. Otherwise,
    it is a http get.

    Raises UpdateError if return code is != 200.
    '''
    log.debug("Trying url: %s", url)
    form_data = urlencode(data).encode() if data else None
    if data:
        log.debug("Posting data: " + form_data.decode('ascii'))
    try:
        with urllib.request.urlopen(url, form_data) as response:
            code = response.getcode()
            html = response.read().decode('ascii')
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
    __version__ = '0.0.3'

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

    def run(self, config, log, ip=None):
        ''' Run the actual module work. '''
        raise NotImplementedError("Attempt to invoke abstract run()")


class IpPlugin(AbstractPlugin):
    ''' An abstract plugin obtaining the ip address. '''

    def run(self, config, log, ip=None):
        ''' Given a configuration namespace and a log, return ip address.
            Raises IpLookupError on errors.
        '''
        raise NotImplementedError("Attempt to invoke abstract run()")


class UpdatePlugin(AbstractPlugin):
    ''' An abstract plugin doing the actual update work using a service. '''

    _ip_cache_ttl = 120     # 2 hours

    def ip_cache_ttl(self):
        ''' Return time when ip cache expires, in minutes from creation.
        '''
        return self._ip_cache_ttl

    def run(self, config, log, ip=None):
        ''' Given configuration, address and log do the actual update.
            Most (not all) services doesnt't need an address.
            Raises UpdateError on errors.
        '''
        raise NotImplementedError("Attempt to invoke abstract run()")
