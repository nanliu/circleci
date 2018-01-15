import argparse
import os
import requests
import json

from circleci.base import CircleCIBase
from circleci.github_status import GithubPullRequest, GithubStatus


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
            if GithubPullRequest(pr).active:
                result = result + [pr]
            else:
                print("{} is not open and dropped from integration tests".format(pr))
        return result

    def filter_integration_branch(self, pull_requests):
        result = []
        for pr in pull_requests:
            p = GithubPullRequest(pr)
            if p.repo_full_name.lower() == self.repo.lower():
                print("Switching integration to {} branch {}".format(pr, p.branch))
                self.branch = p.branch
            else:
                result = result + [pr]
        return result

    def run(self):
        if os.environ.get('CIRCLE_PULL_REQUEST'):
            # NOTE: This is integration for a PR
            current_pr = GithubPullRequest(os.environ.get('CIRCLE_PULL_REQUEST'))
            pull_requests = self.filter_active_pr(current_pr.pull_requests())
            pull_requests = self.filter_integration_branch(pull_requests)
            # NOTE: make sure current PR is in the set
            pull_requests = set(pull_requests + [os.environ.get('CIRCLE_PULL_REQUEST')])
            self.build_param['PR_URL'] = ','.join(pull_requests)

            self.status_urls = [ GithubPullRequest(pr).status_url for pr in pull_requests ]
            self.build_param['STATUS_URL'] = ','.join(self.status_urls)
            self.build_param['STATUS_CONTEXT'] = self.context

            custom_values = [ GithubPullRequest(pr).custom_value() for pr in pull_requests ]
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
                'pending', self.build_url, desc, self.context, url=url)


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
