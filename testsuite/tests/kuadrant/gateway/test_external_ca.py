"""
This module contains the most basic happy path test for both DNSPolicy and TLSPolicy
for a cluster with Let's Encrypt ClusterIssuer

Prerequisites:
* multi-cluster-gateways ns is created and set as openshift["project"]
* managedclustersetbinding is created in openshift["project"]
* gateway class "kuadrant-multi-cluster-gateway-instance-per-cluster" is created
* cert-manager Operator installed
* Let's Encrypt ClusterIssuer object configured on the cluster matching the template:
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-staging
spec:
  acme:
    email: <email_address>
    preferredChain: ISRG Root X1
    privateKeySecretRef:
      name: letsencrypt-private-key
    server: 'https://acme-staging-v02.api.letsencrypt.org/directory'
    solvers:
      - dns01:
          route53:
            accessKeyID: <aws_key_id>
            hostedZoneID: <hosted_zone_id>
            region: <region_name>
            secretAccessKeySecretRef:
              key: awsSecretAccessKey
              name: aws-secret
"""

import dataclasses
import time
from importlib import resources

import pytest
from openshift_client import selector
from openshift_client.model import OpenShiftPythonException

from testsuite.gateway import CustomReference

pytestmark = [pytest.mark.kuadrant_only]


@pytest.fixture(scope="module")
def cluster_issuer(testconfig, hub_openshift):
    """Reference to cluster Let's Encrypt certificate issuer"""
    testconfig.validators.validate(only="letsencrypt")
    name = testconfig["letsencrypt"]["clusterissuer"]
    try:
        selector(f"clusterissuer/{name}", static_context=hub_openshift.context).object()
    except OpenShiftPythonException as exc:
        pytest.skip(f"{name} ClusterIssuer is not present on the cluster: {exc}")
    return CustomReference(
        group="cert-manager.io",
        kind="ClusterIssuer",
        name=name,
    )


@pytest.fixture(scope="module")
def client(commit, hostname, gateway):  # pylint: disable=unused-argument
    """Returns httpx client to be used for requests, it also commits AuthConfig"""
    time.sleep(180)  # it takes a bit for the lets encrypt secret to be actually created
    root_cert = resources.files("testsuite.resources").joinpath("letsencrypt-stg-root-x1.pem").read_text()
    old_cert = gateway.get_tls_cert()
    cert = dataclasses.replace(old_cert, chain=old_cert.certificate + root_cert)
    client = hostname.client(verify=cert)
    yield client
    client.close()


def test_smoke_letsencrypt(client, auth):
    """
    Tests whether the backend, exposed using the HTTPRoute and Gateway, was exposed correctly,
    having a tls secured endpoint with a hostname managed by MGC
    """

    result = client.get("/get", auth=auth)
    assert not result.has_dns_error()
    assert not result.has_cert_verify_error()
    assert result.status_code == 200