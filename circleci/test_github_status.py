import os
import unittest
import json
from mock import patch

from circleci.github_status import GithubStatus


class TestGithubStatus(unittest.TestCase):
    class RequestMock():
        def __init__(self):
            self.text = '{}'

    def setUp(self):
        os.environ['GH_OAUTH_TOKEN'] = 'GH_TOKEN'
        os.environ['CIRCLE_PROJECT_USERNAME'] = 'octocat'
        os.environ['CIRCLE_PROJECT_REPONAME'] = 'Hello-World'
        os.environ['CIRCLE_SHA1'] = '6dcb09b5b57875f334f61aebed695e2e4193db5e'

    def test_oauth(self):
        del os.environ['GH_OAUTH_TOKEN']
        self.assertRaises(
            Exception,
            GithubStatus
        )

    def test_headers(self):
        pr = GithubStatus()
        self.assertEqual(
            pr.headers(),
            {
                'Authorization': 'token GH_TOKEN',
                'Content-Type': 'application/json'
            }
        )

    def test_format_url(self):
        pr = GithubStatus()
        self.assertEqual(
            pr.format_url('{}/repos/{}/{}/statuses/{}'),
            'https://api.github.com/repos/octocat/Hello-World/statuses/6dcb09b5b57875f334f61aebed695e2e4193db5e'
        )
        self.assertEqual(
            pr.format_url('{}/repos/{}/{}/statuses/{}', owner='nanliu', repo='circleci'),
            'https://api.github.com/repos/nanliu/circleci/statuses/6dcb09b5b57875f334f61aebed695e2e4193db5e'
        )
        self.assertEqual(
            pr.format_url('{}/repos/{}/{}/commits/{}/status'),
            'https://api.github.com/repos/octocat/Hello-World/commits/6dcb09b5b57875f334f61aebed695e2e4193db5e/status'
        )
        self.assertEqual(
            pr.format_url('{}/repos/{}/{}/statuses/{}', owner='nanliu', repo='circleci'),
            'https://api.github.com/repos/nanliu/circleci/statuses/6dcb09b5b57875f334f61aebed695e2e4193db5e'
        )

    @patch('requests.post', autospec=True, return_value=RequestMock())
    def test_create_status(self, req):
        pr = GithubStatus()
        pr.create_status(
            'success',
            'https://ci.example.com/1000/output',
            'Build has completed successfully',
            'continuous-integration/jenkins',
        )
        req.assert_called_once_with(
            'https://api.github.com/repos/octocat/Hello-World/statuses/6dcb09b5b57875f334f61aebed695e2e4193db5e',
            headers={
                'Content-Type': 'application/json',
                'Authorization': 'token GH_TOKEN'
            },
            data=json.dumps({
                'state': 'success',
                'target_url': 'https://ci.example.com/1000/output',
                'description': 'Build has completed successfully',
                'context': 'continuous-integration/jenkins'
            }),
        )

    @patch('requests.post', autospec=True, return_value=RequestMock())
    def test_create_status_with_url(self, req):
        pr = GithubStatus()
        pr.create_status(
            'success',
            'https://ci.example.com/1000/output',
            'Build has completed successfully',
            'continuous-integration/jenkins',
            url='https://api.github.com/repos/nanliu/circleci/statuses/6dcb09b5b57875f334f61aebed695e2e4193db5e'
        )
        req.assert_called_once_with(
            'https://api.github.com/repos/nanliu/circleci/statuses/6dcb09b5b57875f334f61aebed695e2e4193db5e',
            headers={
                'Content-Type': 'application/json',
                'Authorization': 'token GH_TOKEN'
            },
            data=json.dumps({
                'state': 'success',
                'target_url': 'https://ci.example.com/1000/output',
                'description': 'Build has completed successfully',
                'context': 'continuous-integration/jenkins'
            }),
        )

    @patch('requests.get', autospec=True, return_value=RequestMock())
    def test_get_combined_status(self, req):
        pr = GithubStatus()
        pr.get_combined_status()
        req.assert_called_once_with(
            'https://api.github.com/repos/octocat/Hello-World/commits/6dcb09b5b57875f334f61aebed695e2e4193db5e/status',
            headers={
                'Content-Type': 'application/json',
                'Authorization': 'token GH_TOKEN'
            },
        )

    @patch('requests.get', autospec=True, return_value=RequestMock())
    def test_get_combined_status_with_url(self, req):
        pr = GithubStatus()
        pr.get_combined_status(url='https://api.github.com/repos/nanliu/circleci/commits/6dcb09b5b57875f334f61aebed695e2e4193db5e/status')
        req.assert_called_once_with(
            'https://api.github.com/repos/nanliu/circleci/commits/6dcb09b5b57875f334f61aebed695e2e4193db5e/status',
            headers={
                'Content-Type': 'application/json',
                'Authorization': 'token GH_TOKEN'
            },
        )
