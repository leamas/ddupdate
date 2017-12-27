'''
ddupdate plugin providing a null ip address.

See: ddupdate(8)

'''

from plugins.plugins_base import IpPlugin


class IpDisabledPlugin(IpPlugin):
    '''
    ddupdate plugin providing a null ip address, to be used when the
    update service determines the address

    Options: nothing
    netrc: Nothing
    '''
    _name = 'ip-disabled'
    _oneliner = 'Force update service to provide ip address'

    def run(self, config, log, ip=None):
        return "0.0.0.0"
