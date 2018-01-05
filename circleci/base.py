import base64
import os
import requests


class CircleCIBase():
    def __init__(self):
        token = os.environ.get('CIRCLE_TOKEN')
        if token is None:
            raise Exception("Must set env var CIRCLE_TOKEN")
        self._auth = base64.standard_b64encode('{}:'.format(token))
        self.github_url = 'https://circleci.com/api/v1.1/project/github'

    def post(self, url, data):
        headers = {
            'Authorization': 'Basic {}'.format(self._auth),
            'Content-Type': 'application/json'
        }
        resp = requests.post(url, data=data, headers=headers)
        return resp.json()

    def get(self, url):
        headers = {
            'Authorization': 'Basic {}'.format(self._auth),
            'Content-Type': 'application/json'
        }
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            return resp.json()
        else:
            print resp.text

    # get running builds
    def get_build_status(self, repo, branch=None, filter='running', limit=30):
        if branch is not None:
            repo = "{}/tree/{}".format(repo, branch)
        url = '{}/{}?filter={}&limit={}'.\
            format(self.github_url, repo, filter, limit)
        return self.get(url)

    def get_single_build_status(self, repo, build_num):
        url = '{}/{}/{}'.\
            format(self.github_url, repo, build_num)
        return self.get(url)

    # trigger a new build in circleci
    def trigger_build(self, repo, branch, data):
        # NOTE: https://circleci.com/docs/api/v1-reference/#new-build-branch
        url = '{}/{}/tree/{}'.\
            format(self.github_url, repo, branch)
        result = self.post(url, data)
        return result
