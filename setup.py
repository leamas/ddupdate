"""ddupdate install data."""

import shutil
import os
import subprocess

from distutils.command.clean import clean
from glob import glob
from setuptools import setup

# pylint: disable=bad-continuation
ROOT = os.path.dirname(__file__)
ROOT = ROOT if ROOT else '.'


def systemd_unitdir():
    """Return the official systemd unit dir path."""
    cmd = 'pkg-config systemd --variable=systemdsystemunitdir'.split()
    try:
        return subprocess.check_output(cmd).decode().strip()
    except (OSError, subprocess.CalledProcessError):
        return "/usr/lib/systemd/system"


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


setup(
    name='ddupdate',
    version='0.6.3',
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
    cmdclass={'clean': _ProjectClean}
)
