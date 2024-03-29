Complete, manual ddupdate configuration
=======================================

Before configuration, the software must be installed. See README.md.
Please also note that the the manual steps described here could
be replaced by running *ddupdat-config* for most users.

Configuration is basically about selecting a plugin for a specific ddns
service and another plugin which provides the ip address to be registered.
Some plugins needs specific plugin options.

There is also a choice how to store the username/password credentials,
either in the _~/.netrc_ file or in the keyring.

Address Plugin
--------------

The address plugin to use is usually either *default-web-ip*
or *default-if*.

The *default-web-ip* plugin should be used when the address to register is
the external address visible on the internet - that is, if the registered
host should be accessed from the internet. For most services *ip-disabled*
could be used instead. Services will then use the external address as seen
from the service. See the *ddupdate --help <service>* info.

The *default-if* plugin uses the first address found on the default
interface. This typically means registering the address used on an internal
network, and should be used if the registered host should be accessed from
this internal network.

Should these options not fit, several other address plugins are available
using *ddupdate --list-addressers*.  After selecting address plugin, test
it using something like::

    $ ./ddupdate --ip-plugin default-web-ip --service-plugin dry-run
    dry-run: Using
        v4 address: 83.255.182.111
        v6 address: None
        hostname: host1.nowhere.net

Service Plugin
--------------
After selecting the address plugin, start the process of selecting a
service by listing all available services (your list might differ)::

    $ ddupdate --list-services
    changeip.com         Updates on http://changeip.com/
    cloudflare.com       Updates on https://cloudflare.com
    dnsdynamic.org       Updates on http://dnsdynamic.org/
    dnsexit.com          Updates on https://www.dnsexit.com
    dnspark.com          Updates on https://dnspark.com/
    dry-run              Debug dummy update plugin
    dtdns.com            Updates on https://www.dtdns.com
    duckdns.org          Updates on http://duckdns.org
    duiadns.net          Updates on https://www.duiadns.net
    dy.fi                Updates on https://www.dy.fi/
    dynu.com             Updates on https://www.dynu.com/en-US/DynamicDNS
    dynv6.com            Updates on http://dynv6.com
    freedns.afraid.org   Updates on https://freedns.afraid.org
    freedns.io           Updates on https://freedns.io
    googledomains        Updates DNS data on domains.google.com
    hurricane_electric   Updates on https://he.com
    myonlineportal.net   Updates on http://myonlineportal.net/
    no-ip.com            Updates on http://no-ip.com/
    now-dns.com          Updates on http://now-dns.com
    nsupdate             Update address via nsupdate
    system-ns.com        Updates on https://system-ns.com

Next, pick a service plugin and check the help info, here dynu::

    $ ddupdate --help dynu
    Name: dynu
    Source: /home/al/src/ddupdate/src/ddupdate/plugins/ddplugin.py

    Update a dns entry on dynu.com

    Supports ip address discovery and can thus work with the ip-disabled
    plugin.

    .netrc: Use a line like:
        machine api.dynu.com login <username> password <password>

    Options:
        none

If all looks good, register on dynu.com. This will end up in a hostname,
username and password. Add the host, username and password to the
_~/.netrc_ file using::

    $ ddupdate -C netrc -p <hostname> <username> <password>

_hostname_ is available in the plugin's .netrc help text as 'machine',
for example _api.dynu.com_ in help text above. Test the service using the
selected address plugins, something like::

    $ ./ddupdate --address-plugin default-web-ip --service-plugin dynu \
    --hostname myhost.dynu.net -l info
    INFO - Loglevel: INFO
    INFO - Using hostname: myhost.dynu.net
    INFO - Using ip address plugin: default-web-ip
    INFO - Using service plugin: dynu
    INFO - Plugin options:
    INFO - Using ip address: 90.3.08.212
    INFO - Update OK

When all is fine, update *~/.config/ddupdate.conf* or */etc/ddupdate.conf* to
something like::

    [update]
    address-plugin = web-default-ip
    service-plugin = dynu
    hostname = myhost.dynu.net
    loglevel = info
    auth-plugin = netrc

After which it should be possible to just invoke *ddupdate* without any
options. When done, proceed to Configuring systemd in README.md

Adding more hosts
=================

It is possible to add more hosts to the configuration file. This means that
ddupdate will update two or more services when run. This is an experimental
procedure.

The starting point could be a _~/.config/ddupdate.conf_ file created by
_ddupdate-config_ like::

    [update]
    address-plugin = default-web-ip
    service-plugin = dynu
    hostname = myhost.dynu.net
    loglevel = info

The first step is to replace '[update]' with a new name, for example
'[dynu]'. After this, ddupdate-config can be run again creating::

    [dynu]
    address-plugin = default-web-ip
    service-plugin = dynu
    auth-plugin = keyring
    hostname = myhost.dynu.net
    loglevel = info

    [update]
    address-plugin = default-web-ip
    service-plugin = duckdns.org
    auth-plugin = keyring
    hostname = myhost.duckdns.org
    loglevel = info

The process can be repeated to add more entries. New entries can also be
added manually.

It is also necessary to update username/password credentials stored in
~/.netrc or the keyring. If using `ddupdate-config` this is handled
automatically. Otherwise this can be done using the `-p' option using
something like::

    $ ddupdate -C netrc <hostname> <username> <password>

_hostname_ is available in the plugin's .netrc help text as 'machine'.
Use `-C keyring` when using the keyring credentials storage. Services only
using an API key should use "" as username and the API key as 'password'.

The CLI support for multiple hosts::

  - `-E` lists the available configuration sections.
  - `-e <section>` can be used to only run a specific section when running
    ddupdate manually on the command line.


Using the keyring for passwords
===============================

Version 7.0 contains experimental support for storing passwords in the system
keyring.  The basic parts

  - Credentials are managed by a new type of auth plugins. Use `ddupdate -P`
    to list available plugins.
  - Set the _auth-plugin_ option in the config file to _keyring_ to activate
    the keyring support.
  - To set passwords for services use the new -p option to `ddupdate`. For
    example `ddupdate -C keyring  -p myhost username password`. For hosts
    using an api key without username, use "" for username.
  - The new script `ddupdate_netrc_to_keyring` migrates all entries in
    _~/.netrc_ to the keyring.
  - To check passwords in keyring::

        $ python3
        > import keyring
        > keyring.get_password('ddupdate', 'myhost.tld')

Note that the keyring needs to be unlocked before accessed making it less
useful in servers.
