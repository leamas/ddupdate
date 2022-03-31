import keyring
import netrc
import sys

def main():
    _netrc = netrc.netrc()
    for host in _netrc.hosts:
        login, account, password = _netrc.authenticators(host) 
        print(host)
        credentials = "{0}\t{1}".format((login or 'api_key'), password)
        keyring.set_password('ddupdate', host, credentials)

if __name__ == '__main__':
    main()
