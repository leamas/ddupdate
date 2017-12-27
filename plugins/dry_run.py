'''
ddupdate plugin making the actual update work

See: ddupdate(8)
'''

from plugins.plugins_base import UpdatePlugin


class DryRunPlugin(UpdatePlugin):
    '''
    Prints the ip address obtained and the configured hostname
    to update, but does not invoke any action. Primarely a
    debug tool.

    Options used: none
    '''
    _name = 'dry-run'
    _oneliner = 'Debug dummy update plugin'

    def run(self, config, log, ip=None):
        ''' Run the actual module work. '''
        print("dry-run: Using address %s and hostname %s"
              % (ip, config.hostname))
