import os
import subprocess
import unittest
from mock import MagicMock, patch
from circleci.namespace_gc import NamespaceGC


def subprocess_side_effect(arg):
    gcloud_list_cmd = [
        'gcloud',
        'compute',
        'instances',
        'list',
        '--filter',
        "name:(condor-circleci-*)",
        "--format=json(name)"
    ]
    if arg == ["kubectl", "get", "ns"]:
        return TestCircleCINamespaceGC.get_ns_output
    elif arg == ['helm', 'list', '-q']:
        return TestCircleCINamespaceGC.get_helm_output
    elif arg == gcloud_list_cmd:
        return TestCircleCINamespaceGC.get_vm_output
    else:
        return "[]"


class TestCircleCINamespaceGC(unittest.TestCase):
    get_ns_output = """NAME            STATUS    AGE
123             Active    19h
circleci-4701   Active    27m
circleci-4702   Active    27m
default         Active    19d
kube-public     Active    19d
kube-system     Active    19d
"""
    get_vm_output = """[
  {
    "name": "condor-circleci-4701"
  },
  {
    "name": "condor-circleci-4702"
  }
]"""
    get_helm_output = """cloud-testing-circleci-4706
cloud-testing-circleci-4707
condor-service-circleci-4702
condor-service-circleci-4705
cron-kube-system
external-dns-kube-system
h-celery-circleci-4701
h-celery-circleci-4705
h-celery-circleci-4710
"""

    def setUp(self):
        os.environ['CIRCLE_TOKEN'] = 'foo'

    @patch('subprocess.check_output', return_value=get_ns_output)
    def test_get_active_namespaces(self, patch1):
        gc = NamespaceGC(False)
        self.assertEqual(
            gc.get_active_namespaces(),
            ['4701', '4702']
        )

    class CircleCIGetMock():
        def __init__(self):
            self.status_code=200
        def json(self):
            return [{'build_num': '123'},
                    {'build_num': '4701'}]

    @patch('requests.get', return_value=CircleCIGetMock())
    def test_get_active_builds(self, patch1):
        gc = NamespaceGC(False)
        result = gc.get_active_builds('org/repo', filter='build_num')
        self.assertEqual(
            result,
            ['123', '4701']
        )

    @patch('subprocess.check_output', return_value=get_vm_output)
    def test_get_active_vms(self, patch1):
        gc = NamespaceGC(False)
        self.assertEqual(
            gc.get_active_vms(),
            ['4701', '4702']
        )

    @patch('subprocess.check_output', return_value=get_helm_output)
    def test_get_active_helm_releases(self, patch1):
        gc = NamespaceGC(False)
        nums = gc.get_active_helm_releases()
        nums.sort()
        self.assertEqual(
            nums,
            ['4701', '4702', '4705', '4706', '4707', '4710']
        )

    @patch('requests.get', return_value=CircleCIGetMock())
    def test_gc_builds(self, get_patch):
        m1 = MagicMock(side_effect=subprocess_side_effect)
        subprocess.check_output = m1
        gc = NamespaceGC(False)
        gc.gc_builds('org/repo')
        m1.assert_any_call(["kubectl", "delete", "ns", "circleci-4702"])
        m1.assert_any_call(
            [
                'helm',
                'delete',
                '--purge',
                'cloud-testing-circleci-4706',
                'cloud-testing-circleci-4707',
                'condor-service-circleci-4702',
                'condor-service-circleci-4705',
                'h-celery-circleci-4705',
                'h-celery-circleci-4710'
            ]
        )
        m1.assert_any_call(["kubectl", "delete", "ns", "circleci-4702"])
        m1.assert_called_with(['gcloud', 'compute', 'instances', 'delete', '--zone=us-west1-b', '--quiet', 'condor-circleci-4702'])
