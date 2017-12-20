import argparse
import json
import os
import requests


def arg_parser():
    p = argparse.ArgumentParser()
    p.add_argument('-u', '--url', default=os.environ.get('STATUS_URL'),
                   help='git commit sha1 URL')
    p.add_argument('state', type=str,
                   help='CI state (running, success, failed)')
    p.add_argument('target', type=str, help='CI job target URL')
    p.add_argument('description', type=str, help='CI job description')
    return p.parse_args()


def headers():
    oauth = os.environ.get('GH_OAUTH_TOKEN')
    if oauth is None:
        raise Exception('Missing environment variable GH_OAUTH_TOKEN')
    return {
        'Authorization': 'token {}'.format(oauth),
        'Content-Type': 'application/json'
    }


def update(url, state, target, desc):
    data = json.dumps({
        'state': state,
        'target_url': target,
        'description': desc,
        'context': 'ci/circleci-integration'
    })
    result = requests.post(url, data=data, headers=headers())
    print result.text


def get(url):
    resp = requests.get(url, headers=headers())
    if resp.status_code == 200:
        return resp.json()
    else:
        print resp.text


def cli():
    args = arg_parser()

    for url in args.url.split(','):
        update(url, args.state, args.target, args.description)
