"""
Parses pull request description and generates custom values on circleci. Expects following format
in the pull request description.

```
pull_requests:
- link
- link
```

"""
import argparse
import os
import re
import requests
import yaml

import circleci_trigger


class Pull_Request:
    def __init__(self, url):
        self.url = url
        validate_url(url, '^https?:\/\/github.com\/.*\/pull\/\d+\/?$')
        #Remove trailing slash
        if url[-1] == '/':
            url = url[:-1]
        api_pr_url = (url.replace("https://github.com", "https://api.github.com/repos", 1)
                     ).replace("pull", "pulls")
        github_token = os.environ['GH_OAUTH_TOKEN']
        auth_headers = {'Authorization': 'token {}'.format(github_token)}
        pull_request = requests.get(api_pr_url, headers=auth_headers).json()
        self.description = pull_request['body']
        self.repo = pull_request['head']['repo']['name']
        self.sha1 = pull_request['head']['sha']
        self.owner = pull_request['head']['repo']['owner']['login']

    def get_description_section(self, yaml_section, delimiter):
        """
        Gets yaml in the pull request description. Otherwise returns None.

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

def validate_url(url, regex):
    """
    Will validate a url against a certain regex rule. Exits on failure

    Args:
    url (string)
    regex (string): the regex used to check the url
    """
    r = re.compile(regex)
    if not r.match(url):
        raise ValueError('ERROR: Invalid url: ' + url)


def validate_integration_branch(repo, integration_branch):
    """
    Will validate that the given integration branch exists

    Args:
    repo (string): github repo of the branch
    integration_branch (string)
    """
    github_token = os.environ['GH_OAUTH_TOKEN']
    auth_headers = {'Authorization': 'token {}'.format(github_token)}
    branch_url = 'https://api.github.com/repos/{}/branches/{}'.format(repo, integration_branch)
    branch = requests.get(branch_url, headers=auth_headers).json()
    try:
        print "Found branch {}".format(branch['name'])
        return branch['commit']['sha']
    except:
        raise Exception("ERROR: Integration branch not found. Does it exist?")


def trigger_integration(args, pull_requests, current_pull_request, integration_branch=None):
    """
    Determines build parameters using an array of pull request urls and then
    triggers an integration

    Args:
    integration_branch (string): branch to use for integration
    pull_requests (array of strings): array of urls
    current_pull_request (object): pull request object
    """
    if integration_branch:
        circle = circleci_trigger.CircleCI(args.repo, integration_branch, args.context)
    else:
        circle = circleci_trigger.CircleCI(args.repo, args.branch)
    branch_sha = validate_integration_branch(circle.repo, circle.branch)
    branch_status_url = 'https://api.github.com/repos/{}/statuses/{}'.format(
        circle.repo,
        branch_sha
    )

    if pull_requests:
        pull_requests.append(current_pull_request.url)
        generate_build_parameters(circle, pull_requests, branch_status_url)
    else:
        default_build_parameters(args, circle, current_pull_request, branch_status_url)
    print circle.build_param
    circle.integration()
    circle.status_pending()


def generate_build_parameters(circle, pull_requests, branch_status_url):
    """
    Generates build parameters and adds them to the circle object

    Args:
    circle (object): object being modified
    pull_requests (array of strings)
    """
    circle.build_param['PR_URL'] = pull_requests
    custom_values = ''
    status_urls = ''
    for p in pull_requests:
        pull_request = Pull_Request(p)
        custom_values = custom_values + '"{}": {{"repo": "{}","tag": "{}"}},'.format(
            pull_request.repo.replace('-', '_'),
            pull_request.repo,
            pull_request.sha1
        )
        status_urls = status_urls + 'https://api.github.com/repos/{}/{}/statuses/{},'.format(
            pull_request.owner,
            pull_request.repo,
            pull_request.sha1
        )
    if branch_status_url and (circle.branch != 'master'):
        status_urls = branch_status_url + ',' + status_urls
    # Remove trailing comma
    if len(custom_values) > 0:
        custom_values = custom_values[:-1]
    if len(status_urls) > 0:
        status_urls = status_urls[:-1]
    custom_values = '{{ {} }}'.format(custom_values)
    circle.build_param['CUSTOM_VALUES'] = custom_values
    circle.build_param['STATUS_URL'] = status_urls


def default_build_parameters(args, circle, current_pull_request, branch_status_url):
    """
    Adds default build parameters to the circle object

    Args:
    circle (object): object being modified
    current_pull_request (object): pull request object
    """
    if current_pull_request:
        circle.build_param['PR_URL'] = current_pull_request.url
        custom_values = '"{}": {{"repo": "{}","tag": "{}"}}'.format(
            current_pull_request.repo.replace('-', '_'),
            current_pull_request.repo,
            current_pull_request.sha1
        )
        circle.build_param['CUSTOM_VALUES'] = '{{ {} }}'.format(custom_values)
    if branch_status_url and (circle.branch != 'master'):
        circle.build_param['STATUS_URL'] = branch_status_url
    if args.KEY is not None:
        if len(args.KEY) != len(args.VALUE):
            raise Exception('each -K key must have matching -V')
        else:
            for i, val in enumerate(args.KEY):
                circle.build_param[val[0]] = args.VALUE[i][0]


def arg_parser():
    p = argparse.ArgumentParser()
    p.add_argument('-c', '--context', default='ci/cirleci-integration',
                   help='git sha context message')
    p.add_argument('-K', '--KEY', action='append', nargs=1)
    p.add_argument('-V', '--VALUE', action='append', nargs=1)
    p.add_argument('repo', type=str, help='github org/repo')
    p.add_argument('branch', type=str, help='git branch to test')
    return p.parse_args()


def cli():
    args = arg_parser()
    urls = []
    current_pull_request = None
    integration_branch = None
    pull_request_url = os.environ.get('CIRCLE_PULL_REQUEST')
    if pull_request_url:
        current_pull_request = Pull_Request(pull_request_url)
        urls = current_pull_request.get_description_section('pull_requests', '```')
        integration_branch = current_pull_request.get_description_section('integration_branch', '```')
    trigger_integration(args, urls, current_pull_request, integration_branch)
