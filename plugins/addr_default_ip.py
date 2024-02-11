"""
ddupdate plugin to obtain ip address.

See: ddupdate(8)
"""

import subprocess

from ddupdate.ddplugin import AddressPlugin, AddressError, IpAddr, dict_of_opts


def find_device(words):
    """Return first word following 'dev' or None."""
    found = False
    for word in words:
        if word == "dev":
            found = True
        elif found:
            return word
    return None


class DefaultIfPLugin(AddressPlugin):
    """
    Locates the default interface.

    Digs in the routing tables and returns it's address using linux-specific
    code based on the ip utility which must be in $PATH

    Options used:
       link
    """

    _name = 'default-if'
    _oneliner = 'Get ip address from default interface (linux)'

    def get_ip(self, log, options):
        """
        Get default interface using ip route and address using ifconfig.
        """
        opts = dict_of_opts(options)
        if_ = None
        remote = opts.get('remote', None)
        if remote:
            key = opts.get('key', None)
            if key:
                prefix = f"ssh -i {key} {remote} "
            else:
                prefix = f"ssh {remote} "
        else:
            prefix = ""
        for line in subprocess.getoutput(''.join((prefix, 'ip route'))).split('\n'):
            words = line.split()
            if words[0] == 'default':
                if_ = find_device(words)
                break
        if if_ is None:
            raise AddressError("Cannot find default interface, giving up")
        address = IpAddr()
        output = subprocess.getoutput(''.join((prefix, 'ip address show dev ', if_)))
        address.parse_ifconfig_output(output, opts.get('link', 'false'))
        return address
