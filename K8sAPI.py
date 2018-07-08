#!/usr/bin/python3
# Author: Zhuangwei Kang
# -*- coding: utf-8 -*-

import os
from kubernetes import client, config


class K8sAPI:
    # Create a deployment on a specific node
    def create_deployment(self, node_name, deployment_name, pod_label, image_name, container_name, cpu_requests=None,
                          cpu_limits=None, container_port=7000, env=None, volume=None):
        # Load config from default location
        config.load_kube_config()
        extension = client.ExtensionsV1beta1Api()

        if cpu_limits is None and cpu_requests is None:
            container_resource = None
        else:
            container_resource = client.V1ResourceRequirements(
                limits={'cpu': cpu_limits},
                requests={'cpu': cpu_requests}
            )

        container = client.V1Container(
            name=container_name,
            image=image_name,
            image_pull_policy='IfNotPresent',
            ports=[client.V1ContainerPort(container_port=container_port)],
            resources=container_resource,
            tty=True,
            stdin=True,
            env=env,
            volume_mounts=volume
        )

        # Create and configurate a spec section
        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels={"app": pod_label}),
            spec=client.V1PodSpec(node_name=node_name, containers=[container]))

        selector = client.V1LabelSelector(match_labels={'app': pod_label})

        # Create the specification of deployment
        spec = client.ExtensionsV1beta1DeploymentSpec(
            replicas=1,
            selector=selector,
            template=template
        )

        # Instantiate the deployment object
        deployment = client.ExtensionsV1beta1Deployment(
            api_version="extensions/v1beta1",
            kind="Deployment",
            metadata=client.V1ObjectMeta(name=deployment_name),
            spec=spec)

        # create deployment
        extension.create_namespaced_deployment(namespace="default", body=deployment)

    # Create a service using NodePort manner
    def create_svc(self, svc_name, selector_label, _port=7000, _node_port=30000):
        config.load_kube_config()
        api_instance = client.CoreV1Api()
        service = client.V1Service()

        service.api_version = "v1"
        service.kind = "Service"

        # define meta data
        service.metadata = client.V1ObjectMeta(name=svc_name)

        # define spec part
        spec = client.V1ServiceSpec()
        spec.selector = {"app": selector_label}
        spec.type = "NodePort"
        spec.ports = [client.V1ServicePort(
            protocol="TCP",
            port=_port,
            node_port=_node_port)]

        service.spec = spec

        # create service
        api_instance.create_namespaced_service(namespace="default", body=service)

    def delete_deployment(self, deployment_name):
        drop_deployment = 'kubectl delete deployment ' + deployment_name
        os.system(drop_deployment)
        print('Delete deployment %s' % deployment_name)

    def delete_svc(self, svc_name):
        drop_svc = 'kubectl delete svc ' + svc_name
        os.system(drop_svc)
        print('Delete service: ' + svc_name)

    def update_cpu_num(self, deployment_name, cpu_requests, cpu_limits=None):
        if cpu_limits is None:
            command = 'kubectl set resources deployment %s --requests=\'cpu=%s\'' % (deployment_name, cpu_requests)
        else:
            command = 'kubectl set resources deployment %s --requests=\'cpu=%s\' --limits=\'cpu=%s\'' % (
                deployment_name, cpu_requests, cpu_limits)
        print(os.popen(command=command).read())