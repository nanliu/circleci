import argparse
import datetime
import logging
import time

from kubernetes import client, config


class KubeStatus:
    def __init__(self):
        config.load_kube_config()
        self.api = client.ApiClient()
        self.batchapi = client.BatchV1Api(self.api)
        self.betaapi = client.ExtensionsV1beta1Api(self.api)

    def wait_for_all_jobs(self, namespace, wait_sec=60):
        jobs = self.batchapi.list_namespaced_job(namespace)
        for j in jobs.items:
            self.wait_for_job(namespace, j.metadata.name, wait_sec)

    def wait_for_job(self, namespace, name, wait_sec=60):
        timeout = datetime.datetime.now() + datetime.timedelta(seconds=wait_sec)

        while datetime.datetime.now() < timeout:
            try:
                deploy = self.batchapi.read_namespaced_job(name, namespace)
                if deploy.status.succeeded >= 1:
                    print("{} job in {} namespace is complete".format(name, namespace))
                    return deploy
                print("waiting for {} job in {} namespace".format(name, namespace))
                time.sleep(10)
            except client.rest.ApiException, e:
                logging.error("Unable to obtain {} job in {} namespace".format(name, namespace))
                logging.error(e)
                time.sleep(10)

        logging.error("{} job in namespace {} failed to complete in {}s".format(name, namespace, wait_sec))
        raise TimeoutError("Error: {} job in {} namespace {}s timeout ".format(name, namespace, wait_sec))


    def wait_for_all_deployments(self, namespace, wait_sec=60):
        deployments = self.betaapi.list_namespaced_deployment(namespace)
        for d in deployments.items:
            self.wait_for_deployment(namespace, d.metadata.name, wait_sec)

    def wait_for_deployment(self, namespace, name, wait_sec=60):
        timeout = datetime.datetime.now() + datetime.timedelta(seconds=wait_sec)

        while datetime.datetime.now() < timeout:
            try:
                deploy = self.betaapi.read_namespaced_deployment(name, namespace)
                if deploy.status.ready_replicas >= 1:
                    print("{} deployment in {} namespace is ready".format(name, namespace))
                    return deploy
                print("waiting for {} deployment in {} namespace".format(name, namespace))
                time.sleep(10)
            except client.rest.ApiException, e:
                logging.error("Unable to obtain {} deployment in {} namespace".format(name, namespace))
                logging.error(e)
                time.sleep(10)

        logging.error("{} deployment in namespace {} failed to deploy in {}s".format(name, namespace, wait_sec))
        raise TimeoutError("Error: {} deployment in {} namespace {}s timeout ".format(name, namespace, wait_sec))


def arg_parser():
    p = argparse.ArgumentParser()
    p.add_argument('-t', '--timeout', type=int, help='timeout (seconds)')
    p.add_argument('namespace', type=str, help='kubernetes namespace')
    return p.parse_args()


def cli():
    args = arg_parser()
    status = KubeStatus()
    status.wait_for_all_jobs(args.namespace)
    status.wait_for_all_deployments(args.namespace)
