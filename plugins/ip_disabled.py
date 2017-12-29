'''
ddupdate plugin providing a null ip address.

See: ddupdate(8)

'''

from ddupdate.plugins_base import IpPlugin


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

    def run(self, config, log, ip=None):
        return "0.0.0.0"
