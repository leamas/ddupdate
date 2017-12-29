
''' Update DNS data for dynamically ip addresses  '''

import argparse
import configparser
import logging
import math
import os
import os.path
import stat
import sys
import time

from straight.plugin import load

from ddupdate.plugins_base import IpPlugin, IpLookupError
from ddupdate.plugins_base import UpdatePlugin, UpdateError

if 'XDG_CACHE_HOME' in os.environ:
    CACHE_DIR = os.environ['XDG_CACHE_HOME']
else:
    CACHE_DIR = os.path.expanduser('~/.cache')

DEFAULTS = {
    'hostname': 'host.nowhere.net',
    'ip-plugin': 'default-if',
    'service-plugin': 'dry-run',
    'loglevel': 'info',
    'options': None,
    'ip-cache': os.path.join(CACHE_DIR, 'ddupdate'),
    'force': False
}


def ip_cache_setup(opts):
    ''' Ensure that our cache directory exists, return cache file path '''
    if not os.path.exists(opts.ip_cache):
        os.makedirs(opts.ip_cache)
    return os.path.join(opts.ip_cache, opts.service_plugin + '.ip')


def ip_cache_clear(opts, log):
    ''' Remove the cache file for actual service plugin in opts. '''
    path = ip_cache_setup(opts)
    if not os.path.exists(path):
        return
    log.debug("Removing cache file: " + path)
    os.unlink(path)


def ip_cache_data(opts, default=("0.0.0.0", 100000)):
    ''' Return  a (address, cache age in minute) tuples. If not existing,
    the default value is returned.
    '''
    path = ip_cache_setup(opts)
    if not os.path.exists(path):
        return default
    mtime = os.stat(path)[stat.ST_MTIME]
    now = time.time()
    delta = math.floor((now - mtime) / 60)
    with open(path) as f:
        addr = f.read().strip()
    return addr, delta


def ip_cache_set(opts, addr):
    ''' Set the cached address to string addr. '''

    path = ip_cache_setup(opts)
    addr = addr if addr else "0.0.0.0"
    with open(path, "w") as f:
        f.write(addr.strip())


def here(path):
    ' Return path added to current dir for __file__. '
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), path)


def parse_conffile(log):
    ' Parse config file path, returns verified path or None. '
    path = os.path.expanduser('~/.config/ddupdate.conf')
    if not os.path.exists(path):
        path = '/etc/ddupdate.conf'
    for i in range(len(sys.argv)):
        arg = sys.argv[i]
        if arg.startswith('-c') or arg.startswith('--conf'):
            if arg.startswith('-c') and len(arg) > 2:
                path = arg[2:]
            elif '=' in arg:
                path = arg.split('=')[1]
            elif i < len(sys.argv) - 1:
                path = sys.argv[i + 1]
            else:
                # Trust that the regular parsing handles the error.
                return None
    if not os.access(path, os.R_OK):
        log.warning("Cannot open config file '%s' for read", path)
        return None
    return path


def parse_config(path, log):
    ' Parse config file, return fully populated dict of key-values '
    results = {}
    config = configparser.ConfigParser()
    config.read(path)
    if 'update' not in config:
        log.warning(
            'No [update] section found in %s, file ignored', path)
        items = {}
    else:
        items = config['update']
    for key in DEFAULTS:
        if key not in items:
            results[key] = DEFAULTS[key]
        else:
            results[key] = items[key]
    return results


def get_parser(conf):
    ''' Construct the argparser. '''
    parser = argparse.ArgumentParser(
        prog='ddupdate',
        add_help=False,
        description="Tool to update DNS data for dynamic ip addresses")
    normals = parser.add_argument_group()
    normals.title = "Normal operation options"
    normals.add_argument(
        "-H", "--hostname", metavar="host",
        help='Hostname to update [host.nowhere.net]',
        default=conf['hostname'])
    normals.add_argument(
        "-s", "--service-plugin", metavar="plugin",
        help='Service plugin used to actually update a dns hostname address',
        default=conf['service-plugin'])
    normals.add_argument(
        "-i", "--ip-plugin", metavar="plugin",
        help='Ip plugin used to obtain the ip address to use',
        default=conf['ip-plugin'])
    normals.add_argument(
        "-c", "--config-file", metavar="path",
        help='Config file with default values for all options'
        + ' [~/.config/dupdate.conf:/etc/dupdate.conf]',
        dest='config_file', default='/etc/ddupdate.conf')
    normals.add_argument(
        "-L", "--loglevel", metavar='level',
        choices=['error', 'warning', 'info', 'debug'],
        help='Amount of printed diagnostics [warning]',
        default=conf['loglevel'])
    normals.add_argument(
        "-o", "--option", metavar="plugin option",
        help='Plugin option (enter multiple times if required)',
        dest='options', action='append')
    others = parser.add_argument_group()
    others.title = "Other options"
    others.add_argument(
        "-l", "--list-plugins", metavar="kind",
        choices=['services', 'ip-plugins', 'all'],
        help='List plugins of given kind: '
        + 'ip-plugins, services or all  [all]',
        const='all', nargs='?')
    others.add_argument(
        "-f", "--force",
        help='Force run even if the cache is fresh',
        default=False, action='store_true')
    others.add_argument(
        "-h", "--help", metavar="plugin",
        help='Print overall help or help for given plugin',
        nargs='?', const='-')
    others.add_argument(
        "-v", "--version",
        help='Print ddupdate version and exit',
        action='version')
    return parser


def parse_options(conf):
    ''' Parse command line using conf as defaults, return namespace. '''
    level_by_name = {
        'error': logging.ERROR,
        'warn': logging.WARNING,
        'warning': logging.WARNING,
        'info': logging.INFO,
        'debug': logging.DEBUG,
    }
    parser = get_parser(conf)
    parser.version = "0.0.3"
    opts = parser.parse_args()
    if opts.help == '-':
        parser.print_help()
        sys.exit(0)
    if not opts.options:
        opts.options = conf['options']
    opts.loglevel = level_by_name[opts.loglevel]
    opts.ip_cache = conf['ip-cache']
    return opts


def log_setup():
    ' Setup the module log. '
    log = logging.getLogger('ddupdate')
    log.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    log.addHandler(handler)
    return log


def log_options(log, args):
    ' Print some info on seledted options. '
    log.info("Loglevel: " + logging.getLevelName(args.loglevel))
    log.info("Using hostname: " + args.hostname)
    log.info("Using ip address plugin: " + args.ip_plugin)
    log.info("Using service plugin: " + args.service_plugin)
    log.info("Plugin options: "
             + (' '.join(args.options) if args.options else ''))


def load_plugins(path, log):
    ''' Load ip and service plugins into dicts keyed by name. '''
    sys.path.insert(0, path)
    getters = load('plugins', subclasses=IpPlugin)
    getters = getters.produce()
    getters_by_name = {plug.name(): plug for plug in getters}
    setters = load('plugins', UpdatePlugin)
    setters = setters.produce()
    setters_by_name = {plug.name(): plug for plug in setters}
    sys.path.pop(0)
    log.debug("Loaded %d address and %d service plugins",
              len(getters), len(setters))
    return getters_by_name, setters_by_name


def list_plugins(ip_plugins, service_plugins, kind):
    ''' List all loaded plugins (noreturn). '''
    if kind == 'all' or kind.startswith('i'):
        for name, plugin in sorted(ip_plugins.items()):
            print("%-20s %s" % (name, plugin.oneliner()))
    if kind == 'all' or kind.startswith('s'):
        for name, plugin in sorted(service_plugins.items()):
            print("%-20s %s" % (name, plugin.oneliner()))
    sys.exit(0)


def plugin_help(ip_plugins, service_plugins, plugid):
    ''' print full help for given plugin (noreturn).'''
    if plugid in ip_plugins:
        plugin = ip_plugins[plugid]
    elif plugid in service_plugins:
        plugin = service_plugins[plugid]
    else:
        print("No help available (nu such plugin?): " + plugid)
        sys.exit(2)
    print("Name: " + plugin.name())
    print("Source: " + plugin.sourcefile() + "\n")
    print(plugin.info())

    sys.exit(0)


def build_load_path(log):
    ''' Return list of paths to load plugins from. '''
    paths = []
    path = os.path.expanduser('~/.local/share')
    if 'XDG_DATA_HOME' in os.environ:
        path = os.environ['XDG_DATA_HOME']
    paths.append(path)
    syspaths = "/usr/local/share:/usr/share"
    if 'XDG_DATA_DIRS' in os.environ:
        syspaths = os.environ['XDG_DATA_DIRS']
    paths.extend(syspaths.split(':'))
    paths = [os.path.join(p, 'ddupdate') for p in paths]
    paths.insert(0, os.getcwd())
    log.debug('paths :%s', ':'.join(paths))
    return paths


def main():
    ''' Indeed: main function. '''
    ip_plugins = {}
    service_plugins = {}
    log = log_setup()
    conffile_path = parse_conffile(log)
    conf = parse_config(conffile_path, log) if conffile_path else DEFAULTS
    opts = parse_options(conf)
    log.handlers[0].setLevel(opts.loglevel)
    log_options(log, opts)
    load_paths = build_load_path(log)
    for path in load_paths:
        getters, setters = load_plugins(path, log)
        ip_plugins.update(getters)
        service_plugins.update(setters)
    if opts.help and opts.help != '-':
        plugin_help(ip_plugins, service_plugins, opts.help)
    if opts.list_plugins:
        list_plugins(ip_plugins, service_plugins, opts.list_plugins)
    if opts.ip_plugin not in ip_plugins:
        log.error("No such ip plugin: %s", opts.ip_plugin)
        sys.exit(2)
    try:
        ip = ip_plugins[opts.ip_plugin].run(opts, log)
    except IpLookupError as err:
        log.error("Cannot obtain ip address: %s", err)
        sys.exit(3)
    if ip == "0.0.0.0":
        log.info("Using ip address provided by update service")
        ip = None
    else:
        log.info("Using ip address: " + ip)
    if opts.force:
        ip_cache_clear(opts, log)
    addr, age = ip_cache_data(opts)
    if opts.service_plugin not in service_plugins:
        log.error("No such service plugin: %s", opts.service_plugin)
        sys.exit(2)
    service_plugin = service_plugins[opts.service_plugin]
    if age < service_plugin.ip_cache_ttl() and (addr == ip or not ip):
        log.info("Update inhibited, cache is fresh (%d min)", age)
        sys.exit(0)
    try:
        service_plugin.run(opts, log, ip)
    except UpdateError as err:
        log.error("Cannot update DNS data: %s", err)
    else:
        ip_cache_set(opts, ip)
        log.info("Update OK")


if __name__ == '__main__':
    main()


# vim: set expandtab ts=4 sw=4:
