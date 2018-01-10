import argparse
import json
import os
from circleci.base import CircleCIBase
import github_status


class CircleCI():
    def __init__(self, repo, branch):
        status_url = 'https://api.github.com/repos/{}/{}/statuses/{}'.format(
            os.environ.get('CIRCLE_PROJECT_USERNAME'),
            os.environ.get('CIRCLE_PROJECT_REPONAME'),
            os.environ.get('CIRCLE_SHA1')
        )
        self.build_param = {
            'PR_URL': os.environ.get('CIRCLE_PULL_REQUESTS'),
            'STATUS_URL': status_url,
        }
        self.circleci = CircleCIBase()
        self.repo = repo
        self.branch = branch

    def integration(self):
        data = json.dumps({'build_parameters': self.build_param})
        result = self.circleci.trigger_build(self.repo, self.branch, data)
        self._build_num = result['build_num']
        self._build_url = result['build_url']
        print "Build Number:{}".format(self._build_num)

    def status_pending(self):
        if self._build_url is None:
            raise Exception('No build has been triggered.')
        msg = 'The integration build {} started'.format(self._build_num)

        for url in self.build_param['STATUS_URL'].split(','):
            github_status.update(url, 'pending', self._build_url, msg)


def arg_parser():
    p = argparse.ArgumentParser()
    p.add_argument('-K', '--KEY', action='append', nargs=1)
    p.add_argument('-V', '--VALUE', action='append', nargs=1)
    p.add_argument('repo', type=str, help='github org/repo')
    p.add_argument('branch', type=str, help='git branch to test')
    return p.parse_args()


def cli():
    args = arg_parser()

    circle = CircleCI(args.repo, args.branch)

    if len(args.KEY) != len(args.VALUE):
        raise Exception('each -K key must have matching -V')
    else:
        for i, val in enumerate(args.KEY):
            circle.build_param[val[0]] = args.VALUE[i][0]

    circle.integration()
    circle.status_pending()
