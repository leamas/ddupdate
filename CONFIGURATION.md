Complete, manual ddupdate configuration
=======================================

Before configuration, the software must be installed. See README.md.
Please also note that the the manual steps described here could
be replaced by running *ddupdat-config* for most users.

Configuration is basically about selecting a plugin for a specific ddns
service and another plugin which provides the ip address to be registered.
Some plugins needs specific plugin options.

The address plugin to use is normally either *default-web-ip*
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

After selecting the address plugin, start the process of selecting a
service by listing all available services (your list might differ)::

    $ ddupdate --list-services
    changeip.com         Updates on http://changeip.com/
    cloudflare.com       Updates on https://cloudflare.com
    dnsdynamic.org       Updates on http://dnsdynamic.org/
    dnsexit.com          Updates on https://www.dnsexit.com
    dnshome.de           Updates on https://www.dnshome.de
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
username and password. Using the .netrc info in the *ddupdate help
<service>*, create an entry in the *~/.netrc*  file like::

    machine api.dynu.com login <username> password <secret>

Note that this file must be protected for other users (otherwise no tools
will accept it). Do::

    $ chmod 600 ~/.netrc

Test the service using the selected address plugins, something like::

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

After which it should be possible to just invoke *ddupdate* without any
options. When done, proceed to Configuring systemd in README.md
