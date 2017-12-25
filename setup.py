from setuptools import setup
from glob import glob
import os

if 'USER_INSTALL_FIX' in os.environ:
    user_share = os.path.expanduser('~/.local/share/')
    data = [
        (os.path.join(user_share, 'plugins'), glob('plugins/*.py')),
        (os.path.join(user_share, 'man/man8'), ['ddupdate.8']),
        (os.path.expanduser('~/bin'), ['ddupdate'])
    ]
else:
    data = [
        ('share/ddupdate/plugins', glob('plugins/*.py')),
        ('/etc', ['ddupdate.conf']),
        ('/lib/systemd/system', glob('systemd/*')),
        ('/usr/share/man/man8', ['ddupdate.8'])
    ]

setup(
    name='ddupdate',
    version = '0.0.1',
    description = 'Update dns data for dynamic IP addresses',
    license = 'MIT',
    url = 'http://github.com/TBD',
    author = 'Alec Leamas',
    author_email = 'alec.leamas@nowhere.net',
    py_modules = ['ddupdate'],
    scripts = ['ddupdate'],
    data_files = data
)
