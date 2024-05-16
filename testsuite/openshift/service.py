"""Service related objects"""

from dataclasses import dataclass, asdict
from typing import Literal

from testsuite.openshift import OpenShiftObject


@dataclass
class ServicePort:
    """Kubernetes Service Port object"""

    name: str
    port: int
    targetPort: int | str  # pylint: disable=invalid-name


class Service(OpenShiftObject):
    """Kubernetes Service object"""

    @classmethod
    def create_instance(
        cls,
        openshift,
        name,
        selector: dict[str, str],
        ports: list[ServicePort],
        labels: dict[str, str] = None,
        service_type: Literal["ClusterIP", "LoadBalancer", "NodePort", "ExternalName"] = None,
    ):
        """Creates new Service"""
        model: dict = {
            "kind": "Service",
            "apiVersion": "v1",
            "metadata": {
                "name": name,
                "labels": labels,
            },
            "spec": {"ports": [asdict(port) for port in ports], "selector": selector},
        }

        if service_type is not None:
            model["spec"]["type"] = service_type

        return cls(model, context=openshift.context)

    def get_port(self, name):
        """Returns port definition for a port with said name"""
        for port in self.model.spec.ports:
            if port["name"] == name:
                return port
        raise KeyError(f"No port with name {name} exists")

    @property
    def external_ip(self):
        """Returns LoadBalancer IP for this service"""
        if self.model.spec.type != "LoadBalancer":
            raise AttributeError("External IP can be only used with LoadBalancer services")
        return self.model.status.loadBalancer.ingress[0].ip

    def delete(self, **kwargs):
        """Deletes the resource and raises the timeout if type is LoadBalancer"""
        if self.model.spec.type == "LoadBalancer":
            return super().delete(timeout_sec=180, **kwargs)
        return super().delete(**kwargs)
