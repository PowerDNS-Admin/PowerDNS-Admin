from OpenSSL import crypto
from datetime import datetime
import pytz
import os
CRYPT_PATH = os.path.abspath(os.path.dirname(os.path.realpath(__file__))  + "/../../")
CERT_FILE = CRYPT_PATH + "/saml_cert.crt"
KEY_FILE = CRYPT_PATH + "/saml_cert.key"


def check_certificate():
    if not os.path.isfile(CERT_FILE):
        return False
    st_cert = open(CERT_FILE, 'rt').read()
    cert = crypto.load_certificate(crypto.FILETYPE_PEM, st_cert)
    now = datetime.now(pytz.utc)
    begin = datetime.strptime(cert.get_notBefore(), "%Y%m%d%H%M%SZ").replace(tzinfo=pytz.UTC)
    begin_ok = begin < now
    end = datetime.strptime(cert.get_notAfter(), "%Y%m%d%H%M%SZ").replace(tzinfo=pytz.UTC)
    end_ok = end > now
    if begin_ok and end_ok:
        return True
    return False

def create_self_signed_cert():

    # create a key pair
    k = crypto.PKey()
    k.generate_key(crypto.TYPE_RSA, 2048)

    # create a self-signed cert
    cert = crypto.X509()
    cert.get_subject().C = "DE"
    cert.get_subject().ST = "NRW"
    cert.get_subject().L = "Dortmund"
    cert.get_subject().O = "Dummy Company Ltd"
    cert.get_subject().OU = "Dummy Company Ltd"
    cert.get_subject().CN = "PowerDNS-Admin"
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(10*365*24*60*60)
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(k)
    cert.sign(k, 'sha256')

    open(CERT_FILE, "wt").write(
        crypto.dump_certificate(crypto.FILETYPE_PEM, cert))
    open(KEY_FILE, "wt").write(
        crypto.dump_privatekey(crypto.FILETYPE_PEM, k))