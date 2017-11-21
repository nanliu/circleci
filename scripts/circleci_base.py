import base64
import os
import requests


class CircleCIBase():
    def __init__(self):
        token = os.environ.get('CIRCLE_TOKEN')
        self._auth = base64.standard_b64encode('{}:'.format(token))
        self.github_url = 'https://circleci.com/api/v1.1/project/github'

    def post(self, url, data):
        headers = {
            'Authorization': 'Basic {}'.format(self._auth),
            'Content-Type': 'application/json'
        }
        return requests.post(url, data=data, headers=headers).json()

    def get(self, url):
        headers = {
            'Authorization': 'Basic {}'.format(self._auth),
            'Content-Type': 'application/json'
        }
        return requests.get(url, headers=headers).json()

    # get running builds
    def get_build_status(self, repo, filter='running'):
        url = '{}/{}?filter={}'.\
            format(self.github_url, repo, filter)
        print "Hitting URL: {}".format(url)
        return self.get(url)

    # trigger a new build in circleci
    def trigger_build(self, repo, branch, data):
        # NOTE: https://circleci.com/docs/api/v1-reference/#new-build-branch
        url = '{}/{}/tree/{}'.\
            format(self.github_url, repo, branch)
        result = self.post(url, data)
        print result.text
        return result
