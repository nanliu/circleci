import argparse
import os
import re
import requests
import json
import yaml

from circleci.base import CircleCIBase
from circleci.github_status import Github, GithubStatus


class PullRequest(Github):
    def __init__(self, url):
        Github.__init__(self)
        self.url = url
        self.parse_url(url)
        self.parse_pr()

    def parse_url(self, url):
        result = re.search('^https?:\/\/github.com\/(.*)\/(.*)\/pull\/(\d+)\/?$', url)
        if result is None:
            raise ValueError('ERROR: Invalid url: ' + url)
        else:
            self.owner = result.group(1)
            self.repo = result.group(2)
            self.helm_chart_name = self.repo.replace('-', '_')
            self.number = result.group(3)

    def parse_pr(self):
        # https://developer.github.com/v3/pulls/
        # GET /repos/:owner/:repo/pulls/:number
        url = '{}/repos/{}/{}/pulls/{}'.format(
            self.github_api,
            self.owner,
            self.repo,
            self.number
        )
        pr = requests.get(url, headers=self.headers()).json()

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
        return '"{}": {{"repo": "{}","tag": "{}"}}'.format(
            self.helm_chart_name,
            self.repo,
            self.sha
        )

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


class Integration():
    def __init__(self, repo, branch='master', build_param={}, context='ci/circleci-integration'):
        self.build_param = build_param
        self.repo = repo
        self.branch = branch
        self.context = context
        self.status_urls = []

    def filter_active_pr(self, pull_requests):
        result = []
        for pr in pull_requests:
            if PullRequest(pr).active:
                result = result + [pr]
            else:
                print("{} is not open and dropped from integration tests".format(pr))
        return result

    def filter_integration_branch(self, pull_requests):
        result = []
        for pr in pull_requests:
            p = PullRequest(pr)
            if p.repo_full_name.lower() == self.repo.lower():
                print("Switching integration to {} branch {}".format(pr, p.branch))
                self.branch = p.branch
            else:
                result = result + [pr]
        return result

    def run(self, context='ci/circleci-integration'):
        if os.environ.get('CIRCLE_PULL_REQUEST'):
            # NOTE: This is integration for a PR
            current_pr = PullRequest(os.environ.get('CIRCLE_PULL_REQUEST'))
            pull_requests = self.filter_active_pr(current_pr.pull_requests())
            pull_requests = self.filter_integration_branch(pull_requests)
            # NOTE: make sure current PR is in the set
            pull_requests = set(pull_requests + [os.environ.get('CIRCLE_PULL_REQUEST')])
            self.build_param['PR_URL'] = ','.join(pull_requests)

            self.status_urls = [ PullRequest(pr).status_url for pr in pull_requests ]
            self.build_param['STATUS_URL'] = ','.join(self.status_urls)
            self.build_param['STATUS_CONTEXT'] = self.context

            custom_values = [ PullRequest(pr).custom_value() for pr in pull_requests ]
            self.build_param['CUSTOM_VALUES'] = '{{ {} }}'.format(','.join(custom_values))

        self.build()
        self.update_status()

    def build(self):
        data = json.dumps({'build_parameters': self.build_param})
        result = CircleCIBase().trigger_build(self.repo, self.branch, data)
        self.build_num = result['build_num']
        self.build_url = result['build_url']
        print("Build Number:{}".format(self.build_num))

    def update_status(self):
        for url in self.status_urls:
            desc = 'The integration build {} started'.format(self.build_num)
            GithubStatus().create_status(
                'running', self.build_url, desc, self.context, url=url)


def arg_parser():
    p = argparse.ArgumentParser()
    p.add_argument('-K', '--KEY', action='append', nargs=1)
    p.add_argument('-V', '--VALUE', action='append', nargs=1)
    p.add_argument('-c', '--context', type=str, default='ci/circleci-integration',
                   help='A string label to differentiate this status from other systems')

    p.add_argument('repo', type=str, help='github org/repo')
    p.add_argument('branch', type=str, help='git branch to test')
    return p.parse_args()


def cli():
    args = arg_parser()
    params = {}
    if args.KEY is not None:
        if len(args.KEY) != len(args.VALUE):
            raise Exception('each -K key must have matching -V')
        else:
            for i, val in enumerate(args.KEY):
                params[val[0]] = args.VALUE[i][0]
    integration = Integration(args.repo, branch=args.branch, build_param=params, context=args.context)
    integration.run()
