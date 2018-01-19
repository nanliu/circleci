import argparse
import json
import os
import re
import requests
import yaml


class Github():
    def __init__(self):
        self.github_api = 'https://api.github.com'
        self.oauth = os.environ.get('GH_OAUTH_TOKEN')
        if self.oauth is None:
            raise Exception('Missing environment variable GH_OAUTH_TOKEN')
        self.headers = {
            'Authorization': 'token {}'.format(self.oauth),
            'Content-Type': 'application/json'
        }

    def request(self, verb, url, data=None):
        if verb == 'get':
            resp = requests.get(url, headers=self.headers)
        elif verb == 'post':
            resp = requests.post(url, headers=self.headers, data=data)

        if 200 <= resp.status_code < 300:
            return resp.json()
        else:
            print resp.text

    def get(self, url):
        return self.request('get', url)

    def post(self, url, data):
        return self.request('post', url, data=data)

class GithubPullRequest(Github):
    def __init__(self, url):
        Github.__init__(self)
        self.url = url
        self.parse_url()
        self.parse_pr()

    def parse_url(self):
        result = re.search('^https?:\/\/github.com\/(.*)\/(.*)\/pull\/(\d+)\/?$', self.url)
        if result is None:
            raise ValueError('ERROR: Invalid url: ' + self.url)
        else:
            self.owner = result.group(1)
            self.repo = result.group(2)
            self.number = result.group(3)
            self.helm_chart_name = self.repo.replace('-', '_')

        # https://developer.github.com/v3/pulls/
        # GET /repos/:owner/:repo/pulls/:number
        self.pr_api_url = '{}/repos/{}/{}/pulls/{}'.format(
            self.github_api,
            self.owner,
            self.repo,
            self.number
        )

    def parse_pr(self):
        pr = self.get(self.pr_api_url)

        self.description = pr['body']
        self.sha = pr['head']['sha']
        self.repo_full_name = pr['head']['repo']['full_name']
        self.branch = pr['head']['ref']
        self.active = pr['state'] == 'open'

        self.status_url = '{}/repos/{}/{}/statuses/{}'.format(
            self.github_api,
            self.owner,
            self.repo,
            self.sha,
        )

    def pull_requests(self):
        prs = self.get_description_section('pull_requests', '```')
        if prs:
            return set([self.url] + prs)
        else:
            return set([self.url])

    def custom_value(self):
        return {
            self.helm_chart_name: {
                'repo': self.repo,
                'tag': self.sha
            }
        }

    def get_description_section(self, yaml_section, delimiter):
        """
        Parses pull request description and generates custom values on
        circleci. Expects following format in the pull request description.

        ```
        pull_requests:
          - link
          - link
        ```

        Args:
        yaml_section (string): string used to search for yaml block
        pr_description (string): Pull request description
        delimeter (string): determines how to split pull request description

        Returns:
        (string): yaml from pull request
        """
        if not self.description:
            return None
        description_array = self.description.split(delimiter)

        yaml_indentifier = '{}:'.format(yaml_section)
        for string in description_array:
            if yaml_indentifier not in string:
                continue
            pr_description = yaml.load(string.strip())
            return pr_description[yaml_section]
        return None


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
        return self.post(url, data)

    def get_combined_status(self, url=None, owner=None, repo=None, ref=None):
        # https://developer.github.com/v3/repos/statuses/#get-the-combined-status-for-a-specific-ref
        # GET /repos/:owner/:repo/commits/:ref/status
        if url is None:
            url = self.format_url('{}/repos/{}/{}/commits/{}/status',
                                  owner=owner, repo=repo, sha=ref)

        return self.get(url)


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


def status_cli():
    args = arg_parser()

    context = args.context
    if os.environ.get('STATUS_CONTEXT'):
        context = os.environ.get('STATUS_CONTEXT')

    for url in args.url.split(','):
        print(GithubStatus().create_status(
            args.state, args.target, args.description, context, url=url))
