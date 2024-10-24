"""Deployment related objects"""

from dataclasses import dataclass
from typing import Any

import openshift_client as oc

from testsuite.openshift import OpenShiftObject, Selector, modify
from testsuite.utils import asdict

# pylint: disable=invalid-name


@dataclass
class VolumeMount:
    """Deployment VolumeMount object"""

    mountPath: str
    name: str
    readOnly: bool = True


@dataclass
class ConfigMapVolume:
    """Deployment ConfigMapVolume object"""

    config_map_name: str
    items: dict[str, str]
    name: str

    def asdict(self):
        """Custom asdict because of needing to put location as parent dict key for inner dict"""
        return {
            "configMap": {
                "items": [{"key": key, "path": value} for key, value in self.items.items()],
                "name": self.config_map_name,
            },
            "name": self.name,
        }


@dataclass
class SecretVolume:
    """Deployment SecretVolume object"""

    secret_name: str
    name: str
    readOnly: bool = True

    def asdict(self):
        """Custom asdict because of needing to put location as parent dict key for inner dict"""
        return {"secret": {"readOnly": self.readOnly, "secretName": self.secret_name}, "name": self.name}


Volume = SecretVolume | ConfigMapVolume


class Deployment(OpenShiftObject):
    """Kubernetes Deployment object"""

    @classmethod
    def create_instance(
        cls,
        openshift,
        name,
        container_name,
        image,
        ports: dict[str, int],
        selector: Selector,
        labels: dict[str, str],
        command_args: list[str] = None,
        volumes: list[Volume] = None,
        volume_mounts: list[VolumeMount] = None,
        readiness_probe: dict[str, Any] = None,
    ):
        """
        Creates new instance of Deployment
        Supports only single container Deployments everything else should be edited directly
        """
        model: dict = {
            "kind": "Deployment",
            "apiVersion": "apps/v1",
            "metadata": {
                "name": name,
                "labels": labels,
            },
            "spec": {
                "selector": asdict(selector),
                "template": {
                    "metadata": {"labels": {"deployment": name, **labels}},
                    "spec": {
                        "containers": [
                            {
                                "image": image,
                                "name": container_name,
                                "imagePullPolicy": "IfNotPresent",
                                "ports": [{"name": name, "containerPort": port} for name, port in ports.items()],
                            }
                        ]
                    },
                },
            },
        }
        template = model["spec"]["template"]["spec"]

        if volumes:
            template["volumes"] = [asdict(volume) for volume in volumes]

        container = template["containers"][0]

        if command_args:
            container["args"] = command_args

        if volume_mounts:
            container["volumeMounts"] = [asdict(mount) for mount in volume_mounts]

        if readiness_probe:
            container["readinessProbe"] = readiness_probe

        return cls(model, context=openshift.context)

    def wait_for_ready(self, timeout=90):
        """Waits until Deployment is marked as ready"""
        with oc.timeout(timeout):
            success, _, _ = self.self_selector().until_all(success_func=lambda obj: "readyReplicas" in obj.model.status)
            assert success, f"Deployment {self.name()} did not get ready in time"

    @property
    def template(self):
        """Returns spec.template.spec part of Deployment"""
        return self.model.spec.template.spec

    @property
    def container(self):
        """Returns spec.template.spec.container[0] part of Deployment"""
        return self.template.containers[0]

    @modify
    def add_mount(self, mount: VolumeMount):
        """Adds volume mount"""
        mounts = self.container.setdefault("volumeMounts", [])
        mounts.append(asdict(mount))

    @modify
    def add_volume(self, volume: Volume):
        """Adds volume"""
        mounts = self.template.setdefault("volumes", [])
        mounts.append(asdict(volume))
