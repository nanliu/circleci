import os
import unittest
import json
from mock import patch

from circleci.trigger import CircleCI
import integration


class TestPullRequest(unittest.TestCase):
    class PullRequestGetMock():
        def json(self):
            return json.loads(r'''{
  "body": "```\r\npull_requests:\r\n  - https://github.com/octocat/Hello-world/pull/123\r\n```",
  "state": "open",
  "head": {
    "sha": "6dcb09b5b57875f334f61aebed695e2e4193db5e",
    "ref": "branch-name",
    "repo": {
      "owner": {
        "login": "octocat"
      },
      "name": "Hello-World",
      "full_name": "octocat/Hello-World"
    }
  }
}''')

    def setUp(self):
        os.environ['GH_OAUTH_TOKEN'] = 'GH_TOKEN'
        os.environ['CIRCLE_PROJECT_USERNAME'] = 'octocat'
        os.environ['CIRCLE_PROJECT_REPONAME'] = 'Hello-World'
        os.environ['CIRCLE_SHA1'] = '6dcb09b5b57875f334f61aebed695e2e4193db5e'

    @patch.object(integration.PullRequest, 'parse_pr')
    def test_parse_url(self, url):
        test_urls = [
            "https://github.com/octocat/Hello-World/pull/1347",
            "http://github.com/octocat/Hello/pull/124/",
            "https://api.github.com/repos/octocat/Hello-World/pulls/failure"
        ]

        pr = integration.PullRequest(test_urls[0])
        self.assertEqual(pr.owner, 'octocat')
        self.assertEqual(pr.repo, 'Hello-World')
        self.assertEqual(pr.number, '1347')
        self.assertEqual(pr.helm_chart_name, 'Hello_World')

        pr = integration.PullRequest(test_urls[1])
        self.assertEqual(pr.owner, 'octocat')
        self.assertEqual(pr.repo, 'Hello')
        self.assertEqual(pr.number, '124')

        with self.assertRaises(ValueError) as context:
            integration.PullRequest(test_urls[2])

        self.assertTrue('ERROR: Invalid url: {}'.format(test_urls[2]) in context.exception)

    @patch('requests.get', return_value=PullRequestGetMock())
    def test_parse_pr(self, url):
        pr = integration.PullRequest('https://github.com/octocat/Hello-world/pull/124')
        self.assertEqual(
            pr.description,
            "```\r\npull_requests:\r\n  - https://github.com/octocat/Hello-world/pull/123\r\n```")
        self.assertEqual(pr.sha, '6dcb09b5b57875f334f61aebed695e2e4193db5e')
        self.assertEqual(pr.branch, 'branch-name')
        self.assertEqual(pr.status_url, 'https://api.github.com/repos/octocat/Hello-world/statuses/6dcb09b5b57875f334f61aebed695e2e4193db5e')

    @patch('requests.get', return_value=PullRequestGetMock())
    def test_pull_requests(self, url):
        pr = integration.PullRequest('https://github.com/octocat/Hello-world/pull/124')
        self.assertEqual(
            pr.pull_requests(),
            set(['https://github.com/octocat/Hello-world/pull/123','https://github.com/octocat/Hello-world/pull/124'])
        )

        pr = integration.PullRequest('https://github.com/octocat/Hello-world/pull/123')
        self.assertEqual(
            pr.pull_requests(),
            set(['https://github.com/octocat/Hello-world/pull/123'])
        )

class TestIntegration(unittest.TestCase):
    maxDiff = None

    def setUp(self):
        os.environ['CIRCLE_TOKEN'] = 'CI_TOKEN'
        os.environ['GH_OAUTH_TOKEN'] = 'GH_TOKEN'
        os.environ['CIRCLE_PULL_REQUEST'] = 'https://github.com/nanliu/circleci/pull/32'

    class PullRequestGetMock():
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
        current_pull_request = integration.PullRequest('https://github.com/nanliu/circleci/pull/32')
        urls = current_pull_request.get_description_section('pull_requests', '```')
        self.assertEqual(
            urls,
            ['https://github.com/octocat/Hello-world/pull/123']
        )

    @patch('requests.get', return_value=PullRequestGetMock())
    def test_init(self, req):
        pr = integration.Integration('nanliu/circleci')
        #self.assertEqual(
        #    pr.status_urls,
        #    'https://api.github.com/repos/octocat/Hello-world/statuses/a96e5a6dfba3a96d27bfcbef66717ea51ffeacb8,https://api.github.com/repos/nanliu/circleci/statuses/a96e5a6dfba3a96d27bfcbef66717ea51ffeacb8'
        #)

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
