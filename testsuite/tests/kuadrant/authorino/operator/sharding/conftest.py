"""Conftest for authorino sharding tests"""
import pytest

from testsuite.objects import Value, JsonResponse
from testsuite.openshift.envoy import Envoy
from testsuite.openshift.objects.auth_config import AuthConfig


@pytest.fixture(scope="module")
def envoy(request, authorino, openshift, blame, backend, testconfig):
    """Envoy"""

    def _envoy(auth=authorino):
        name = blame("envoy")
        envoy = Envoy(openshift, auth, name, blame("label"), backend, testconfig["envoy"]["image"])
        request.addfinalizer(envoy.delete)
        envoy.commit()
        route = envoy.expose_hostname(name)
        return route

    return _envoy


# pylint: disable=unused-argument
@pytest.fixture(scope="module")
def authorization(request, authorino, blame, openshift, module_label):
    """In case of Authorino, AuthConfig used for authorization"""

    def _authorization(hostname=None, sharding_label=None):
        auth = AuthConfig.create_instance(
            openshift,
            blame("ac"),
            None,
            hostnames=[hostname],
            labels={"testRun": module_label, "sharding": sharding_label},
        )
        auth.responses.add_success_header("header", JsonResponse({"anything": Value(sharding_label)}))
        request.addfinalizer(auth.delete)
        auth.commit()
        return auth

    return _authorization


@pytest.fixture(scope="module", autouse=True)
def commit():
    """Ensure no default resources are created"""
    return
