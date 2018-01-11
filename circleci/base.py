import os
import requests
from requests.auth import HTTPBasicAuth


class CircleCIBase():
    # https://circleci.com/docs/api/v1-reference/
    def __init__(self):
        token = os.environ.get('CIRCLE_TOKEN')
        if token is None:
            raise Exception("Must set env var CIRCLE_TOKEN")
        self.auth = HTTPBasicAuth(token, '')
        self.github_url = 'https://circleci.com/api/v1.1/project/github'

    def request(self, verb, url, data=None):
        headers = {
            'Content-Type': 'application/json'
        }
        if verb == 'get':
            resp = requests.get(url, auth=self.auth, headers=headers)
        elif verb == 'post':
            resp = requests.post(url, auth=self.auth, headers=headers, data=data)

        if 200 <= resp.status_code < 300:
            return resp.json()
        else:
            print resp.text

    def get(self, url):
        return self.request('get', url)

    def post(self, url, data):
        return self.request('post', url, data=data)

    # get running builds
    def get_build_status(self, repo, branch=None, filter='running', limit=30):
        # GET: /project/:vcs-type/:username/:project
        if branch is not None:
            repo = "{}/tree/{}".format(repo, branch)
        url = '{}/{}?filter={}&limit={}'.\
            format(self.github_url, repo, filter, limit)
        return self.get(url)

    def get_single_build_status(self, repo, build_num):
        # GET: /project/:vcs-type/:username/:project/:build_num
        url = '{}/{}/{}'.\
            format(self.github_url, repo, build_num)
        return self.get(url)

    # trigger a new build in circleci
    def trigger_build(self, repo, branch, data):
        # https://circleci.com/docs/api/v1-reference/#new-build-branch
        # POST: /project/:vcs-type/:username/:project/tree/:branch
        url = '{}/{}/tree/{}'.\
            format(self.github_url, repo, branch)
        resp = self.post(url, data)
        self.build_num = resp['build_num']
        self.build_url = resp['build_url']
        # print "Build Number: {}".format(self._build_num)
        return resp

    def github_status_pending(self, context=None, url=None):
        if self.build_url is None:
            raise Exception('No build has been triggered.')
        if context is None:
            context = 'ci/circleci-integration'
        desc = 'The integration build {} started'.format(self._build_num)

        GithubStatus().create_status('pending', self.build_url, desc, context, url=url)
