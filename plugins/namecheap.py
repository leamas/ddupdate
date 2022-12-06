"""
ddupdate plugin updating data on namecheap.com

See: ddupdate(8)
See: https://www.namecheap.com/support/knowledgebase/article.aspx/29/11/how-to-dynamically-update-the-hosts-ip-with-an-http-request/

"""
from ddupdate.ddplugin import ServicePlugin, ServiceError
from ddupdate.ddplugin import get_response, get_netrc_auth
import xml.etree.ElementTree as ET

class NamecheapPlugin(ServicePlugin):
    """
    Update a dns entry on namecheap.com

    As usual, any host updated must first be defined in the web UI.
    Supports most address plugins including default-web-ip, default-if
    and ip-disabled. ipv6 is supported

    Access to the service requires an API token. This is available in the
    website account.

    netrc: Use a line like
        machine namecheap.com login {domainname} password {namecheap hostname passwd}

    Options:
        None
    """

    _name = 'namecheap.com'
    _oneliner = 'Updates on http://namecheap.com'
    _url = "https://dynamicdns.park-your-domain.com/update?host={0}&domain={1}&ip={2}&password={3}"

    def _etree_to_dict(self, t):
        """ https://stackoverflow.com/questions/7684333/converting-xml-to-dictionary-using-elementtree/68082847#68082847 """
        if type(t) is ET.ElementTree: return self._etree_to_dict(t.getroot())
        return {
            **t.attrib,
            'text': t.text,
            **{e.tag: self._etree_to_dict(e) for e in t}
        }

    def register(self, log, hostname, ip, options):
        """Implement ServicePlugin.register()."""

        password = get_netrc_auth(self._name)[1]
        # domain is last two elements of 'host'
        domain = '.'.join(hostname.split('.')[-2:])
        # hostname is everything above the last two elements of 'host'
        host = '.'.join(hostname.split('.')[:-2])
	# handle the special case of co.uk 
	# it is the only second-level domain namecheap support
	if domain == "co.uk":
		domain = '.'.join(hostname.split('.')[-3:])
		host = '.'.join(hostname.split('.')[:-3])
        # ip address is either an ipv4 or ipv6
        ip = ip.v4 if ip.v4 else ip.v6

        url = self._url.format(host, domain, ip, password)
        html = get_response(log, url)

        tree = ET.ElementTree(ET.fromstring(html))
        resp = self._etree_to_dict(tree)

        if resp['errors']['text'] is not None:
            raise ServiceError("Update error, got: " + resp['errors']['text'])
