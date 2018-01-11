import argparse
import json
import os
import requests


class Github():
    def __init__(self):
        self.github_api = 'https://api.github.com'
        self.oauth = os.environ.get('GH_OAUTH_TOKEN')
        if self.oauth is None:
            raise Exception('Missing environment variable GH_OAUTH_TOKEN')

    def headers(self):
        return {
            'Authorization': 'token {}'.format(self.oauth),
            'Content-Type': 'application/json'
        }


class GithubStatus(Github):
    # https://developer.github.com/v3/repos/statuses
    def __init__(self):
        Github.__init__(self)

    def format_url(self, url, owner=None, repo=None, sha=None):
        if owner is None:
            owner = os.environ.get('CIRCLE_PROJECT_USERNAME')
        if repo is None:
            repo = os.environ.get('CIRCLE_PROJECT_REPONAME')
        if sha is None:
            sha = os.environ.get('CIRCLE_SHA1')

        return url.format(
            self.github_api, owner, repo, sha
        )

    def create_status(self, state, target_url, description, context,
                      url=None, owner=None, repo=None, sha=None):
        # https://developer.github.com/v3/repos/statuses/#create-a-status
        # POST /repos/:owner/:repo/statuses/:sha
        if url is None:
            url = self.format_url('{}/repos/{}/{}/statuses/{}',
                                  owner=owner, repo=repo, sha=sha)

        data = json.dumps({
            'state': state,
            'target_url': target_url,
            'description': description,
            'context': context
        })
        print('Updating status for commit {}:\n{}'.format(url, data))
        result = requests.post(url, data=data, headers=self.headers())
        return json.loads(result.text)

    def get_combined_status(self, url=None, owner=None, repo=None, ref=None):
        # https://developer.github.com/v3/repos/statuses/#get-the-combined-status-for-a-specific-ref
        # GET /repos/:owner/:repo/commits/:ref/status
        if url is None:
            url = self.format_url('{}/repos/{}/{}/commits/{}/status',
                                  owner=owner, repo=repo, sha=ref)

        result = requests.get(url, headers=self.headers())
        return json.loads(result.text)


def arg_parser():
    p = argparse.ArgumentParser()
    p.add_argument(
        '-u', '--url', default=os.environ.get('STATUS_URL'),
        help='A comma seperated list of github commit status urls'
    )
    p.add_argument(
        'state', type=str,
        help='The state of the status (error, failure, pending, success)'
    )
    p.add_argument(
        'target', type=str, help='The target URL to associate with this status'
    )
    p.add_argument(
        'description', type=str, help='A short description of the status'
    )
    p.add_argument(
        '-c', '--context', type=str, default='ci/circleci-integration',
        help='A string label to differentiate this status from other systems'
    )
    return p.parse_args()


def update(url, state, target, description, context='ci/circleci-integration'):
    print(GithubStatus().create_status(
        state, target, description, context, url=url))


def cli():
    args = arg_parser()

    for url in args.url.split(','):
        print(GithubStatus().create_status(
            args.state, args.target, args.description, context, url=url))
