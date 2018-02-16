ddupdate - Update dns data for dynamic ip addresses.
====================================================

General
-------

ddupdate is a tool for automatically updating dns data for a system using
for example DHCP. It makes it possible to access such a system with
a fixed dns name like myhost.somewhere.net even if the IP address is
changed. It is a linux-centric, user-friendly and secure alternative to
the ubiquitous ddclient.

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
  - The /usr/sbin/ip command is used in some plugins.
  - python3-setuptools  (build)
  - pkg-config  (build)

Installation
------------

**ddupdate** can be run as a regular user straight off the cloned git
directory. To make it possible to run from anywhere make a symlink::

    $ ln -s $PWD/ddupdate $HOME/bin/ddupdate

It is also possible to install as a pypi package using::

    $ sudo pip install ddupdate --prefix=/usr/local

See CONTRIBUTE.md for more info on using the pypi package.

ddupdate is part of Fedora from Fedora 28. Fedora 27, CentOS/EPEL and
Mageia users can install native rpm packages from
https://copr.fedorainfracloud.org/coprs/leamas/ddupdate/.

Ubuntu users can install native .deb packages using the PPA at
https://launchpad.net/~leamas-alec/+archive/ubuntu/ddupdate

ddupdate is part of the Debian sid distribution. CONTRIBUTE.md describes
how to create packages for other Debian distributions. Overall, using
native packages is the preferred installation method on platforms
supporting this.

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
*~/.config/ddupdate.conf* and *~/.netrc*.

After running the script it should be possible to run a plain
```ddupdate -l debug``` without error messages.

When this works, systemd should be configured as described below.


Configuring systemd
-------------------

systemd is setup to run as a user service. Start by testing it::

    $ sudo systemctl --user daemon-reload
    $ sudo systemctl --user start ddupdate.service
    $ sudo journalctl --user -u ddupdate.service

If all is fine make sure ddupdate is run hourly using::

    $ sudo systemctl --user start ddupdate.timer
    $ sudo systemctl --user enable ddupdate.timer

If you want the service to start as soon as the machine boots, and to
continue even when you log out do:

    $ sudo  loginctl enable-linger $USER

If there is trouble or if you for example want to run ddupdate more often,
edit the files *~/.config/systemd/user/ddupdate.service* and
*~/.config/systemd/user/ddupdate.timer*

Configuring NetworkManager
--------------------------

NetworkManager can be configured to start/stop ddupdate when interfaces goes
up or down. An example script to drop in */etc/NetworkManager/dispatcher.d*
is distributed in the package.
