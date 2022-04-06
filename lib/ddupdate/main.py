"""Update DNS data for dynamic ip addresses."""

import argparse
import configparser
import glob
import importlib
import importlib.util
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
from ddupdate.ddplugin import ServicePlugin, ServiceError, IpAddr
from ddupdate.ddplugin import AuthPlugin, AuthError
from ddupdate.ddplugin import set_auth_plugin, get_auth_plugin


if 'XDG_CACHE_HOME' in os.environ:
    CACHE_DIR = os.environ['XDG_CACHE_HOME']
else:
    CACHE_DIR = os.path.expanduser('~/.cache')

DEFAULTS = {
    'hostname': 'host.nowhere.net',
    'address-plugin': 'default-if',
    'service-plugin': 'dry-run',
    'auth-plugin': 'netrc',
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


class _SectionFailError(Exception):
    """General error, terminates section processing."""


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
    for i, arg in enumerate(sys.argv):
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


def parse_config(config, section):
    """Return dict with values from config backed by DEFAULTS."""
    results = {}
    if section not in config:
        raise _GoodbyeError("No such section: " + section, 2)
    items = config[section]
    for key, value in DEFAULTS.items():
        results[key] = items[key] if key in items else value
    return results


def get_config(log):
    """Parse config file, return a (ConfigParser, list of sections) tuple."""
    path = parse_conffile(log)
    config = configparser.ConfigParser()
    config.read(path)
    sections = list(config.keys())
    if 'DEFAULT' in sections:
        sections.remove('DEFAULT')
    return config, sections


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
        "-C", "--auth-plugin", metavar="plugin",
        help='Plugin providing authentication credentials  [%s]'
        % conf['auth-plugin'],
        default=conf['auth-plugin'])
    normals.add_argument(
        "-c", "--config-file", metavar="path",
        help='Config file with default values for all options'
        + ' [' + envvar_default('XDG_CONFIG_HOME', ' ~/.config/ddupdate.conf')
        + ':/etc/ddupdate.conf]',
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
        default=conf['ip-version'])
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
        "-P", "--list-auth-plugins",
        help='List plugins providing credentials. ',
        default=False, action='store_true')
    others.add_argument(
        "-E", "--list-sections",
        help='List configuration file sections. ',
        default=False, action='store_true')
    others.add_argument(
        "-e", "--execute-section", metavar="section",
        help='Update a given configuration file section [all sections]',
        dest='execute_section', default='')
    others.add_argument(
        "-p", "--set_password", nargs=3, metavar=('host', 'user', 'pw'),
        help='Update username/password for host. Use "" for empty username',
        default="")
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
    parser.version = "0.7.1"
    opts = parser.parse_args()
    if opts.help == '-':
        parser.print_help()
        raise _GoodbyeError()
    if not opts.address_options:
        opts.address_options = []
        if conf['address-options']:
            opts.address_options = conf['address-options'].split()
    if not opts.service_options:
        opts.service_options = []
        if conf['service-options']:
            opts.service_options = conf['service-options'].split()
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


def log_init(log, loglevel, opts):
    """Initiate the global log."""
    log.handlers[0].setLevel(loglevel if loglevel else opts.loglevel)
    log.debug('Using config file: %s', parse_conffile(log))
    log.info("Loglevel: " + logging.getLevelName(opts.loglevel))
    log.info("Using hostname: " + opts.hostname)
    log.info("Using ip address plugin: " + opts.address_plugin)
    log.info("Using service plugin: " + opts.service_plugin)

    log.info("Service options: " +
             (' '.join(opts.service_options) if opts.service_options else ''))
    log.info("Address options: " +
             (' '.join(opts.address_options) if opts.address_options else ''))


def load_module(path):
    """Return instantiated module loaded from given path."""
    # pylint: disable=deprecated-method
    name = os.path.basename(path).replace('.py', '')
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
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
    auths = load_plugin_dir(os.path.join(path, 'plugins'), AuthPlugin)
    getters_by_name = {plug.name(): plug for plug in getters}
    setters_by_name = {plug.name(): plug for plug in setters}
    auths_by_name = {plug.name(): plug for plug in auths}
    log.debug("Loaded %d address, %d service and %d auth plugins from %s",
              len(getters), len(setters), len(auths), path)
    return auths_by_name, getters_by_name, setters_by_name


def list_plugins(plugins):
    """List given plugins."""
    for name, plugin in sorted(plugins.items()):
        print("%-20s %s" % (name, plugin.oneliner()))


def plugin_help(plugins, plugid):
    """Print full help for given plugin."""
    if plugid in plugins:
        plugin = plugins[plugid]
    else:
        raise _GoodbyeError("No help found (no such plugin?): " + plugid, 1)
    print("Name: " + str(plugin))
    print("Source file: " + plugin.module.__file__ + "\n")
    print(plugin.info())


def set_password(opts):
    """Set password using selected auth plugin."""
    auth_plugin = get_auth_plugin()
    auth_plugin.set_password(*opts.set_password)


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


def get_plugins(opts, log, sections):
    """
    Handles plugin listing, plugin help or load plugins.

    Return: (auth_plugin, ip plugin, service plugin) tuple.
    """
    # pylint: disable=too-many-branches,too-many-locals
    ip_plugins = {}
    service_plugins = {}
    auth_plugins = {}
    for path in build_load_path(log):
        auths, getters, setters = load_plugins(path, log)
        for name, plugin in getters.items():
            ip_plugins.setdefault(name, plugin)
        for name, plugin in setters.items():
            service_plugins.setdefault(name, plugin)
        for name, plugin in auths.items():
            auth_plugins.setdefault(name, plugin)
    if opts.list_services:
        list_plugins(service_plugins)
        raise _GoodbyeError()
    if opts.list_addressers:
        list_plugins(ip_plugins)
        raise _GoodbyeError()
    if opts.list_auth_plugins:
        list_plugins(auth_plugins)
        raise _GoodbyeError()
    if opts.help and opts.help != '-':
        all_plugins = {**auth_plugins, **ip_plugins, **service_plugins}
        plugin_help(all_plugins, opts.help)
        raise _GoodbyeError()
    if opts.list_sections:
        print("\n".join(sections))
        raise _GoodbyeError()
    if opts.ip_plugin:
        raise _GoodbyeError(
            "--ip-plugin has been replaced by --address-plugin.")
    if opts.address_plugin not in ip_plugins:
        raise _GoodbyeError('No such ip plugin: ' + opts.address_plugin, 2)
    if opts.auth_plugin not in auth_plugins:
        raise _GoodbyeError('No such auth plugin: ' + opts.auth_plugin, 2)
    if opts.service_plugin not in service_plugins:
        raise _GoodbyeError(
            'No such service plugin: ' + opts.service_plugin, 2)
    service_plugin = service_plugins[opts.service_plugin]
    ip_plugin = ip_plugins[opts.address_plugin]
    auth_plugin = auth_plugins[opts.auth_plugin]
    if opts.set_password:
        set_auth_plugin(auth_plugin)
        set_password(opts)
        raise _GoodbyeError()
    return auth_plugin, ip_plugin, service_plugin


def get_ip(ip_plugin, opts, log):
    """Try to get current ip address using the ip_plugin."""
    try:
        ip = ip_plugin.get_ip(log, opts.address_options)
    except AddressError as err:
        raise _SectionFailError("Cannot obtain ip address: " + str(err)) \
            from err
    if not ip or ip.empty():
        log.info("Using ip address provided by update service")
        ip = None
    else:
        ip = filter_ip(opts.ip_version, ip)
        log.info("Using ip address: %s", ip)
    return ip


def check_ip_cache(ip, service_plugin, opts, log):
    """Throw a _SectionFailError if ip is already in a fresh cache."""
    if opts.force:
        ip_cache_clear(opts, log)
    cached_ip, age = ip_cache_data(opts, log)
    if age < service_plugin.ip_cache_ttl() and (cached_ip == ip or not ip):
        log.info("Update inhibited, cache is fresh (%d/%d min)",
                 age, service_plugin.ip_cache_ttl())
        raise _SectionFailError()


def main():
    """Indeed: main function."""
    try:
        log = log_setup()
        config, sections = get_config(log)
        opts = parse_options(DEFAULTS)
        get_plugins(opts, log, sections)
        if opts.execute_section:
            sections = [opts.execute_section]
        for section in sections:
            try:
                conf = parse_config(config, section)
                opts = parse_options(conf)
                log_init(log, None, opts)
                log.info("Processing configuration section: %s", section)
                auth_plugin, ip_plugin, service_plugin = get_plugins(
                    opts, log, sections)
                set_auth_plugin(auth_plugin)
                log.debug("Using auth plugin: %s", str(auth_plugin))
                ip = get_ip(ip_plugin, opts, log)
                check_ip_cache(ip, service_plugin, opts, log)
                service_plugin.register(
                    log, opts.hostname, ip, opts.service_options)
                ip_cache_set(opts, ip)
                log.info("Update OK")
            except _SectionFailError:
                print("Skipping config section: %s" % section)
                continue
            except (ServiceError, AuthError) as err:
                log.error("Cannot update DNS data: %s", err)
                log.info("Skipping config section: %s", section)
                continue
    except _GoodbyeError as err:
        if err.exitcode != 0:
            log.error(err.msg)
            sys.stderr.write("Fatal error: " + str(err) + "\n")
        sys.exit(err.exitcode)


if __name__ == '__main__':
    main()


# vim: set expandtab ts=4 sw=4:
