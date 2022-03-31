"""
Implement credentials lookup using the ~/.netrc(5) file
"""

from netrc import netrc
import os.path

from ddupdate.ddplugin import AuthPlugin, AuthError

class AuthNetrc(AuthPlugin):
    """ Get credentials stored in the .netrc(5) file """
    _name = 'netrc'
    _oneliner = 'Get credentials using .netrc'
    __version__ = '0.6.6'


    def get_auth(self, machine):

        if os.path.exists(os.path.expanduser('~/.netrc')):
            path = os.path.expanduser('~/.netrc')
        elif os.path.exists('/etc/netrc'):
            path = '/etc/netrc'
        else:
            raise AuthError("Cannot locate the netrc file (see manpage).")
        auth = netrc(path).authenticators(machine)
        if not auth:
            raise AuthError("No .netrc data found for " + machine)
        if not auth[2]:
            raise AuthError("No password found for " + machine)
        return auth[0], auth[2]
    


