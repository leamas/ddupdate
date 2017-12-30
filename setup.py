''' ddupdate install data. '''

import os
from glob import glob
from setuptools import setup

# pylint: disable=bad-continuation
ROOT = os.path.dirname(__file__)
ROOT = ROOT if ROOT else '.'

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
        ('share/doc/ddupdate',
            ['README.rst', 'LICENSE.txt', 'ddupdate.8.html']),
        ('share/ddupdate/dispatcher.d', ['dispatcher.d/50-ddupdate'])
    ]

setup(
    name='ddupdate',
    version='0.0.4',
    description='Update dns data for dynamic ip addresses',
    long_description=open(ROOT + '/README.rst').read(),
    license='MIT',
    url='http://github.com/leamas/ddupdate',
    author='Alec Leamas',
    author_email='alec.leamas@nowhere.net',
    install_requires=['straight.plugin'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: End Users/Desktop',
        'Topic :: System :: Networking',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.4',
    ],
    keywords=['dyndns', 'dhcp', 'dns'],
    package_dir={'': 'lib'},
    packages=['ddupdate'],
    scripts=['ddupdate'],
    data_files=DATA
)
