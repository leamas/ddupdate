"""Update DNS data for dynamic ip addresses."""

import argparse
import configparser
import glob
import importlib
import inspect
import logging
import math
import os
import os.path
import stat
import sys
import time
import ast

from ddupdate.ddplugin import AddressPlugin, AddressError
from ddupdate.ddplugin import ServicePlugin, ServiceError
from ddupdate.ddplugin import IpAddr

# pylint: disable=ungrouped-imports
if sys.version_info >= (3, 5):
    import importlib.util
else:
    from importlib.machinery import SourceFileLoader


if 'XDG_CACHE_HOME' in os.environ:
    CACHE_DIR = os.environ['XDG_CACHE_HOME']
else:
    CACHE_DIR = os.path.expanduser('~/.cache')

DEFAULTS = {
    'hostname': 'host.nowhere.net',
    'address-plugin': 'default-if',
    'service-plugin': 'dry-run',
    'loglevel': 'info',
    'ip-version': 'v4',
    'service-options': None,
    'address-options': None,
    'ip-cache': os.path.join(CACHE_DIR, 'ddupdate'),
    'force': False
}


class _GoodbyeError(Exception):
    """General error, implies sys.exit()."""

    def __init__(self, msg="", exitcode=0):
        Exception.__init__(self, msg)
        self.exitcode = exitcode
        self.msg = msg


def envvar_default(var, default=None):
    """Return var if found in environment, else default."""
    return os.environ[var] if var in os.environ else default


def ip_cache_setup(opts):
    """Ensure that our cache directory exists, return cache file path."""
    if not os.path.exists(opts.ip_cache):
        os.makedirs(opts.ip_cache)
    return os.path.join(opts.ip_cache, opts.service_plugin + '.ip')


def ip_cache_clear(opts, log):
    """Remove the cache file for actual service plugin in opts."""
    path = ip_cache_setup(opts)
    if not os.path.exists(path):
        return
    log.debug("Removing cache file: " + path)
    os.unlink(path)


def ip_cache_data(opts, log, default=(IpAddr(ipv4="0.0.0.0"), 100000)):
    """
    Return an (address, cache age in minute) tuple.

    If not existing, the default value is returned.
    """
    path = ip_cache_setup(opts)
    if not os.path.exists(path):
        return default
    mtime = os.stat(path)[stat.ST_MTIME]
    now = time.time()
    delta = math.floor((now - mtime) / 60)
    with open(path) as f:
        astr = f.read().strip()
    try:
        ll = ast.literal_eval(astr)
        ip = IpAddr(ipv4=ll[0], ipv6=ll[1])
    except SyntaxError:
        log.debug("SyntaxError while reading ip cache.")
        ip_cache_clear(opts, log)
        ip, delta = default
    return ip, delta


def ip_cache_set(opts, ip):
    """Set the cached address to IpAddr ip."""
    path = ip_cache_setup(opts)
    ip = ip if ip else IpAddr(ipv4="0.0.0.0")
    with open(path, "w") as f:
        f.write(str(ip))


def here(path):
    """Return path added to current dir for __file__."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), path)


def parse_conffile(log):
    """Parse config file path, returns verified path or None."""
    path = envvar_default('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
    path = os.path.join(path, 'ddupdate.conf')
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
    """Parse config file, return fully populated dict of key-values."""
    results = {}
    config = configparser.ConfigParser()
    config.read(path)
    if 'update' in config:
        items = config['update']
    else:
        log.warning(
            'No [update] section found in %s, file ignored', path)
        items = {}
    for key in DEFAULTS:
        if key in items:
            results[key] = items[key]
        else:
            results[key] = DEFAULTS[key]
    return results


def get_parser(conf):
    """Construct the argparser."""
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
        help='Plugin updating a dns hostname address [%s]'
        % conf['service-plugin'],
        default=conf['service-plugin'])
    normals.add_argument(
        "-a", "--address-plugin", metavar="plugin",
        help='Plugin providing ip address to use [%s]'
        % conf['address-plugin'],
        default=conf['address-plugin'])
    normals.add_argument(
        "-c", "--config-file", metavar="path",
        help='Config file with default values for all options'
        + ' [' + envvar_default('XDG_CONFIG_HOME', ' ~/.config/ddupdate.conf')
        + ':/etc/dupdate.conf]',
        dest='config_file', default='/etc/ddupdate.conf')
    normals.add_argument(
        "-l", "--loglevel", metavar='level',
        choices=['error', 'warning', 'info', 'debug'],
        help='Amount of printed diagnostics [warning]',
        default=conf['loglevel'])
    normals.add_argument(
        "-v", "--ip-version", metavar='version',
        choices=['all', 'v6', 'v4'],
        help='Ip address version(s) to register (v6, v4, all) [v4]',
        default='')
    normals.add_argument(
        "-o", "--service-option", metavar="plugin option",
        help='Service plugin option (enter multiple times if required)',
        dest='service_options', action='append')
    normals.add_argument(
        "-O", "--address-option", metavar="plugin option",
        help='Address plugin option (enter multiple times if required)',
        dest='address_options', action='append')
    normals.add_argument(
        "-i", "--ip-plugin", help=argparse.SUPPRESS)
    others = parser.add_argument_group()
    others.title = "Other options"
    others.add_argument(
        "-S", "--list-services",
        help='List service provider plugins. ',
        default=False, action='store_true')
    others.add_argument(
        "-A", "--list-addressers",
        help='List plugins providing ip address. ',
        default=False, action='store_true')
    others.add_argument(
        "-f", "--force",
        help='Force run even if the cache is fresh',
        default=False, action='store_true')
    others.add_argument(
        "-h", "--help", metavar="plugin",
        help='Print overall help or help for given plugin',
        nargs='?', const='-')
    others.add_argument(
        "-V", "--version",
        help='Print ddupdate version and exit',
        action='version')
    return parser


def parse_options(conf):
    """Parse command line using conf as defaults, return namespace."""
    level_by_name = {
        'error': logging.ERROR,
        'warn': logging.WARNING,
        'warning': logging.WARNING,
        'info': logging.INFO,
        'debug': logging.DEBUG,
    }
    parser = get_parser(conf)
    parser.version = "0.6.3"
    opts = parser.parse_args()
    if opts.help == '-':
        parser.print_help()
        raise _GoodbyeError()
    if not opts.address_options:
        opts.address_options = conf['address-options']
    if not opts.service_options:
        opts.service_options = conf['service-options']
    if not opts.ip_version:
        opts.ip_version = conf['ip-version']
    opts.loglevel = level_by_name[opts.loglevel]
    opts.ip_cache = conf['ip-cache']
    return opts


def log_setup():
    """Initialize and return the module log."""
    log = logging.getLogger('ddupdate')
    log.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter("%(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    log.addHandler(handler)
    return log


def log_options(log, args):
    """Print some info on seledted options."""
    log.info("Loglevel: " + logging.getLevelName(args.loglevel))
    log.info("Using hostname: " + args.hostname)
    log.info("Using ip address plugin: " + args.address_plugin)
    log.info("Using service plugin: " + args.service_plugin)
    log.info("Service options: " +
             (' '.join(args.service_options) if args.service_options else ''))
    log.info("Address options: " +
             (' '.join(args.address_options) if args.address_options else ''))


def load_module(path):
    """Return instantiated module loaded from given path."""
    # pylint: disable=deprecated-method
    name = os.path.basename(path).replace('.py', '')
    if sys.version_info >= (3, 5):
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    else:
        module = SourceFileLoader(name, path).load_module()
    return module


def load_plugin_dir(dirpath, parent_class):
    """
    Load all plugins in dirpath having a class derived from parent_class.

    Parameters:
      - dirpath: string, all path/*.py files are plugin candidates.
      - parent_class: class, objects being a subclass of parent are loaded.

    Returns:
      List of instantiated plugins, all derived from parent_class.

    """
    found = []
    for plugpath in glob.glob(os.path.join(dirpath, '*.py')):
        try:
            module = load_module(plugpath)
        except ImportError:
            continue
        for member_class in [m[1] for m in inspect.getmembers(module)]:
            # pylint: disable=undefined-loop-variable
            if not inspect.isclass(member_class):
                continue
            if not issubclass(member_class, parent_class):
                continue
            if member_class == parent_class:
                continue
            instance = member_class()
            instance.module = module
            found.append(instance)
    return found


def load_plugins(path, log):
    """Load ip and service plugins into dicts keyed by name."""
    setters = load_plugin_dir(os.path.join(path, 'plugins'), ServicePlugin)
    getters = load_plugin_dir(os.path.join(path, 'plugins'), AddressPlugin)
    getters_by_name = {plug.name(): plug for plug in getters}
    setters_by_name = {plug.name(): plug for plug in setters}
    log.debug("Loaded %d address and %d service plugins from %s",
              len(getters), len(setters), path)
    return getters_by_name, setters_by_name


def list_plugins(plugins):
    """List given plugins."""
    for name, plugin in sorted(plugins.items()):
        print("%-20s %s" % (name, plugin.oneliner()))


def plugin_help(ip_plugins, service_plugins, plugid):
    """Print full help for given plugin."""
    if plugid in ip_plugins:
        plugin = ip_plugins[plugid]
    elif plugid in service_plugins:
        plugin = service_plugins[plugid]
    else:
        raise _GoodbyeError("No help found (nu such plugin?): " + plugid, 1)
    print("Name: " + plugin.name())
    print("Source file: " + plugin.module.__file__ + "\n")
    print(plugin.info())


def filter_ip(ip_version, ip):
    """Filter the ip address to match the --ip-version option."""
    if ip_version == 'v4':
        ip.v6 = None
    elif ip_version == 'v6':
        ip.v4 = None
    if ip.empty():
        raise AddressError("No usable address")
    return ip


def build_load_path(log):
    """Return list of paths to load plugins from."""
    paths = []
    paths.append(envvar_default('XDG_DATA_HOME',
                                os.path.expanduser('~/.local/share')))
    syspaths = envvar_default('XDG_DATA_DIRS', '/usr/local/share:/usr/share')
    paths.extend(syspaths.split(':'))
    paths = [os.path.join(p, 'ddupdate') for p in paths]
    home = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), '..', '..')
    paths.insert(0, os.path.abspath(home))
    log.debug('paths :%s', ':'.join(paths))
    return paths


def setup(loglevel=None):
    """Return a standard log, arg_parser tuple."""
    log = log_setup()
    conffile_path = parse_conffile(log)
    conf = parse_config(conffile_path, log) if conffile_path else DEFAULTS
    opts = parse_options(conf)
    log.handlers[0].setLevel(loglevel if loglevel else opts.loglevel)
    log.debug('Using config file: %s', conffile_path)
    log_options(log, opts)
    return log, opts


def get_plugins(log, opts):
    """
    Handles plugin listing, plugin help or load plugins.

    return: (ip plugin, service plugin) tuple.
    """
    ip_plugins = {}
    service_plugins = {}
    for path in build_load_path(log):
        getters, setters = load_plugins(path, log)
        for name, plugin in getters.items():
            ip_plugins.setdefault(name, plugin)
        for name, plugin in setters.items():
            service_plugins.setdefault(name, plugin)
    if opts.list_services:
        list_plugins(service_plugins)
        raise _GoodbyeError()
    if opts.list_addressers:
        list_plugins(ip_plugins)
        raise _GoodbyeError()
    if opts.help and opts.help != '-':
        plugin_help(ip_plugins, service_plugins, opts.help)
        raise _GoodbyeError()
    if opts.ip_plugin:
        raise _GoodbyeError(
            "--ip-plugin has been replaced by --address-plugin.")
    elif opts.address_plugin not in ip_plugins:
        raise _GoodbyeError('No such ip plugin: ' + opts.address_plugin, 2)
    elif opts.service_plugin not in service_plugins:
        raise _GoodbyeError(
            'No such service plugin: ' + opts.service_plugin, 2)
    service_plugin = service_plugins[opts.service_plugin]
    ip_plugin = ip_plugins[opts.address_plugin]
    return ip_plugin, service_plugin


def main():
    """Indeed: main function."""
    try:
        log, opts = setup()
        ip_plugin, service_plugin = get_plugins(log, opts)
        try:
            ip = ip_plugin.get_ip(log, opts.address_options)
        except AddressError as err:
            raise _GoodbyeError("Cannot obtain ip address: " + str(err), 3)
        if not ip or ip.empty():
            log.info("Using ip address provided by update service")
            ip = None
        else:
            ip = filter_ip(opts.ip_version, ip)
            log.info("Using ip address: %s", ip)
        if opts.force:
            ip_cache_clear(opts, log)
        cached_ip, age = ip_cache_data(opts, log)
        if age < service_plugin.ip_cache_ttl() and (cached_ip == ip or not ip):
            log.info("Update inhibited, cache is fresh (%d/%d min)",
                     age, service_plugin.ip_cache_ttl())
            raise _GoodbyeError()
    except _GoodbyeError as err:
        if err.exitcode != 0:
            log.error(err.msg)
            sys.stderr.write("Fatal error: " + str(err) + "\n")
        sys.exit(err.exitcode)
    try:
        service_plugin.register(log, opts.hostname, ip, opts.service_options)
    except ServiceError as err:
        log.error("Cannot update DNS data: %s", err)
    else:
        ip_cache_set(opts, ip)
        log.info("Update OK")


if __name__ == '__main__':
    main()


# vim: set expandtab ts=4 sw=4:
