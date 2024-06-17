import pytest
import yaml

from importlib import resources
from testsuite.kuadrantctl import KuadrantctlClient


@pytest.fixture(scope="session")
def oas_example():
    path = resources.files("testsuite.resources").joinpath("petstore-openapi.yaml")
    with path.open("r", encoding="UTF-8") as stream:
        return yaml.safe_load(stream)


@pytest.fixture(scope="module")
def commit():
    return


@pytest.fixture(scope="session")
def kuadrantctl(testconfig, skip_or_fail, openshift):
    kctl = KuadrantctlClient(binary=testconfig["kuadrantctl"], openshift=openshift)
    if not kctl.exists:
        skip_or_fail("Skipping Kuadrantctl tests as kuadrantctl binary path is not properly configured")
    return kctl
