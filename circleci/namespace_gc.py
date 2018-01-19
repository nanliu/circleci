import argparse
import json
import logging
import subprocess
import sys
import re
from circleci.base import CircleCIBase


class NamespaceGC():
    def __init__(self, noop, prefix='circleci'):
        self.circleci = CircleCIBase()
        self.noop = noop
        self.prefix=prefix

    def get_active_namespaces(self):
        active_namespaces = []
        ns_out = subprocess.check_output(["kubectl", "get", "ns"])
        ignore = ['default', 'kube-system', 'kube-public']
        for line in ns_out.rstrip().split("\n")[1:]:
            spl_line = line.split()
            if spl_line[1] == 'Active':
                name = spl_line[0]
                if name not in ignore:
                    match = re.search('^{}-(\d+)$'.format(self.prefix), name)
                    if match:
                        active_namespaces.append(match.group(1))
                    else:
                        logging.debug(
                            "Found unexpected namespace: {}".format(name)
                        )
        return active_namespaces

    def get_active_vms(self):
        cmd = [
            'gcloud',
            'compute',
            'instances',
            'list',
            '--filter',
            "name:(condor-{}-*)".format(self.prefix),
            "--format=json(name)"
        ]
        logging.debug(" ".join(cmd))
        vm_out = subprocess.check_output(cmd)
        vm_names = [
            str(
                x['name'].strip('condor-{}-'.format(self.prefix))
            ) for x in json.loads(vm_out)
        ]
        return vm_names

    def get_active_helm_releases(self):
        cmd = [
            'helm',
            'list',
            '-q',
        ]
        logging.debug(" ".join(cmd))
        vm_out = subprocess.check_output(cmd)
        build_nums = set()
        for release in vm_out.split():
            match = re.search('^\S*-{}-(\d+)$'.format(self.prefix), release)
            if match:
                build_nums.add(match.group(1))
            else:
                logging.debug("Unexpected release found: {}".format(release))
        # this has lots of dups, but it gets converted to a set later
        return list(build_nums)

    # get up to the last 30 builds that are active, you can
    # also filter the results to return a single key
    def get_active_builds(self, repo, filter=None):
        builds = self.circleci.get_build_status(repo)
        if isinstance(builds, list):
            if filter is not None:
                builds = [str(x[filter]) for x in builds]
            return builds
        else:
            logging.error("Unexpected type for data: {}".format(builds))
            exit(1)

    def _run_gcloud_vm_delete_cmd(self, build_nums=[]):
        self._run_delete_cmd(
            "condor-{}-".format(self.prefix),
            [
                "gcloud",
                "compute",
                "instances",
                "delete",
                "--zone=us-west1-b",
                "--quiet"
            ],
            build_nums,
        )

    def _run_gc_ns_delete_cmd(self, build_nums=[]):
        self._run_delete_cmd(
            "{}-".format(self.prefix),
            ["kubectl", "delete", "ns"],
            build_nums,
        )

    def _run_helm_delete_cmd(self, build_nums=[]):
        cmd = [
            'helm',
            'list',
            '-q',
        ]
        logging.debug(" ".join(cmd))
        helm_list_out = subprocess.check_output(cmd)
        releases_to_delete = []
        for release in helm_list_out.split():
            match = re.search('^\S*-{}-(\d+)$'.format(self.prefix), release)
            if match:
                if match.group(1) in build_nums:
                    releases_to_delete.append(release)
        self._run_delete_cmd(
            '',
            ["helm", "delete", "--purge"],
            releases_to_delete,
        )

    def _run_delete_cmd(self, prefix, cmd, build_nums=[]):
        munged_objs = ['{}{}'.format(prefix, i) for i in build_nums]
        if len(munged_objs) > 0:
            cmd.extend(munged_objs)
            logging.info("Running delete command: {}".format(cmd))
            if self.noop is False:
                delete_out = subprocess.check_output(cmd)
                logging.info(delete_out)

    def gc_builds(self, repo):
        # you have to get ns first b/c otherwise, you could delete builds that
        # are created before ns is called
        active_ns = self.get_active_namespaces()
        active_builds = self.get_active_builds(repo, filter='build_num')
        active_vms = self.get_active_vms()
        active_helm_releases = self.get_active_helm_releases()
        ns_to_gc = list(set(active_ns) - set(active_builds))
        vms_to_gc = list(set(active_vms) - set(active_builds))
        releases_to_gc = list(set(active_helm_releases) - set(active_builds))
        logging.debug("Active builds: {}".format(active_builds))
        logging.debug("Active helm: {}".format(set(active_helm_releases)))
        logging.debug("Active VMs: {}".format(active_vms))
        logging.debug("Active namespaces: {}".format(active_ns))
        logging.debug("NS to GC:{}".format(ns_to_gc))
        logging.debug("VMs to GC:{}".format(vms_to_gc))
        logging.debug("Releases to GC:{}".format(releases_to_gc))

        self._run_helm_delete_cmd(releases_to_gc)
        self._run_gc_ns_delete_cmd(ns_to_gc)
        self._run_gcloud_vm_delete_cmd(vms_to_gc)


def arg_parser():
    p = argparse.ArgumentParser()
    p.add_argument('--noop', action='store_true', default=False)
    p.add_argument('--verbose', action='store_true', default=False)
    p.add_argument('--prefix', type=str, default='circleci')
    p.add_argument('repo', type=str, help='github org/repo')
    return p.parse_args()


def init_logger(level=logging.INFO):
    root = logging.getLogger()
    root.setLevel(level)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    root.addHandler(ch)

def cli():
    args = arg_parser()
    if args.verbose:
        init_logger(level=logging.DEBUG)
    else:
        init_logger(level=logging.INFO)
    gc = NamespaceGC(args.noop, prefix=args.prefix)
    gc.gc_builds(args.repo)
