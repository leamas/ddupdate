"""ddupdate install data."""

import shutil
import os
import subprocess

from distutils.command.clean import clean
from distutils.command.install import install

from glob import glob
from setuptools import setup

# pylint: disable=bad-continuation
ROOT = os.path.dirname(__file__)
ROOT = ROOT if ROOT else '.'


def systemd_unitdir():
    """Return the official systemd user unit dir path without leading /."""
    cmd = 'pkg-config systemd --variable=systemduserunitdir'.split()
    try:
        return subprocess.check_output(cmd).decode().strip()[1:]
    except (OSError, subprocess.CalledProcessError):
        return  "usr/lib/systemd/user"


DATA = [
    (systemd_unitdir(), glob('systemd/*')),
    ('share/bash-completion/completions/', ['bash_completion.d/ddupdate']),
    ('share/man/man8', ['ddupdate.8', 'ddupdate-config.8']),
    ('share/man/man5', ['ddupdate.conf.5']),
    ('share/ddupdate/plugins', glob('plugins/*.py')),
    ('share/ddupdate/dispatcher.d', ['dispatcher.d/50-ddupdate']),
    ('share/ddupdate/systemd', glob('systemd/*'))
]


class _ProjectClean(clean):
    """Actually clean up everything generated."""

    def run(self):
        super().run()
        paths = ['build', 'install', 'dist', 'lib/ddupdate.egg-info']
        for path in paths:
            if os.path.exists(path):
                shutil.rmtree(path)

class _ProjectInstall(install):
    """Log used installation paths."""

    def run(self):
        super().run()
        from distutils.fancy_getopt import longopt_xlate
        s = ""
        install_lib = ""
        for (option, _, _) in self.user_options:
            option = option.translate(longopt_xlate)
            if option[-1] == "=":
                option = option[:-1]
            try:
                value = getattr(self, option)
            except AttributeError:
                continue
            if option == "install_lib":
                install_lib = value
            s += option + " = " + (str(value) if value else "") + "\n"
        if not install_lib:
            print("Warning: cannot create platform install paths file")
            return
        path = install_lib + "/ddupdate/install.conf"
        print("Creating install config file " + path)
        with open(path, "w") as f:
            f.write("[install]\n")
            f.write(s)


setup(
    name='ddupdate',
    version='0.6.6',
    description='Update dns data for dynamic ip addresses',
    long_description=open(ROOT + '/README.md').read(),
    include_package_data=True,
    license='MIT',
    url='http://github.com/leamas/ddupdate',
    author='Alec Leamas',
    author_email='alec.leamas@nowhere.net',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'Topic :: System :: Networking',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.4',
    ],
    keywords=['dyndns', 'dhcp', 'dns'],
    package_dir={'': 'lib'},
    packages=['ddupdate'],
    scripts=['ddupdate', 'ddupdate-config'],
    data_files=DATA,
    cmdclass={'clean': _ProjectClean, 'install': _ProjectInstall}
)
