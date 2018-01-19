import os
import unittest
import json
from mock import patch

from circleci.github import Github, GithubPullRequest, GithubStatus


class TestGithub(unittest.TestCase):
    def test_init(self):
        with self.assertRaises(Exception) as context:
            Github()
            self.assertEqual(context, '')

        os.environ['GH_OAUTH_TOKEN'] = 'GH_TOKEN'

        gh = Github()
        self.assertEqual(gh.oauth, 'GH_TOKEN')


class TestGithubPullRequest(unittest.TestCase):
    class PullRequestGetMock():
        def __init__(self):
            self.status_code = 200
            self.text = '{}'

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

    @patch.object(GithubPullRequest, 'parse_pr')
    def test_parse_url(self, url):
        test_urls = [
            "https://github.com/octocat/Hello-World/pull/1347",
            "http://github.com/octocat/Hello/pull/124/",
            "https://api.github.com/repos/octocat/Hello-World/pulls/failure"
        ]

        pr = GithubPullRequest(test_urls[0])
        self.assertEqual(pr.owner, 'octocat')
        self.assertEqual(pr.repo, 'Hello-World')
        self.assertEqual(pr.number, '1347')
        self.assertEqual(pr.helm_chart_name, 'Hello_World')
        self.assertEqual(pr.pr_api_url, 'https://api.github.com/repos/octocat/Hello-World/pulls/1347')

        pr = GithubPullRequest(test_urls[1])
        self.assertEqual(pr.owner, 'octocat')
        self.assertEqual(pr.repo, 'Hello')
        self.assertEqual(pr.number, '124')
        self.assertEqual(pr.pr_api_url, 'https://api.github.com/repos/octocat/Hello/pulls/124')

        with self.assertRaises(ValueError) as context:
            GithubPullRequest(test_urls[2])

        self.assertTrue('ERROR: Invalid url: {}'.format(test_urls[2]) in context.exception)

    @patch('requests.get', return_value=PullRequestGetMock())
    def test_parse_pr(self, url):
        pr = GithubPullRequest('https://github.com/octocat/Hello-world/pull/124')
        self.assertEqual(
            pr.description,
            "```\r\npull_requests:\r\n  - https://github.com/octocat/Hello-world/pull/123\r\n```")
        self.assertEqual(pr.sha, '6dcb09b5b57875f334f61aebed695e2e4193db5e')
        self.assertEqual(pr.branch, 'branch-name')
        self.assertEqual(pr.status_url, 'https://api.github.com/repos/octocat/Hello-world/statuses/6dcb09b5b57875f334f61aebed695e2e4193db5e')

    @patch('requests.get', return_value=PullRequestGetMock())
    def test_pull_requests(self, url):
        pr = GithubPullRequest('https://github.com/octocat/Hello-world/pull/124')
        self.assertEqual(
            pr.pull_requests(),
            set(['https://github.com/octocat/Hello-world/pull/123','https://github.com/octocat/Hello-world/pull/124'])
        )

        pr = GithubPullRequest('https://github.com/octocat/Hello-world/pull/123')
        self.assertEqual(
            pr.pull_requests(),
            set(['https://github.com/octocat/Hello-world/pull/123'])
        )


class TestGithubStatus(unittest.TestCase):
    class RequestMock():
        def __init__(self):
            self.status_code = 200
            self.text = '{}'

        def json(self):
            return {}

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
            pr.headers,
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
