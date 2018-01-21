"""
ddupdate plugin to obtain ip address.

See: ddupdate(8)
"""

import subprocess

from ddupdate.ddplugin import AddressPlugin, AddressError, IpAddr


class DefaultIfPLugin(AddressPlugin):
    """
    Locates the default interface.

    Digs in the routing tables and returns it's address using linux-specific
    code based on the ip utility which must be in $PATH

    Options used: none
    """

    _name = 'default-if'
    _oneliner = 'Get ip address from default interface (linux)'

    def get_ip(self, log, options):
        """
        Get default interface using ip route and address using ifconfig.
        """
        if_ = None
        for line in subprocess.getoutput('ip route').split('\n'):
            words = line.split()
            if words[0] == 'default':
                if_ = words[4]
                break
        if if_ is None:
            raise AddressError("Cannot find default interface, giving up")
        address = IpAddr()
        output = subprocess.getoutput('ip address show dev ' + if_)
        address.parse_ifconfig_output(output)
        return address
