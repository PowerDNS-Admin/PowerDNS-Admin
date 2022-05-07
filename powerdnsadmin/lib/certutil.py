import datetime
import os

from cryptography import x509
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.x509.oid import NameOID


CRYPT_PATH = os.path.abspath(os.path.dirname(os.path.realpath(__file__)) + "/../../")
CERT_FILE = CRYPT_PATH + "/saml_cert.crt"
KEY_FILE = CRYPT_PATH + "/saml_cert.key"


def create_self_signed_cert():
    """ Generate a new self-signed RSA-2048-SHA256 x509 certificate. """
    # Generate our key
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # Write our key to disk for safe keeping
    with open(KEY_FILE, "wb") as key_file:
        key_file.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))

    # Various details about who we are. For a self-signed certificate the
    # subject and issuer are always the same.
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "DE"),
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "NRW"),
        x509.NameAttribute(NameOID.LOCALITY_NAME, "Dortmund"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Dummy Company Ltd"),
        x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "Dummy Company Ltd"),
        x509.NameAttribute(NameOID.COMMON_NAME, "PowerDNS-Admin"),
    ])

    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow()
    ).not_valid_after(
        datetime.datetime.utcnow() + datetime.timedelta(days=10*365)
    ).sign(key, hashes.SHA256())

    # Write our certificate out to disk.
    with open(CERT_FILE, "wb") as cert_file:
        cert_file.write(cert.public_bytes(serialization.Encoding.PEM))
