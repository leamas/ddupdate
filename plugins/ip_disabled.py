'''
ddupdate plugin providing a null ip address.

See: ddupdate(8)

'''

from ddupdate.plugins_base import IpPlugin, IpAddr


class IpDisabledPlugin(IpPlugin):
    '''
    ddupdate plugin providing a null ip address, to be used when the
    update service determines the address

    Options:
        None
    netrc:
        None
    '''
    _name = 'ip-disabled'
    _oneliner = 'Force update service to provide ip address'

    def get_ip(self, log, options):
        return IpAddr()
