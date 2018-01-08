import os
import subprocess
import unittest
import circleci.gh_status


class TestCircleCIGHStatus(unittest.TestCase):

    def change_status_and_assert_change(
            self,
            ref,
            state,
            desc='test_desc',
            target_url = 'http://target_url',
            ):
        url1 = 'https://api.github.com/repos/nanliu/circleci/statuses/{}'.format(ref)
        url2 = 'https://api.github.com/repos/nanliu/circleci/commits/{}/status'.format(ref)
        output = subprocess.check_output([
            'gh_status',
            '-u',
            url1,
            state,
            target_url,
            desc,
        ])
        data = circleci.gh_status.get(url2)
        found = False
        for s in  data['statuses']:
            if s['description'] == desc:
                print s
                found = True
                assert s['target_url'] == target_url
                assert s['state'] == state
        assert found, True

    def test_update_gh_status(self):
        ref = 'a96e5a6dfba3a96d27bfcbef66717ea51ffeacb8'
        self.change_status_and_assert_change(ref=ref, state='success')
        self.change_status_and_assert_change(ref=ref, state='failure')
