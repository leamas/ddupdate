"""
ddupdate plugin API.

A plugin is either a service plugin or an address plugin.

Service plugins register the ip address with a dynamic dns service provider.
They implement the ServicePlugin abstract interface. Naming of these plugins
is normally based on the website used to register since these by definition
are unique

Address plugins determines the ip address to register. They implement the
abstract AddressPlugin interface.

All plugins shares the AbstractPlugin interface. This handles general
aspects like name and documentation.

The module also provides some utility functions used in plugins.

"""

import inspect
import os.path

import urllib.request
from urllib.parse import urlencode, urlparse

from socket import timeout as timeoutError
from netrc import netrc

URL_TIMEOUT = 120  # Default timeout in get_response()


def http_basic_auth_setup(url, host=None):
    """
    Configure urllib to provide basic authentication.

    Parameters:
        - url: string, the url to connect to.
        - host: string, hostname looked up in .netrc. Defaults to
          to hostname part of url.

    """
    if not host:
        host = urlparse(url).hostname
    user, password = get_netrc_auth(host)
    pwmgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    pwmgr.add_password(None, url, user, password)
    auth_handler = urllib.request.HTTPBasicAuthHandler(pwmgr)
    opener = urllib.request.build_opener(auth_handler)
    urllib.request.install_opener(opener)


def dict_of_opts(options):
    """
    Convert list of plugin options from the arg_parser to a dict.

    Single keyword options are inserted as dict[keyword] = True,
    key=val options are inserted as dict[key] = val.

    """
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


def get_response(log, url, **kwargs):
    """
    Get data from server at given url.

    Parameters:
      - log: Standard python log instance
      - url: The url to make a post/get request to.
      - kwargs: Keyword arguments.
         - data: dict of post data. If data != None, get_response makes a
           http POST request, otherwise a http GET.
         - timeout: int, timeout in seconds. Defaults to 120.
    Returns:
      - Text read from url.
    Raises:
      - ServiceError if return code is != 200, httpError or timeout.

    """
    log.debug("Trying url: %s", url)
    data = urlencode(kwargs['data']).encode() if 'data' in kwargs else None
    to = kwargs['timeout'] if 'timeout' in kwargs else URL_TIMEOUT
    if data:
        log.debug("Posting data: " + data.decode('ascii'))
    try:
        with urllib.request.urlopen(url, data, timeout=to) as response:
            code = response.getcode()
            html = response.read().decode('ascii')
    except timeoutError:
        raise ServiceError("Timeout reading %s" % url)
    except (urllib.error.HTTPError, urllib.error.URLError) as err:
        raise ServiceError("Error reading %s :%s" % (url, err))
    log.debug("Got response (%d) : %s", code, html)
    if code != 200:
        raise ServiceError("Cannot update, response code: %d" % code)
    return html


def get_netrc_auth(machine):
    """
    Retrieve data from  ~/-netrc or /etc/netrc.

    Parameters:
      - machine: key while searching in netrc file.
    Returns:
      - A (user, password) tuple. User might be None.
    Raises:
      - ServiceError if .netrc or password is not found.
    See:
      - netrc(5)

    """
    if os.path.exists(os.path.expanduser('~/.netrc')):
        path = os.path.expanduser('~/.netrc')
    elif os.path.exists('/etc/netrc'):
        path = '/etc/netrc'
    else:
        raise ServiceError("Cannot locate the netrc file (see manpage).")
    auth = netrc(path).authenticators(machine)
    if not auth:
        raise ServiceError("No .netrc data found for " + machine)
    if not auth[2]:
        raise ServiceError("No password found for " + machine)
    return auth[0], auth[2]


class IpAddr(object):
    """A (ipv4, ipv6) container."""

    def __init__(self, ipv4=None, ipv6=None):
        """
        Construct a fresh object.

        Parameters:
          - ipv4: string, the ipv4 address in dotted notation.
          - ipv6: string, the ipv6 address in colon-hex notation.

        """
        self.v4 = ipv4
        self.v6 = ipv6

    def __str__(self):
        return repr([self.v4, self.v6])

    def __eq__(self, obj):
        if not isinstance(obj, IpAddr):
            return False
        return obj.v4 == self.v4 and obj.v6 == self.v6

    def __hash__(self):
        return hash(self.v4, self.v6)

    def empty(self):
        """Check if any address is set."""
        return self.v4 is None and self.v6 is None

    def parse_ifconfig_output(self, text):
        """
        Update v4 and v6 attributes by parsing ifconfig(8) or ip(8) output.

        Parameters:
          - text: string, ifconfig <dev> or ip address show dev <dev> output.
        Raises:
          - AddressError if no address can be found in text

        """
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
            raise AddressError("Cannot find address for %s, giving up" % text)


class AddressError(Exception):
    """General error in AddressPlugin."""

    def __init__(self, value, exitcode=1):
        """
        Construct the error.

        Parameters:
          - value: string, error message
          - exitcode: int, aimed as sys.exit() argument.

        """
        Exception.__init__(self, value)
        self.value = value
        self.exitcode = exitcode

    def __str__(self):
        """Represent the error."""
        return repr(self.value)


class ServiceError(AddressError):
    """General error in ServicePlugin."""

    pass


class AbstractPlugin(object):
    """Abstract base for all plugins."""

    _name = None
    _oneliner = 'No info found'
    __version__ = '0.6.3'

    def oneliner(self):
        """Return oneliner describing the plugin."""
        return self._oneliner

    def info(self):
        """
        Return full, formatted user info; in particular, options used.

        Default implementation returns class docstring.
        """
        return inspect.getdoc(self)

    def name(self):
        """
        Retrieve the plugin short, unique id (no spaces).

        Returning None implies not-a-plugin. Names must be unique.
        Also module name (i. e., filename) must be unique.
        """
        return self._name

    def version(self):
        """Return plugin version."""
        return self.__version__


class AddressPlugin(AbstractPlugin):
    """An abstract plugin obtaining the ip address."""

    def get_ip(self, log, options):
        """
        Return ip address to register.

        Parameters:
            - log: Standard python log instance.
            - options: List of --address-option options.

        Returns:
            - IpAddr or None

        Raises:
            AddressError.

        """
        raise NotImplementedError("Attempt to invoke abstract get_ip()")


class ServicePlugin(AbstractPlugin):
    """Abstract plugin doing the actual update work using a service."""

    _ip_cache_ttl = 120    # 2 hours, address cache timeout

    def __init__(self):
        """Default, empty constructor."""
        AbstractPlugin.__init__(self)

    def ip_cache_ttl(self):
        """Return time when ip cache expires, in minutes from creation."""
        return self._ip_cache_ttl

    def register(self, log, hostname, ip, options):
        """
        Do the actual update.

        Parameters:
        - log: Standard python log instance
        - hostname: string, the DNS name to register
        - ip: IpAddr, address to register
        - opts: List of --service-option values.

        Raises:
        - ServiceError on errors.

        """
        raise NotImplementedError("Attempt to invoke abstract register()")
