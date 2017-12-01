import os
import subprocess
import unittest
import json
from mock import MagicMock, patch

from circleci_namespace_gc import NamespaceGC
from circleci_trigger import CircleCI
import integration

class TestIntegration(unittest.TestCase):
    maxDiff = None
    def setUp(self):
        os.environ['CIRCLE_TOKEN'] = 'foo'
        os.environ['GH_OAUTH_TOKEN'] = 'bar'
        os.environ['CIRCLE_PULL_REQUEST'] = 'bass'

    class PullRequestGetMock():
        def json(self):
            pull_request_response_example = r'''{
	"body": "```\r\nintegration_branch: \"not_master\"\r\npull_requests:\r\n  - https://github.com/octocat/Hello-world/pull/123\r\n```",
	"head": {
		"sha": "6dcb09b5b57875f334f61aebed695e2e4193db5e",
		"repo": {
			"owner": {
				"login": "octocat"
			},
			"name": "Hello-World"
		}
	}
}'''
            return json.loads(pull_request_response_example)
    class BranchRequestGetMock():
        def json(self):
            branch_response_example = r'''{
  "name": "master",
  "commit": {
    "sha": "7fd1a60b01f91b314f59955a4e4d4e80d8edf11d",
    "url": "https://api.github.com/repos/octocat/Hello-World/commits/7fd1a60b01f91b314f59955a4e4d4e80d8edf11d"
  }
}'''
            return json.loads(branch_response_example)

    @patch('requests.get', return_value=PullRequestGetMock())
    def test_get_description_section(self, patch1):
        current_pull_request = integration.Pull_Request('https://github.com/octocat/Hello-world/pull/123')
        urls = current_pull_request.get_description_section('pull_requests', '```')
        integration_branch = current_pull_request.get_description_section('integration_branch', '```') 
        self.assertEqual(
            urls,
            ['https://github.com/octocat/Hello-world/pull/123']
        )
        self.assertEqual(integration_branch, 'not_master')

    def test_validate_url(self):
        test_urls = [
        "https://github.com/octocat/Hello-World/pull/1347",
        "http://github.com/octocat/Hello/pull/124/",
        "https://api.github.com/repos/octocat/Hello-World/pulls/failure"
        ]
        regex = '^https?:\/\/github.com\/.*\/pull\/\d+\/?$'
        integration.validate_url(test_urls[0], regex)
        integration.validate_url(test_urls[1], regex)
        with self.assertRaises(ValueError) as context:
           integration.validate_url(test_urls[2],'^https?:\/\/github.com\/.*\/pull\/\d+\/?$')

        self.assertTrue('ERROR: Invalid url: {}'.format(test_urls[2]) in context.exception)
  
    @patch('requests.get', return_value=BranchRequestGetMock())
    def test_validate_integration_branch(self, patch1):
        integration.validate_integration_branch('octocat/Hello-world','master')
    

    @patch('requests.get', return_value=PullRequestGetMock())
    def test_generate_build_parameters(self, patch1):
        pull_requests = ['https://github.com/octocat/Hello-world/pull/123','https://github.com/octocat/Hello/pull/124']
        circle = CircleCI('integration/repo', 'foo')
        integration.generate_build_parameters(circle, pull_requests,'https://api.github.com/repos/octocat/integration/statuses/sha')
        self.assertEqual(
            circle.build_param,
            {'PR_URL': ['https://github.com/octocat/Hello-world/pull/123', 'https://github.com/octocat/Hello/pull/124'],
             'CUSTOM_VALUES':
             '{ "Hello_World": {"repo": "Hello-World","tag": "6dcb09b5b57875f334f61aebed695e2e4193db5e"},"Hello_World": {"repo": "Hello-World","tag": "6dcb09b5b57875f334f61aebed695e2e4193db5e"} }',
             'STATUS_URL': 'https://api.github.com/repos/octocat/integration/statuses/sha,https://api.github.com/repos/octocat/Hello-World/statuses/6dcb09b5b57875f334f61aebed695e2e4193db5e,https://api.github.com/repos/octocat/Hello-World/statuses/6dcb09b5b57875f334f61aebed695e2e4193db5e'}
        )
        circle_master = CircleCI('integration/repo', 'master')
        integration.generate_build_parameters(circle_master, pull_requests,'https://api.github.com/repos/octocat/integration/statuses/sha')
        self.assertEqual(
            circle_master.build_param,
            {'PR_URL': ['https://github.com/octocat/Hello-world/pull/123', 'https://github.com/octocat/Hello/pull/124'],
             'CUSTOM_VALUES':
             '{ "Hello_World": {"repo": "Hello-World","tag": "6dcb09b5b57875f334f61aebed695e2e4193db5e"},"Hello_World": {"repo": "Hello-World","tag": "6dcb09b5b57875f334f61aebed695e2e4193db5e"} }',
             'STATUS_URL': 'https://api.github.com/repos/octocat/Hello-World/statuses/6dcb09b5b57875f334f61aebed695e2e4193db5e,https://api.github.com/repos/octocat/Hello-World/statuses/6dcb09b5b57875f334f61aebed695e2e4193db5e'}
        )
