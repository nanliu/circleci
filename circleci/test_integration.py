import os
import unittest
import json
from mock import MagicMock, patch

from circleci.github import GithubPullRequest, GithubStatus
import integration


class TestIntegration(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        os.environ['CIRCLE_TOKEN'] = 'CI_TOKEN'
        os.environ['GH_OAUTH_TOKEN'] = 'GH_TOKEN'
        os.environ['CIRCLE_PULL_REQUEST'] = 'https://github.com/nanliu/circleci/pull/32'

    class PullRequestGetMock():
        def __init__(self):
            self.status_code = 200

        def json(self):
            pull_request_response_example = r'''{
  "body": "```\r\npull_requests:\r\n  - https://github.com/octocat/Hello-world/pull/123\r\n```",
  "state": "open",
  "head": {
    "ref": "test_branch",
    "sha": "a96e5a6dfba3a96d27bfcbef66717ea51ffeacb8",
    "repo": {
      "name": "circleci",
      "full_name": "nanliu/circleci",
      "owner": {
        "login": "nanliu"
      }
    }
  }
}'''
            return json.loads(pull_request_response_example)

    @patch('requests.get', return_value=PullRequestGetMock())
    def test_get_description_section(self, patch1):
        current_pull_request = GithubPullRequest('https://github.com/nanliu/circleci/pull/32')
        urls = current_pull_request.get_description_section('pull_requests', '```')
        self.assertEqual(
            urls,
            ['https://github.com/octocat/Hello-world/pull/123']
        )

    @patch('requests.get', return_value=PullRequestGetMock())
    def test_init(self, req):
        pr = integration.Integration('nanliu/circleci')
        self.assertEqual(pr.repo, 'nanliu/circleci')
        self.assertEqual(pr.branch, 'master')
        self.assertEqual(pr.build_param,  {})
        self.assertEqual(pr.context,  'ci/circleci-integration')

    @patch('requests.get', return_value=PullRequestGetMock())
    def test_filter_active_pr(self, req):
        pr = integration.Integration('nanliu/circleci')
        self.assertEqual(
            pr.filter_active_pr(['https://github.com/nanliu/circleci/pull/32']),
            ['https://github.com/nanliu/circleci/pull/32']
        )
        self.assertEqual(
            pr.branch,
            'master'
        )

    @patch('requests.get', return_value=PullRequestGetMock())
    def test_filter_integration_branch(self, req):
        pr = integration.Integration('nanliu/circleci')
        self.assertEqual(
            pr.filter_integration_branch(['https://github.com/nanliu/circleci/pull/32']),
            []
        )
        self.assertEqual(
            pr.branch,
            'test_branch'
        )

    @patch('requests.get', return_value=PullRequestGetMock())
    def test_run(self, req):
        pr = integration.Integration('nanliu/circleci')
        pr.build = MagicMock()
        pr.update_status = MagicMock()
        pr.run()
        self.assertEqual(
            pr.build_param['PR_URL'],
            'https://github.com/nanliu/circleci/pull/32'
        )
        self.assertEqual(
            pr.build_param['CUSTOM_VALUES'],
            '{"circleci": {"repo": "circleci", "tag": "a96e5a6dfba3a96d27bfcbef66717ea51ffeacb8"}}'
        )
        self.assertEqual(
            pr.build_param['STATUS_CONTEXT'],
            'ci/circleci-integration'
        )
        self.assertEqual(
            pr.build_param['STATUS_URL'],
            'https://api.github.com/repos/nanliu/circleci/statuses/a96e5a6dfba3a96d27bfcbef66717ea51ffeacb8'
        )

        pr = integration.Integration(
            'nanliu/circleci',
            build_param={"CUSTOM_VALUES": '{"test": {"1": "2"} }' },
            context='ci/circleci-int'
        )
        pr.build = MagicMock()
        pr.update_status = MagicMock()
        pr.run()
        self.assertEqual(
            pr.build_param['PR_URL'],
            'https://github.com/nanliu/circleci/pull/32'
        )
        self.assertEqual(
            pr.build_param['CUSTOM_VALUES'],
            '{"test": {"1": "2"}, "circleci": {"repo": "circleci", "tag": "a96e5a6dfba3a96d27bfcbef66717ea51ffeacb8"}}'
        )
        self.assertEqual(
            pr.build_param['STATUS_CONTEXT'],
            'ci/circleci-int'
        )
        self.assertEqual(
            pr.build_param['STATUS_URL'],
            'https://api.github.com/repos/nanliu/circleci/statuses/a96e5a6dfba3a96d27bfcbef66717ea51ffeacb8'
        )

        pr = integration.Integration(
            'nanliu/circleci',
            build_param={"CUSTOM_VALUES": 'bad' }
        )
        pr.build = MagicMock()
        pr.update_status = MagicMock()
        with self.assertRaises(ValueError) as context:
            pr.run()
