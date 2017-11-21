import argparse
import subprocess
import re
from circleci_base import CircleCIBase


class NamespaceGC():
    def __init__(self, noop):
        self.circleci = CircleCIBase()
        self.noop = noop

    def get_active_builds_by_namespace(self):
        active_namespaces = []
        ns_out = subprocess.check_output(["kubectl", "get", "ns"])
        # print ns_out
        ignore = ['default', 'kube-system', 'kube-public']
        for line in ns_out.rstrip().split("\n")[1:]:
            spl_line = line.split()
            if spl_line[1] == 'Active':
                name = spl_line[0]
                if name not in ignore:
                    match = re.search('^circleci-(\d+)$', name)
                    if match:
                        active_namespaces.append(match.group(1))
                    else:
                        print "Found unexpected namespace: {}".format(name)
        return active_namespaces

    # get up to the last 30 builds that are active, you can
    # also filter the results to return a single key
    def get_active_builds(self, repo, filter=None):
        builds = self.circleci.get_build_status(repo)
        if filter is not None:
            builds = [str(x[filter]) for x in builds]
        return builds

    def run_gc_ns_cmd(self, build_nums=None):
        namespaces = ['circleci-{}'.format(i) for i in build_nums]
        if len(build_nums) > 0:
            cmd = ["kubectl", "delete", "ns"]
            cmd.extend(namespaces)
            print "Running delete command: {}".format(cmd)
            if self.noop is False:
                ns_delete_out = subprocess.check_output(cmd)
                print ns_delete_out

    def gc_namespaces(self, repo):
        # you have to get ns first b/c otherwise, you could delete builds that
        # are created before ns is called
        circle_builds = self.get_active_builds_by_namespace()
        active_ns_builds = self.get_active_builds(repo, filter='build_num')
        # print circle_builds
        # print active_ns_builds
        builds_to_gc = list(set(circle_builds) - set(active_ns_builds))
        self.run_gc_ns_cmd(builds_to_gc)


def arg_parser():
    p = argparse.ArgumentParser()
    p.add_argument('--noop', action='store_true', default=False)
    p.add_argument('repo', type=str, help='github org/repo')
    return p.parse_args()


def cli():
    args = arg_parser()
    gc = NamespaceGC(args.noop)
    gc.gc_namespaces(args.repo)
