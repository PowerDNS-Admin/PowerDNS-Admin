import sys
from typing import NamedTuple, Optional

if sys.version_info >= (3, 8):
    from typing import Final
else:
    from typing_extensions import Final

class __KeyData(NamedTuple):  # __KeyData type
    name: str
    href: Optional[str]

class __Transform(NamedTuple):  # __Transform type
    name: str
    href: Optional[str]
    usage: int

DSigNs: Final = 'http://www.w3.org/2000/09/xmldsig#'
EncNs: Final = 'http://www.w3.org/2001/04/xmlenc#'
KeyDataAes: Final = __KeyData('aes', 'http://www.aleksey.com/xmlsec/2002#AESKeyValue')
KeyDataDes: Final = __KeyData('des', 'http://www.aleksey.com/xmlsec/2002#DESKeyValue')
KeyDataDsa: Final = __KeyData('dsa', 'http://www.w3.org/2000/09/xmldsig#DSAKeyValue')
KeyDataEcdsa: Final = __KeyData('ecdsa', 'http://scap.nist.gov/specifications/tmsad/#resource-1.0')
KeyDataEncryptedKey: Final = __KeyData('enc-key', 'http://www.w3.org/2001/04/xmlenc#EncryptedKey')
KeyDataFormatBinary: Final = 1
KeyDataFormatCertDer: Final = 8
KeyDataFormatCertPem: Final = 7
KeyDataFormatDer: Final = 3
KeyDataFormatPem: Final = 2
KeyDataFormatPkcs12: Final = 6
KeyDataFormatPkcs8Der: Final = 5
KeyDataFormatPkcs8Pem: Final = 4
KeyDataFormatUnknown: Final = 0
KeyDataHmac: Final = __KeyData('hmac', 'http://www.aleksey.com/xmlsec/2002#HMACKeyValue')
KeyDataName: Final = __KeyData('key-name', None)
KeyDataRawX509Cert: Final = __KeyData('raw-x509-cert', 'http://www.w3.org/2000/09/xmldsig#rawX509Certificate')
KeyDataRetrievalMethod: Final = __KeyData('retrieval-method', None)
KeyDataRsa: Final = __KeyData('rsa', 'http://www.w3.org/2000/09/xmldsig#RSAKeyValue')
KeyDataTypeAny: Final = 65535
KeyDataTypeNone: Final = 0
KeyDataTypePermanent: Final = 16
KeyDataTypePrivate: Final = 2
KeyDataTypePublic: Final = 1
KeyDataTypeSession: Final = 8
KeyDataTypeSymmetric: Final = 4
KeyDataTypeTrusted: Final = 256
KeyDataTypeUnknown: Final = 0
KeyDataValue: Final = __KeyData('key-value', None)
KeyDataX509: Final = __KeyData('x509', 'http://www.w3.org/2000/09/xmldsig#X509Data')
NodeCanonicalizationMethod: Final = 'CanonicalizationMethod'
NodeCipherData: Final = 'CipherData'
NodeCipherReference: Final = 'CipherReference'
NodeCipherValue: Final = 'CipherValue'
NodeDataReference: Final = 'DataReference'
NodeDigestMethod: Final = 'DigestMethod'
NodeDigestValue: Final = 'DigestValue'
NodeEncryptedData: Final = 'EncryptedData'
NodeEncryptedKey: Final = 'EncryptedKey'
NodeEncryptionMethod: Final = 'EncryptionMethod'
NodeEncryptionProperties: Final = 'EncryptionProperties'
NodeEncryptionProperty: Final = 'EncryptionProperty'
NodeKeyInfo: Final = 'KeyInfo'
NodeKeyName: Final = 'KeyName'
NodeKeyReference: Final = 'KeyReference'
NodeKeyValue: Final = 'KeyValue'
NodeManifest: Final = 'Manifest'
NodeObject: Final = 'Object'
NodeReference: Final = 'Reference'
NodeReferenceList: Final = 'ReferenceList'
NodeSignature: Final = 'Signature'
NodeSignatureMethod: Final = 'SignatureMethod'
NodeSignatureProperties: Final = 'SignatureProperties'
NodeSignatureValue: Final = 'SignatureValue'
NodeSignedInfo: Final = 'SignedInfo'
NodeX509Data: Final = 'X509Data'
Ns: Final = 'http://www.aleksey.com/xmlsec/2002'
NsExcC14N: Final = 'http://www.w3.org/2001/10/xml-exc-c14n#'
NsExcC14NWithComments: Final = 'http://www.w3.org/2001/10/xml-exc-c14n#WithComments'
Soap11Ns: Final = 'http://schemas.xmlsoap.org/soap/envelope/'
Soap12Ns: Final = 'http://www.w3.org/2002/06/soap-envelope'
TransformAes128Cbc: Final = __Transform('aes128-cbc', 'http://www.w3.org/2001/04/xmlenc#aes128-cbc', 16)
TransformAes128Gcm: Final = __Transform('aes128-gcm', 'http://www.w3.org/2009/xmlenc11#aes128-gcm', 16)
TransformAes192Cbc: Final = __Transform('aes192-cbc', 'http://www.w3.org/2001/04/xmlenc#aes192-cbc', 16)
TransformAes192Gcm: Final = __Transform('aes192-gcm', 'http://www.w3.org/2009/xmlenc11#aes192-gcm', 16)
TransformAes256Cbc: Final = __Transform('aes256-cbc', 'http://www.w3.org/2001/04/xmlenc#aes256-cbc', 16)
TransformAes256Gcm: Final = __Transform('aes256-gcm', 'http://www.w3.org/2009/xmlenc11#aes256-gcm', 16)
TransformDes3Cbc: Final = __Transform('tripledes-cbc', 'http://www.w3.org/2001/04/xmlenc#tripledes-cbc', 16)
TransformDsaSha1: Final = __Transform('dsa-sha1', 'http://www.w3.org/2000/09/xmldsig#dsa-sha1', 8)
TransformEcdsaSha1: Final = __Transform('ecdsa-sha1', 'http://www.w3.org/2001/04/xmldsig-more#ecdsa-sha1', 8)
TransformEcdsaSha224: Final = __Transform('ecdsa-sha224', 'http://www.w3.org/2001/04/xmldsig-more#ecdsa-sha224', 8)
TransformEcdsaSha256: Final = __Transform('ecdsa-sha256', 'http://www.w3.org/2001/04/xmldsig-more#ecdsa-sha256', 8)
TransformEcdsaSha384: Final = __Transform('ecdsa-sha384', 'http://www.w3.org/2001/04/xmldsig-more#ecdsa-sha384', 8)
TransformEcdsaSha512: Final = __Transform('ecdsa-sha512', 'http://www.w3.org/2001/04/xmldsig-more#ecdsa-sha512', 8)
TransformEnveloped: Final = __Transform('enveloped-signature', 'http://www.w3.org/2000/09/xmldsig#enveloped-signature', 1)
TransformExclC14N: Final = __Transform('exc-c14n', 'http://www.w3.org/2001/10/xml-exc-c14n#', 3)
TransformExclC14NWithComments: Final = __Transform(
    'exc-c14n-with-comments', 'http://www.w3.org/2001/10/xml-exc-c14n#WithComments', 3
)
TransformHmacMd5: Final = __Transform('hmac-md5', 'http://www.w3.org/2001/04/xmldsig-more#hmac-md5', 8)
TransformHmacRipemd160: Final = __Transform('hmac-ripemd160', 'http://www.w3.org/2001/04/xmldsig-more#hmac-ripemd160', 8)
TransformHmacSha1: Final = __Transform('hmac-sha1', 'http://www.w3.org/2000/09/xmldsig#hmac-sha1', 8)
TransformHmacSha224: Final = __Transform('hmac-sha224', 'http://www.w3.org/2001/04/xmldsig-more#hmac-sha224', 8)
TransformHmacSha256: Final = __Transform('hmac-sha256', 'http://www.w3.org/2001/04/xmldsig-more#hmac-sha256', 8)
TransformHmacSha384: Final = __Transform('hmac-sha384', 'http://www.w3.org/2001/04/xmldsig-more#hmac-sha384', 8)
TransformHmacSha512: Final = __Transform('hmac-sha512', 'http://www.w3.org/2001/04/xmldsig-more#hmac-sha512', 8)
TransformInclC14N: Final = __Transform('c14n', 'http://www.w3.org/TR/2001/REC-xml-c14n-20010315', 3)
TransformInclC14N11: Final = __Transform('c14n11', 'http://www.w3.org/2006/12/xml-c14n11', 3)
TransformInclC14N11WithComments: Final = __Transform(
    'c14n11-with-comments', 'http://www.w3.org/2006/12/xml-c14n11#WithComments', 3
)
TransformInclC14NWithComments: Final = __Transform(
    'c14n-with-comments',
    'http://www.w3.org/TR/2001/REC-xml-c14n-20010315#WithComments',
    3,
)
TransformKWAes128: Final = __Transform('kw-aes128', 'http://www.w3.org/2001/04/xmlenc#kw-aes128', 16)
TransformKWAes192: Final = __Transform('kw-aes192', 'http://www.w3.org/2001/04/xmlenc#kw-aes192', 16)
TransformKWAes256: Final = __Transform('kw-aes256', 'http://www.w3.org/2001/04/xmlenc#kw-aes256', 16)
TransformKWDes3: Final = __Transform('kw-tripledes', 'http://www.w3.org/2001/04/xmlenc#kw-tripledes', 16)
TransformMd5: Final = __Transform('md5', 'http://www.w3.org/2001/04/xmldsig-more#md5', 4)
TransformRemoveXmlTagsC14N: Final = __Transform('remove-xml-tags-transform', None, 3)
TransformRipemd160: Final = __Transform('ripemd160', 'http://www.w3.org/2001/04/xmlenc#ripemd160', 4)
TransformRsaMd5: Final = __Transform('rsa-md5', 'http://www.w3.org/2001/04/xmldsig-more#rsa-md5', 8)
TransformRsaOaep: Final = __Transform('rsa-oaep-mgf1p', 'http://www.w3.org/2001/04/xmlenc#rsa-oaep-mgf1p', 16)
TransformRsaPkcs1: Final = __Transform('rsa-1_5', 'http://www.w3.org/2001/04/xmlenc#rsa-1_5', 16)
TransformRsaRipemd160: Final = __Transform('rsa-ripemd160', 'http://www.w3.org/2001/04/xmldsig-more#rsa-ripemd160', 8)
TransformRsaSha1: Final = __Transform('rsa-sha1', 'http://www.w3.org/2000/09/xmldsig#rsa-sha1', 8)
TransformRsaSha224: Final = __Transform('rsa-sha224', 'http://www.w3.org/2001/04/xmldsig-more#rsa-sha224', 8)
TransformRsaSha256: Final = __Transform('rsa-sha256', 'http://www.w3.org/2001/04/xmldsig-more#rsa-sha256', 8)
TransformRsaSha384: Final = __Transform('rsa-sha384', 'http://www.w3.org/2001/04/xmldsig-more#rsa-sha384', 8)
TransformRsaSha512: Final = __Transform('rsa-sha512', 'http://www.w3.org/2001/04/xmldsig-more#rsa-sha512', 8)
TransformSha1: Final = __Transform('sha1', 'http://www.w3.org/2000/09/xmldsig#sha1', 4)
TransformSha224: Final = __Transform('sha224', 'http://www.w3.org/2001/04/xmldsig-more#sha224', 4)
TransformSha256: Final = __Transform('sha256', 'http://www.w3.org/2001/04/xmlenc#sha256', 4)
TransformSha384: Final = __Transform('sha384', 'http://www.w3.org/2001/04/xmldsig-more#sha384', 4)
TransformSha512: Final = __Transform('sha512', 'http://www.w3.org/2001/04/xmlenc#sha512', 4)
TransformUsageAny: Final = 65535
TransformUsageC14NMethod: Final = 2
TransformUsageDSigTransform: Final = 1
TransformUsageDigestMethod: Final = 4
TransformUsageEncryptionMethod: Final = 16
TransformUsageSignatureMethod: Final = 8
TransformUsageUnknown: Final = 0
TransformVisa3DHack: Final = __Transform('Visa3DHackTransform', None, 1)
TransformXPath: Final = __Transform('xpath', 'http://www.w3.org/TR/1999/REC-xpath-19991116', 1)
TransformXPath2: Final = __Transform('xpath2', 'http://www.w3.org/2002/06/xmldsig-filter2', 1)
TransformXPointer: Final = __Transform('xpointer', 'http://www.w3.org/2001/04/xmldsig-more/xptr', 1)
TransformXslt: Final = __Transform('xslt', 'http://www.w3.org/TR/1999/REC-xslt-19991116', 1)
TypeEncContent: Final = 'http://www.w3.org/2001/04/xmlenc#Content'
TypeEncElement: Final = 'http://www.w3.org/2001/04/xmlenc#Element'
XPath2Ns: Final = 'http://www.w3.org/2002/06/xmldsig-filter2'
XPathNs: Final = 'http://www.w3.org/TR/1999/REC-xpath-19991116'
XPointerNs: Final = 'http://www.w3.org/2001/04/xmldsig-more/xptr'
