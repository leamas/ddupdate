"""
ddupdate plugin updating data on domains.google.com.

See: ddupdate(8)
See: https://support.google.com/domains/answer/6147083?hl=en

"""
import urllib.parse
import urllib.request

from ddupdate.ddplugin import ServiceError, ServicePlugin
from ddupdate.ddplugin import AuthError, get_response, get_netrc_auth


# See https://github.com/leamas/ddupdate/pull/56
# and https://github.com/leamas/ddupdate/issues/52
# for why these functions are specialized here.

# pylint: disable=duplicate-code
# broken for now: https://github.com/PyCQA/pylint/issues/214

def http_basic_auth_setup(url, *, providerhost=None, targethost=None):
    """
    Configure urllib to provide basic authentication.

    See get_auth for how providerhost and targethost
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
    user, password = get_auth(providerhost, targethost)
    pwmgr = urllib.request.HTTPPasswordMgrWithDefaultRealm()
    pwmgr.add_password(None, url, user, password)
    auth_handler = urllib.request.HTTPBasicAuthHandler(pwmgr)
    opener = urllib.request.build_opener(auth_handler)
    urllib.request.install_opener(opener)


def get_auth(providerhost, targethost=None):
    """
    Retrieve credentials from configured source.

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
      - AuthError password is not found.

    """
    if targethost is not None:
        machine1 = "%s.%s.ddupdate" % (targethost, providerhost)
        try:
            credentials = get_netrc_auth(machine1)
        except AuthError:
            credentials = get_netrc_auth(providerhost)
    else:
        credentials = get_netrc_auth(providerhost)
    return credentials


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

        url = "{}?{}".format(self._url, urllib.parse.urlencode(query))
        http_basic_auth_setup(url, targethost=hostname)
        request = urllib.request.Request(url=url, method='POST')
        html = get_response(log, request)

        code = html.split()[0]
        if code not in ['good', 'nochg']:
            raise ServiceError("Bad server reply: " + html)
