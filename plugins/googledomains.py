"""
ddupdate plugin updating data on domains.google.com.

See: ddupdate(8)
See: https://support.google.com/domains/answer/6147083?hl=en

"""
import netrc
import os.path
import urllib.parse
import urllib.request
from ddupdate.ddplugin import ServiceError, ServicePlugin, \
    get_response


# See https://github.com/leamas/ddupdate/pull/56
# and https://github.com/leamas/ddupdate/issues/52
# for why these functions are specialized here.
def http_basic_auth_setup(url, *, providerhost=None, targethost=None):
    """
    Configure urllib to provide basic authentication.

    See get_netrc_auth for how providerhost and targethost
    are resolved to credentials stored in netrc.

    Parameters:
        - url: string, the url to connect to.
        - providerhost: string, a hostname representing the provider.
          Defaults to the hostname part of url.
        - targethost: string, the host being updated.  Optional, used
          to discriminate hosts registered with different
          credentials at the same provider.
    """
    if not providerhost:
        providerhost = urllib.parse.urlparse(url).hostname
    user, password = get_netrc_auth(providerhost, targethost)
    pwmgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    pwmgr.add_password(None, url, user, password)
    auth_handler = urllib.request.HTTPBasicAuthHandler(pwmgr)
    opener = urllib.request.build_opener(auth_handler)
    urllib.request.install_opener(opener)

def get_netrc_auth(providerhost, targethost=None):
    """
    Retrieve data from  ~/-netrc or /etc/netrc.

    Will look for matching identifiers in the netrc file.

    If a targethost is passed, the first machine name we look for
    is targethost.providerhost.ddupdate, falling back to providerhost.
    If no targethost is passed, we only look for providerhost.

    Parameters:
      - providerhost: identifies the dns provider
      - targethost: optional.  Allows selecting credentials for multiple
        host names registered at the same provider.
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
    netrcdata = netrc.netrc(path)
    if targethost is not None:
        machine1 = "%s.%s.ddupdate" % (targethost, providerhost)
        auth = netrcdata.authenticators(machine1) or netrcdata.authenticators(providerhost)
    else:
        auth = netrcdata.authenticators(providerhost)
    if not auth:
        raise ServiceError("No .netrc data found for " + providerhost)
    if not auth[2]:
        raise ServiceError("No password found for " + providerhost)
    return auth[0], auth[2]


class GoogleDomainsPlugin(ServicePlugin):
    """
    Update a DNS entry on domains.google.com.

    .netrc: Use a line like:
        machine domains.google.com login <username> password <password>

    Options:
        none
    """

    _name = "domains.google.com"
    _oneliner = "Updates on https://domains.google.com"
    _url = "https://domains.google.com/nic/update"

    def register(self, log, hostname, ip, options):
        """Implement ServicePlugin.register()."""
        query = {
            'hostname': hostname,
        }

        # IP address is optional for IPv4
        if ip:
            query['myip'] = ip.v6 or ip.v4

        url="{}?{}".format(self._url, urllib.parse.urlencode(query))
        http_basic_auth_setup(url, targethost=hostname)
        request = urllib.request.Request(url=url, method='POST')
        html = get_response(log, request)

        code = html.split()[0]
        if code not in ['good', 'nochg']:
            raise ServiceError("Bad server reply: " + html)
