import os
import subprocess
import time
import unittest


class TestCircleCINamespaceGCIntegration(unittest.TestCase):
    def setUp(self):
        subprocess.call(['kubectl','delete', 'ns', 'test-0'])
        self.repo=os.environ.get('TEST_REPO')

    def test_delete_ns(self):
        if self.repo is None:
            self.fail("Must define TEST_REPO env var")
        result = 1
        attempts = 0
        while(result != 0):
            print "retrying"
            result = subprocess.call(['kubectl', 'create', 'ns', 'test-0'])
            if(result == 0):
                break;
            if(attempts > 5):
                self.fail("Could not create test namespace")
            time.sleep(5)
            attempts = attempts = attempts + 1
        # running in noop b/c terrified this tests will break something
        output = subprocess.check_output(['circleci_namespace_gc', self.repo, '--prefix=test'])
        print output
        assert 'Running delete command: [\'kubectl\', \'delete\', \'ns\', \'test-0\']' in output
        get_ns_out = subprocess.check_output(['kubectl', 'get', 'ns', 'test-0'], stderr=subprocess.STDOUT)
        if not ('test-0    Terminating' in get_ns_out or 'namespaces "test-0" not found' in get_ns_out):
            self.fail("namespace not deleted: {}".format(get_ns_out))
