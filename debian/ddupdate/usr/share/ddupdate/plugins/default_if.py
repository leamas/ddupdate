'''
ddupdate plugin to obtain ip address

See: ddupdate(8)
'''

import subprocess

from plugins.plugins_base import IpPlugin, IpLookupError


class DefaultIfPLugin(IpPlugin):
    '''
    Locates the default interface by digging in the routing tables
    and returmns it's address using linux-specific code.

    Options used: none
    '''
    _name = 'default-if'
    _oneliner = 'Get ip address from default interface (linux)'

    def run(self, config, log, ip=None):
        '''
        Get default interface using ip route and address using ifconfig
        '''
        if_ = None
        for line in subprocess.getoutput('ip route').split('\n'):
            words = line.split()
            if words[0] == 'default':
                if_ = words[4]
                break
        if if_ is None:
            raise IpLookupError("Cannot find default interface, giving up")
        use_next = False
        for word in subprocess.getoutput('ip address show dev ' + if_).split():
            if use_next:
                return word.split('/')[0]
            use_next = word == 'inet'
        raise IpLookupError("Cannot find address for %s, giving up", if_)
