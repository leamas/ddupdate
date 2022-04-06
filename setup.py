"""ddupdate install data."""

# pylint: disable=bad-option-value, import-outside-toplevel
# pylint: disable=consider-using-with

import shutil
import os
import subprocess

from distutils.command.clean import clean
from distutils.command.install import install

from glob import glob
from setuptools import setup

ROOT = os.path.dirname(__file__)
ROOT = ROOT if ROOT else '.'


def systemd_unitdir():
    """Return the official systemd user unit dir path."""
    cmd = 'pkg-config systemd --variable=systemduserunitdir'.split()
    try:
        return subprocess.check_output(cmd).decode().strip()
    except (OSError, subprocess.CalledProcessError):
        return "/usr/lib/systemd/user"


DATA = [
    (systemd_unitdir(), glob('systemd/*')),
    ('share/bash-completion/completions/', ['bash_completion.d/ddupdate']),
    ('share/man/man8', ['ddupdate.8', 'ddupdate-config.8',
                        'ddupdate-netrc-to-keyring.8']),
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
        final_prefix = None
        if 'FINAL_PREFIX' in os.environ:
            final_prefix = os.environ['FINAL_PREFIX']
        if final_prefix:
            # Strip leading prefix in paths like /usr/lib/systemd,
            # avoiding /usr/usr when applying the prefix
            if DATA[0][0].startswith(self.prefix):
                DATA[0] = (DATA[0][0][len(self.prefix) + 1:], DATA[0][1])
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
            if final_prefix and self.root:
                value = str(value).replace(self.root, final_prefix)
            elif final_prefix and self.prefix:
                value = str(value).replace(self.prefix, final_prefix)
            value = str(value).replace('//', '/')
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
    version='0.7.1',
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
    scripts=['ddupdate', 'ddupdate-config', 'ddupdate_netrc_to_keyring'],
    data_files=DATA,
    cmdclass={'clean': _ProjectClean, 'install': _ProjectInstall}
)
