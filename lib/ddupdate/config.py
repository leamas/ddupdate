"""Simple, CLI configuration script for ddupdate."""

import configparser
import logging
import os
import os.path
import re
import shutil
from typing import Dict

import stat
import subprocess
import sys
import tempfile
import time

from ddupdate.main import \
    setup, build_load_path, envvar_default, load_plugin_dir
from ddupdate.ddplugin import \
    ServicePlugin, AddressPlugin, AddressError, IpVersion

_CONFIG_TRAILER = """
#
# Check for plugin options using ddupdate --help  <plugin name>
#
# service-options = foo bar
# address-options = foo bar
"""

_UPDATE_CONFIG = """
#!/bin/sh
if test -e {netrc_path}; then
    sed -E -i '/machine[ ]+{machine}/d' {netrc_path}
fi
if test "{netrc_line}" != "machine dummy"; then
    echo {netrc_line} >> {netrc_path}
fi
chmod 600 {netrc_path}
cp {config_src} {config_dest}

"""


class _GoodbyeError(Exception):
    """General error, implies sys.exit()."""

    def __init__(self, msg="", exitcode=0):
        Exception.__init__(self, msg)
        self.exitcode = exitcode
        self.msg = msg


def check_existing_files():
    """Check existing files and let user save them."""
    confdir = \
        envvar_default('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
    files = [
        os.path.expanduser('~/.netrc'),
        os.path.join(confdir, 'ddupdate.conf')
    ]
    files = [f for f in files if os.path.exists(f)]
    if not files:
        return
    print("The following configuration file(s)s already exists:")
    for f in files:
        print("        " + f)
    reply = input("OK to overwrite (Yes/No) [No]: ")
    if not reply or not reply.lower().startswith('y'):
        print("Please save these file(s) and try again.")
        raise _GoodbyeError("", 0)


def _load_plugins(log, paths, plugin_class):
    """
    Load plugins into dict keyed by name.

    Parameters:
      - log: Standard python log instance.
      - paths: List of strings, path candidates containing plugins.
      - plugin_class: Type, base class of plugins to load.

    Returns:
      dict of loaded plugins with plugin.name() as key.

    """
    plugins = {}
    for path in paths:
        these = load_plugin_dir(os.path.join(path, 'plugins'), plugin_class)
        these_by_name = {plug.name(): plug for plug in these}
        for name, plugin in these_by_name.items():
            plugins.setdefault(name, plugin)
        log.debug("Loaded %d plugins from %s", len(plugins), path)
    return plugins


def _load_services(log, paths):
    """Load service plugins from paths into dict keyed by name."""
    return _load_plugins(log, paths, ServicePlugin)


def _load_addressers(log, paths):
    """Load address plugins from paths into dict keyed by name."""
    return _load_plugins(log, paths, AddressPlugin)


def get_service_plugin(service_plugins):
    """
    Present a menu with all plugins to user, let her select.

    Parameters:
      - service_plugins: Dict of loaded plugins keyed by plugin.name()

    Return:
      A loaded plugin as selected by user.

    """
    ix = 1
    services_by_ix = {}
    use_service = False

    for id_ in sorted(service_plugins):
        print("%2d     %-18s     %s" %
              (ix, id_, service_plugins[id_].oneliner()))
        services_by_ix[ix] = service_plugins[id_]
        ix += 1

    while not use_service:
        reply = input("Select service to use: ")

        try:
            ix = int(reply)
        except ValueError:
            ix = 0

        if ix not in range(1, len(services_by_ix) + 1):
            reply = input("Invalid option selected, try again? (Yes/No) [Yes]: ")
            if reply and reply.lower().startswith('n'):
                raise _GoodbyeError("Configuration aborted by user", 1)
        else:
            use_service = True

    return services_by_ix[ix]


def get_address_plugin(
        log: logging.Logger,
        address_plugins: Dict[str, AddressPlugin],
        address_options: [str],
        default_plugin_id: str = 'default-web-ip') -> AddressPlugin:
    """
    Let user select address plugin.

    Parameters:
      - log: Standard python log instance.
      - address_plugins: Dict of loaded plugins keyed by plugin.name()
      - address_options: Options from --address-options
      - default_plugin_id: ID of the plugin to use by default if nothing is selected

    Return:
      A loaded plugin as selected by user.

    """

    ix = 1
    plugins_by_ix = {}
    default_plugin_ix = 1
    use_plugin = False

    for id_ in sorted(address_plugins):
        print("%2d     %-18s     %s"
              % (ix, id_, address_plugins[id_].oneliner()))

        plugins_by_ix[ix] = address_plugins[id_]

        # Update default index based on the actual position of the default_plugin_id
        if default_plugin_id == id_:
            default_plugin_ix = ix

        ix += 1

    # Let the user continuously select until satisfied.
    while not use_plugin:
        reply = input("Select address-plugin to resolve ip-addresses [%d]: "
                      % default_plugin_ix).strip()

        try:
            ix = int(reply.strip() if reply else default_plugin_ix)
        except ValueError:
            ix = 0

        if ix in plugins_by_ix:
            print("Probing for addresses, can take some time...")
            try:
                # Probe IPs from selected service
                ip = plugins_by_ix[ix].get_ip(log, address_options)
                if not ip or ip.empty():
                    print("Service did not respond with a ip-address.")
                    reply = input("Use this service anyway? (Yes/No) [No]: ")
                    use_plugin = reply and reply.lower().startswith('y')
                else:
                    print("Received IPv4-address: %s" % ip.v4)
                    print("Received IPv6-address: %s" % ip.v6)
                    reply = input("Use this service? (Yes/No) [Yes]: ")
                    use_plugin = not reply or reply.lower().startswith('y')
            except AddressError as err:
                print("Error obtaining ip-addresses: %s" % err)
                reply = input("Try another service? (Yes/No) [Yes]: ")
                if reply and not reply.lower().startswith('n'):
                    use_plugin = True
        else:
            reply = input("Invalid option selected, try again? (Yes/No) [Yes]: ")
            if reply and reply.lower().startswith('n'):
                raise _GoodbyeError("Configuration aborted by user", 1)

    return plugins_by_ix[ix]


def get_ip_version(default_version: IpVersion = IpVersion.V4) -> str:
    """Let user select the ip-version.

    Parameters:
      - default_version: ip-version enum value to be used if none is selected.

    Return:
      The ip-version string as selected by the user.

    """
    versions_by_ix = {}
    default_version_ix = 1
    use_version = False

    for ix, version in enumerate(IpVersion, 1):
        print("%2d     %s" % (ix, version.value))

        versions_by_ix[ix] = version

        # Update default index based on the actual position of the default_version
        if default_version is version:
            default_version_ix = ix

        ix += 1

    # Let the user continuously select until satisfied.
    ix = default_version_ix
    while not use_version:
        reply = input("Select ip-version to update [%d]: "
                      % default_version_ix).strip()

        try:
            ix = int(reply.strip() if reply else default_version_ix)
        except ValueError:
            ix = 0

        if ix in versions_by_ix:
            use_version = True
        else:
            reply = input("Invalid option selected, try again? (Yes/No) [Yes]: ")
            if reply and reply.lower().startswith('n'):
                raise _GoodbyeError("Configuration aborted by user", 1)

    return versions_by_ix[ix].name.lower()


def copy_systemd_units():
    """Copy system-wide templates to ~/.config/systemd/user."""
    confdir = \
        envvar_default('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
    user_dir = os.path.join(confdir, 'systemd/user')
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)
    path = os.path.join(user_dir, "ddupdate.service")
    if not os.path.exists(path):
        shutil.copy("/usr/share/ddupdate/systemd/ddupdate.service", path)
    path = os.path.join(user_dir, "ddupdate.timer")
    if not os.path.exists(path):
        shutil.copy("/usr/share/ddupdate/systemd/ddupdate.timer", path)
    here = os.path.abspath(os.path.dirname(os.path.realpath(__file__)))
    installconf_path = os.path.join(here, "install.conf")
    parser = configparser.SafeConfigParser()
    try:
        parser.read(installconf_path)
    except configparser.Error:
        parser.clear()
    if 'install' in parser:
        bindir = parser['install']['install_scripts']
    else:
        bindir = os.path.abspath(os.path.join(here, '..', '..'))
    with open(os.path.join(user_dir, 'ddupdate.service')) as f:
        lines = f.readlines();
    with open(os.path.join(user_dir, 'ddupdate.service'), 'w')  as f:
        for l in lines:
            if l.startswith('ExecStart'):
                f.write("ExecStart=" + bindir + "/ddupdate\n")
            else:
                f.write(l + "\n")


def get_netrc(service):
    """
    Get .netrc line for service.

    Looks into the service class documentation for a line starting
    with 'machine' and returns it after substituting values in
    angle brackets lke <username> with values supllied by user.

    Parameters:
      - service: Loaded service plugin.

    Return:
      netrc line with <user>, <password>, etc., as substituted by user.

    """
    lines = service.info().split('\n')
    line = ''
    for line in lines:
        if line.strip().startswith('machine'):
            break
    else:
        return None
    matches = re.findall('<([^>]+)>', line)
    for item in matches:
        value = input("[%s] %s :" % (service.name(), item))
        line = line.replace('<' + item + '>', value)
    return line


def merge_configs(netrc_line, netrc_path, config_src, config_dest, cmd):
    """
    Merge netrc and config file options into current configuration.

    Parameters:
      - netrc_line: String, new netrc authentication line.
      - netrc_path: String, path of netrc file.
      - config_src: String, path of updated, temporary config file.
      - config_dest: String, path of existing config file actually used.
      - cmd: function(path) returning command executing path in a shell,
             a list of strings.

    Returns nothing.

    """
    netrc_line = netrc_line if netrc_line else "machine dummy"
    script = _UPDATE_CONFIG.format(
        netrc_line=netrc_line,
        machine=netrc_line.split()[1],
        netrc_path=netrc_path,
        config_src=config_src,
        config_dest=config_dest
    )
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(script.encode())
    os.chmod(f.name, stat.S_IRUSR | stat.S_IXUSR)
    subprocess.run(cmd(f.name))
    os.unlink(f.name)
    print("Patched .netrc: " + netrc_path)
    print("Patched config: " + config_dest)


def update_config(config, path):
    """
    Merge values from config dict and existing conf into tempfile.

    Parameters:
      - config: dict of new configuration options.
      - path:  Path to existing config file.

    Return:
      Path to temporary config file with updated options.

    """
    parser = configparser.SafeConfigParser()
    try:
        parser.read(path)
    except configparser.Error:
        parser.clear()
    parser.setdefault('update', {})
    parser['update'].setdefault('ip-version', 'v4')
    parser['update'].setdefault('loglevel', 'info')
    parser['update'].update(config)
    with tempfile.NamedTemporaryFile(delete=False, mode='w') as f:
        f.write('# Created by ddupdate-config at %s\n' % time.asctime())
        parser.write(f)
        if ('service-options' or 'address-options') not in parser:
            f.write(_CONFIG_TRAILER)
        f.flush()
    return f.name


def write_config_files(config, netrc_line):
    """
    Merge user config data into user config files.

    Parameters:
      - config: dict with new configuration options.
      - netrc_line: Authentication line to merge into existing .netrc file.

    Updates:
      ~/.config/ddupdate.conf and ~/.netrc, respecting XDG_CONFIG_HOME.

    """
    confdir = \
        envvar_default('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
    if not os.path.exists(confdir):
        os.makedirs(confdir)
    tmp_conf = update_config(config, os.path.join(confdir, "ddupdate.conf"))
    merge_configs(netrc_line,
                  os.path.expanduser('~/.netrc'),
                  tmp_conf,
                  os.path.join(confdir, "ddupdate.conf"),
                  lambda p: ["/bin/sh", p])
    os.unlink(tmp_conf)


def try_start_service():
    """Start dduppdate systemd user service and display logs."""
    print("Starting service and displaying logs")
    cmd = 'systemctl --user daemon-reload'
    cmd += ';systemctl --user start ddupdate.service'
    cmd += ';journalctl -l --user --since -60s -u ddupdate.service'
    cmd = ['sh', '-c', cmd]
    subprocess.run(cmd)
    print('Use "journalctl --user -u ddupdate.service" to display logs.')


def enable_service():
    """Enable/start service and timer as user determines."""
    reply = input("Shall I run service regularly (Yes/No) [No]: ")
    do_start = reply and reply.lower().startswith('y')
    if do_start:
        cmd = 'systemctl --user start ddupdate.timer'
        cmd += ';systemctl --user enable ddupdate.timer'
        print("\nStarting and enabling ddupdate.timer")
        subprocess.run(['sh', '-c', cmd])
    else:
        cmd = 'systemctl --user stop ddupdate.timer'
        cmd += 'systemctl --user disable ddupdate.timer'
        print("Stopping ddupdate.timer")
        subprocess.run(['sh', '-c', cmd])
        msg = "systemctl --user start ddupdate.timer"
        msg += "; systemctl --user enable ddupdate.timer"
        print('\nStart ddupdate using "%s"' % msg)
    print("To run service from boot and after logout do "
          + '"sudo loginctl enable-linger $USER"')


def main():
    """Indeed: main function."""
    try:
        log = setup(logging.WARNING)[0]
        check_existing_files()
        copy_systemd_units()
        load_paths = build_load_path(log)
        service_plugins = _load_services(log, load_paths)
        service = get_service_plugin(service_plugins)
        netrc = get_netrc(service)
        hostname = input("[%s] hostname: " % service.name())
        address_plugins = _load_addressers(log, load_paths)
        address_plugin = get_address_plugin(log, address_plugins, [])
        ip_version = get_ip_version()
        conf = {
            'address-plugin': address_plugin.name(),
            'service-plugin': service.name(),
            'hostname': hostname,
            'ip-version': ip_version,
        }
        write_config_files(conf, netrc)
        try_start_service()
        enable_service()
    except _GoodbyeError as err:
        if err.exitcode != 0:
            sys.stderr.write("Fatal error: " + str(err) + "\n")
        sys.exit(err.exitcode)


if __name__ == '__main__':
    main()

# vim: set expandtab ts=4 sw=4:
