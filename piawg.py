import os
import requests
import json
from requests_toolbelt.adapters import host_header_ssl
import ssl
import urllib3
import subprocess
import urllib.parse

# PIA uses the CN attribute for certificates they issue themselves.
# This will be deprecated by urllib3 at some point in the future, and generates a warning (that we ignore).
urllib3.disable_warnings(urllib3.exceptions.SubjectAltNameWarning)

_CA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ca.rsa.4096.crt')


class _PIAAdapter(host_header_ssl.HostHeaderSSLAdapter):
    # Python 3.13+ rejects PIA's CA unless VERIFY_X509_STRICT is cleared.
    # Chain and hostname checks stay on.
    def init_poolmanager(self, connections, maxsize, block=False, **pool_kwargs):
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        if hasattr(ssl, 'VERIFY_X509_STRICT'):
            ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
        ctx.load_verify_locations(_CA_PATH)
        ctx.check_hostname = False
        pool_kwargs['ssl_context'] = ctx
        return super().init_poolmanager(connections, maxsize, block=block, **pool_kwargs)


def _pia_session():
    session = requests.Session()
    session.mount('https://', _PIAAdapter())
    session.verify = _CA_PATH
    return session


class piawg:
    def __init__(self):
        self.server_list = {}
        self.get_server_list()
        self.region = None
        self.token = None
        self.publickey = None
        self.privatekey = None
        self.connection = None

    def get_server_list(self):
        r = requests.get('https://serverlist.piaservers.net/vpninfo/servers/v4')
        # Only process first line of response, there's some base64 data at the end we're ignoring
        data = json.loads(r.text.splitlines()[0])
        for server in data['regions']:
            self.server_list[server['name']] = server

    def set_region(self, region_name):
        self.region = region_name

    def get_token(self, username, password):
        # Regional meta servers now present an ExpressVPN certificate, which the
        # bundled PIA CA cannot verify. PIA's current token API uses a public cert.
        r = requests.post('https://www.privateinternetaccess.com/api/client/v2/token',
                          data={'username': username, 'password': password})
        try:
            data = r.json()
        except ValueError:
            return False
        if r.status_code == 200 and data.get('token'):
            self.token = data['token']
            return True
        else:
            return False

    def generate_keys(self):
        self.privatekey = subprocess.run(['wg', 'genkey'], stdout=subprocess.PIPE, encoding="utf-8").stdout.strip()
        self.publickey = subprocess.run(['wg', 'pubkey'], input=self.privatekey, stdout=subprocess.PIPE,
                                        encoding="utf-8").stdout.strip()

    def addkey(self):
        # Get common name and IP address for wireguard endpoint in region
        cn = self.server_list[self.region]['servers']['wg'][0]['cn']
        ip = self.server_list[self.region]['servers']['wg'][0]['ip']

        # Verify PIA's certificate even though the request goes to an IP.
        # https://toolbelt.readthedocs.io/en/latest/adapters.html#requests_toolbelt.adapters.host_header_ssl.HostHeaderSSLAdapter
        s = _pia_session()

        r = s.get("https://{}:1337/addKey?pt={}&pubkey={}".format(ip, urllib.parse.quote(self.token),
                                                                  urllib.parse.quote(self.publickey)), headers={"Host": cn})
        if r.status_code == 200 and r.json()['status'] == 'OK':
            self.connection = r.json()
            return True, r.content
        else:
            return False, r.content
