import os
import subprocess
import unittest

from circleci.base import CircleCIBase


class TestCircleIntegration(unittest.TestCase):

    def test_circle_integration(self):
        circle = CircleCIBase()
        output = subprocess.check_output([
            'integration', 'nanliu/circleci', 'test_branch',
            ], env=dict(
                os.environ,
                CIRCLE_PULL_REQUEST='https://github.com/nanliu/circleci/pull/32',
                CIRCLE_PROJECT_USERNAME='nanliu',
                CIRCLE_PROJECT_REPONAME='circleci',
                CIRCLE_SHA1='a96e5a6dfba3a96d27bfcbef66717ea51ffeacb8',
            )
        )
        build_num = None
        for line in output.split("\n"):
            if line.startswith('Build Number'):
                build_num = line.split(':')[1]
        build_status = circle.get_single_build_status(
            'nanliu/circleci',
            build_num
        )
        build_params = build_status['build_parameters']
        assert build_params['PR_URL'], 'https://github.com/nanliu/circleci/pull/32'
        assert build_params['STATUS_URL'], 'https://api.github.com/repos/nanliu/circleci/statuses/a96e5a6dfba3a96d27bfcbef66717ea51ffeacb8'
        assert build_params['CUSTOM_VALUES'], '{ "circleci": {"repo": "circleci","tag": "a96e5a6dfba3a96d27bfcbef66717ea51ffeacb8"} }'
