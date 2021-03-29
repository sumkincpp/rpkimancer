import argparse
import ipaddress
import os

from cryptography.hazmat.primitives import serialization

from .econtent import RpkiSignedURIList
from .cert import make_cert

DEMO_ASN = 37271
DEMO_URI = "https://as37271.fyi/static/net_info_portal/md/bgp-communities.md"
COMMUNITY_DEFS_OID = (1, 3, 6, 1, 4, 1, 35743, 3)
DEMO_PUBLICATION_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                     "target", "demo", "rpki")


def demo():
    parser = argparse.ArgumentParser()
    parser.add_argument("--uri", nargs="+", default=[DEMO_URI],
                        dest="uri_list",
                        help="URIs to retrive and hash")
    parser.add_argument("--asn", default=DEMO_ASN,
                        help="ASN to include in resources")
    parser.add_argument("--content-type", default=COMMUNITY_DEFS_OID,
                        help="Content type of hashed data")
    args = parser.parse_args()
    rsu = RpkiSignedURIList(*args.uri_list,
                            version=0,
                            resources=dict(asID=[("id", args.asn)]),
                            type=args.content_type)
    # create TA
    ta_cert = make_cert(ip_resources=[ipaddress.ip_network("0.0.0.0/0"),
                                      ipaddress.ip_network("::/0")],
                        as_resources=[(0, 4294967295)])
    os.makedirs(os.path.join(DEMO_PUBLICATION_PATH, "TA"), exist_ok=True)
    with open(os.path.join(DEMO_PUBLICATION_PATH, "TA.cer"), "wb") as f:
        f.write(ta_cert.public_bytes(serialization.Encoding.DER))
    # create CA2
    ca_cert_parent = make_cert(common_name="CA1", issuer=ta_cert,
                               ip_resources=[ipaddress.ip_network("41.78.188.0/22"),
                                             ipaddress.ip_network("197.157.64.0/19")],
                               as_resources=[37271])
    os.makedirs(os.path.join(DEMO_PUBLICATION_PATH, "CA1"), exist_ok=True)
    with open(os.path.join(DEMO_PUBLICATION_PATH, "TA", "CA1.cer"), "wb") as f:
        f.write(ca_cert_parent.public_bytes(serialization.Encoding.DER))
    # create CA2
    ca_cert_child = make_cert(common_name="CA2", issuer=ca_cert_parent,
                              as_resources=[37271])
    os.makedirs(os.path.join(DEMO_PUBLICATION_PATH, "CA2"), exist_ok=True)
    with open(os.path.join(DEMO_PUBLICATION_PATH, "TA", "CA2.cer"), "wb") as f:
        f.write(ca_cert_child.public_bytes(serialization.Encoding.DER))
    # create RSU
    print(rsu.to_asn1())


if __name__ == "__main__":
    demo()
