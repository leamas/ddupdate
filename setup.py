''' ddupdate install data. '''

import os
from glob import glob
from setuptools import setup

if 'USER_INSTALL_FIX' in os.environ:
    USER_SHARE = os.path.expanduser('~/.local/share/')
    DATA = [
        (os.path.join(USER_SHARE, 'plugins'), glob('plugins/*.py')),
        (os.path.join(USER_SHARE, 'man/man8'), ['ddupdate.8']),
        (os.path.expanduser('~/bin'), ['ddupdate'])
    ]
else:
    DATA = [
        ('share/ddupdate/plugins', glob('plugins/*.py')),
        ('/etc', ['ddupdate.conf']),
        ('/lib/systemd/system', glob('systemd/*')),
        ('share/man/man8', ['ddupdate.8']),
        ('share/doc/ddupdate', ['README.md', 'COPYING'])
    ]

setup(
    name='ddupdate',
    version='0.0.1',
    description='Update dns data for dynamic IP addresses',
    license='MIT',
    url='http://github.com/TBD',
    author='Alec Leamas',
    author_email='alec.leamas@nowhere.net',
    py_modules=['ddupdate'],
    scripts=['ddupdate'],
    data_files=DATA
)
