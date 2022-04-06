"""
Implement credentials lookup using the ~/.netrc(5) file.
"""
import base64
import binascii
from netrc import netrc
import os.path

from ddupdate.ddplugin import AuthPlugin, AuthError


class AuthNetrc(AuthPlugin):
    """Get credentials stored in the .netrc(5) file.

    This is the original storage used before 0.7.1. It is less secure
    than for example the keyring but is convenient and, since it does
    not require anything to be unlocked, a good candidate for servers.
    """

    _name = 'netrc'
    _oneliner = 'Store credentials in .netrc(5)'
    __version__ = '0.7.1'

    def get_auth(self, machine):
        """Implement AuthPlugin::get_auth()."""
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
        try:
            pw = base64.b64decode(auth[2]).decode('ascii')
        except (binascii.Error, UnicodeDecodeError):
            pw = auth[2]
        return auth[0], pw

    def set_password(self, machine, username, password):
        """Implement AuthPlugin::set_password()."""

        def is_matching_entry(line):
            """Return True if line contains 'machine' machine'."""
            words = line.split(' ')
            for i in range(0, len(words) - 1):
                if words[i] == 'machine' \
                        and words[i + 1].lower() == machine.lower():
                    return True
            return False

        def new_entry():
            """Return new entry."""
            pw = base64.b64encode(password.encode('utf-8')).decode('ascii')
            line = 'machine ' + machine.lower()
            if username:
                line += ' login ' + username
            line += ' password ' + pw
            return line

        path = os.path.expanduser('~/.netrc')
        lines = []
        if os.path.exists(path):
            with open(path, 'r') as f:
                lines = f.readlines()
        lines = [line for line in lines if not is_matching_entry(line)]
        lines.append(new_entry())
        lines = [line.strip() + "\n" for line in lines]
        with open(path, 'w') as f:
            f.writelines(lines)
