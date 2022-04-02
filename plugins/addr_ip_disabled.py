"""
ddupdate plugin providing a null ip address.

See: ddupdate(8)

"""

from ddupdate.ddplugin import AddressPlugin, IpAddr


class IpDisabledPlugin(AddressPlugin):
    """
    ddupdate plugin providing a null ip address.

    To be used when the update service determines the address

    Options:
        None
    netrc:
        None
    """

    _name = 'ip-disabled'
    _oneliner = 'Force update service to provide ip address'

    def get_ip(self, log, options):
        """Implement AddressPlugin.get_ip()."""
        return IpAddr()
