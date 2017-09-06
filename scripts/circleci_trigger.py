import argparse
import base64
import json
import os
import requests
import gh_status


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

        token = os.environ.get('CIRCLE_TOKEN')
        self._auth = base64.standard_b64encode('{}:'.format(token))

        # NOTE: https://circleci.com/docs/api/v1-reference/#new-build-branch
        self._url = 'https://circleci.com/api/v1.1/project/github/{}/tree/{}'.\
            format(repo, branch)

    def integration(self):
        data = json.dumps({'build_parameters': self.build_param})
        headers = {
            'Authorization': 'Basic {}'.format(self._auth),
            'Content-Type': 'application/json'
        }
        result = requests.post(self._url, data=data, headers=headers)
        self._build_num = result.json()['build_num']
        self._build_url = result.json()['build_url']
        print result.text

    def status_pending(self):
        if self._build_url is None:
            raise Exception('No build has been triggered.')
        msg = 'The integration build {} started'.format(self._build_num)

        for url in self.build_param['STATUS_URL'].split(','):
            gh_status.update(url, 'pending', self._build_url, msg)


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
