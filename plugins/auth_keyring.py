"""
Implement credentials lookup using python3-keyring. 

The keyring just provides a basic username -> password lookup. However,
the get_auth() call should possibly return both username and password
for a given machine. To that end, the value stored for each hostname
is 'username<tab>password'

For hosts using just an api key i. e., without a username the username
field is set to 'api-key'
"""

KEYRING_MISSING_MSG = """
python keyring module not found. Please install python3-keyring
using package manager or the keyring package using pip.
"""

from ddupdate.ddplugin import AuthPlugin, AuthError

try:
    import keyring
except (ModuleNotFoundError, ImportError):
    raise(AuthError(KEYRING_MISSING_MSG))

class AuthKeyring(AuthPlugin):
    """ Implement credentials lookup using python3-keyring """

    _name = 'keyring'
    _oneliner = 'Get credentials stored in the system keyring'
    __version__ = '0.7.0'

    def get_auth(self, machine):
        try:
            credentials = keyring.get_password('ddupdate', machine).split('\t')
        except KeyringError:
            raise AuthError("Cannot obtain credentials for: " + machine)
        if len(credentials) != 2:
            raise AuthError("Cannot parse credentials for: " + machine)
        if credentials[0] == 'api-key':
            credentials[0] = None
        return credentials[0], credentials[1]

    def set_auth(self, machine, username, password):
        if not username:
            username = 'api-key'
        credentials = username + '\t' + password
        try:
            keyring.set_password('ddupdate', machine, credentials)
        except KeyringError:
            raise AuthError("Cannot set credentials for: " + machine)
