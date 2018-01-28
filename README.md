ddupdate - Update dns data for dynamic ip addresses.
====================================================

General
-------

ddupdate is a tool for automatically updating dns data for a system using
for example DHCP. It makes it possible to access the system with
a fixed dns name such as myhost.somewhere.net even if the IP address is
changed. It is a linux-centric, user-friendly, flexible and maintainable
alternative to the ubiquitous ddclient.

Status
------

Beta. The plugin API will be kept stable up to 1.0.0, and there should be
no incompatible CLI changes.

At the time of writing 14 free services are supported. There are also 7
address plugins. Together, this should cover most usecases based on freely
available services.

Still, this is beta and there is most likely bugs out there.

Dependencies
------------

  - python3 (tested on 3.6 and 3.4)
  - python3-straight.plugin. Packaged in most (all?) linux distributions
    and also available at https://pypi.python.org
  - python3-setuptools
  - The /usr/sbin/ip command is used in some plugins.

Installation
------------

**ddupdate** can be run as a regular user straight off the cloned git
directory. To make it possible to run from anywhere make a symlink::

    $ ln -s $PWD/ddupdate $HOME/bin/ddupdate

It is also possible to install as a pypi package using::

    $ sudo pip install ddupdate --prefix=/usr/local

See CONTRIBUTE.md for more info on using the pypi package.

Fedora and Mageia users can install native rpm packages from
https://copr.fedorainfracloud.org/coprs/leamas/ddupdate/.

Ubuntu users can install native .deb packages using the PPA at
https://launchpad.net/~leamas-alec/+archive/ubuntu/ddupdate

CONTRIBUTE.md describes how to create Debian packages. Here is also more
info on using the pypi package. Overall, using native packages is the
preferred method on platforms supporting this.

Configuration
-------------

This is the fast track assuming that you are using a native package and
mainstream address options. If running into troubles, see the manual
steps described in CONFIGURATION.md.

Start with running ```ddupdate --list-services```. Pick a supported
service and check it using ```ddupdate --help <service>```.

At this point you need to register with the relevant website. The usual
steps are to first create an account and then, using the account, create
a host. The process should end up with a hostname, a user and a secret
password (some sites just uses an API key).

Then start the configuration script ```ddupdate-config```. The script
guides you through the configuration and updates several files, notably
*/etc/ddupdate.conf* and *~ddupdate/.netrc*.

Configuring systemd
-------------------

Start by testing the service::

    $ sudo systemctl daemon-reload
    $ sudo systemcl start ddupdate.service
    $ sudo journalctl -u ddupdate.service

If all is fine make sure ddupdate is run hourly using::

    $ sudo systemctl start ddupdate.timer
    $ sudo systemctl enable ddupdate.timer

If there is trouble or you for example want to run ddupdate more often,
do not not use the upstream systemd files. Instead, do::

    $ sudo cp /lib/systemd/system/ddupdate.service /etc/systemd/system
    $ sudo cp /lib/systemd/system/ddupdate.timer /etc/systemd/system

Check the two /etc files, in particular for paths. Test the service and
the logged info as described above.

Configuring NetworkManager
--------------------------

NetworkManager can be configured to start/stop ddupdate when interfaces goes
up or down. An example script to drop in */etc/NetworkManager/dispatcher.d*
is distributed in the package.
