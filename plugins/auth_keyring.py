"""Implement credentials lookup using python3-keyring.

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

# pylint: disable=wrong-import-position

from ddupdate.ddplugin import AuthPlugin, AuthError
try:
    import keyring
    import keyring.errors
except (ModuleNotFoundError, ImportError):
    raise AuthError(KEYRING_MISSING_MSG) from None


class AuthKeyring(AuthPlugin):
    """Implement credentials lookup using python3-keyring.

    This is a reasonably secure way to handle the passwords. Before actually
    accessing the passwords the keyring must be unlocked. This makes this
    backend less suited to servers but is no problem on for example a
    notebook.

    Prior to 0.7.1 all passwords was stored in the .netrc file. See the
    ddupdate-netrc-to-keyring tool for migrating passwords from .netrc to
    the keyring backend.
    """

    _name = 'keyring'
    _oneliner = 'Store credentials in the system keyring'
    __version__ = '0.7.1'

    def get_auth(self, machine):
        """Implement AuthPlugin::get_auth()."""
        try:
            credentials = keyring.get_password('ddupdate', machine.lower())
            if not credentials:
                raise AuthError("Cannot get authentication for: " + machine)
            credentials = credentials.split('\t')
        except keyring.errors.KeyringError as err:
            raise AuthError("Cannot obtain credentials for: " + machine) \
                from err
        if len(credentials) != 2:
            raise AuthError("Cannot parse credentials for: " + machine)
        if credentials[0] == 'api-key':
            credentials[0] = None
        return credentials[0], credentials[1]

    def set_password(self, machine, username, password):
        """Implement AuthPlugin::set_password()."""
        if not username:
            username = 'api-key'
        credentials = username + '\t' + password
        try:
            keyring.set_password('ddupdate', machine.lower(), credentials)
        except keyring.errors.KeyringError as err:
            raise AuthError("Cannot set credentials for: " + machine) from err
