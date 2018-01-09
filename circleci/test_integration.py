import os
import unittest
import json
from mock import patch

from circleci.trigger import CircleCI
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
	"body": "```\r\npull_requests:\r\n  - https://github.com/octocat/Hello-world/pull/123\r\n```",
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
}'''
            return json.loads(pull_request_response_example)

    @patch('requests.get', return_value=PullRequestGetMock())
    def test_get_description_section(self, patch1):
        current_pull_request = integration.Pull_Request('https://github.com/octocat/Hello-world/pull/123')
        urls = current_pull_request.get_description_section('pull_requests', '```')
        self.assertEqual(
            urls,
            ['https://github.com/octocat/Hello-world/pull/123']
        )

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


    @patch('requests.get', return_value=PullRequestGetMock())
    def test_generate_build_parameters(self, patch1):
        pull_requests = ['https://github.com/octocat/Hello-world/pull/123','https://github.com/octocat/Hello/pull/124']
        circle = CircleCI('integration/repo', 'foo')
        integration.generate_build_parameters(circle, pull_requests)
        self.assertEqual(
            circle.build_param,
            {'PR_URL': ['https://github.com/octocat/Hello-world/pull/123', 'https://github.com/octocat/Hello/pull/124'],
             'CUSTOM_VALUES':
             '{ "Hello_World": {"repo": "Hello-World","tag": "6dcb09b5b57875f334f61aebed695e2e4193db5e"},"Hello_World": {"repo": "Hello-World","tag": "6dcb09b5b57875f334f61aebed695e2e4193db5e"} }',
             'STATUS_CONTEXT': 'ci/circleci-integration',
             'STATUS_URL': 'https://api.github.com/repos/octocat/Hello-World/statuses/6dcb09b5b57875f334f61aebed695e2e4193db5e,https://api.github.com/repos/octocat/Hello-World/statuses/6dcb09b5b57875f334f61aebed695e2e4193db5e'}
        )
        #Ensure that we ignore status for integration repo
        circle_master = CircleCI('octocat/hello-world', 'master')
        integration.generate_build_parameters(circle_master, pull_requests)
        self.assertEqual(
            circle_master.build_param,
            {'PR_URL': ['https://github.com/octocat/Hello-world/pull/123', 'https://github.com/octocat/Hello/pull/124'],
             'CUSTOM_VALUES': '',
             'STATUS_CONTEXT': 'ci/circleci-integration',
             'STATUS_URL': ''}
        )
        self.assertEqual(circle_master.branch,'branch-name')
