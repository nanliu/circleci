import argparse
import json
import os
import requests


def arg_parser():
    p = argparse.ArgumentParser()
    p.add_argument('-u', '--url', default=os.environ.get('STATUS_URL'),
                   help='git commit sha1 URL')
    p.add_argument('-c', '--context', default='ci/cirleci-integration',
                   help='git status context message')
    p.add_argument('state', type=str,
                   help='CI state (running, success, failed)')
    p.add_argument('target', type=str, help='CI job target URL')
    p.add_argument('description', type=str, help='CI job description')
    return p.parse_args()


def update(url, context, state, target, desc):
    oauth = os.environ.get('GH_OAUTH_TOKEN')
    if oauth is None:
        raise Exception('Missing environment variable GH_OAUTH_TOKEN')
    headers = {'Authorization': 'token {}'.format(oauth)}
    data = json.dumps({
        'state': state,
        'target_url': target,
        'description': desc,
        'context': context
    })
    result = requests.post(url, data=data, headers=headers)
    print result.text


def cli():
    args = arg_parser()

    for url in args.url.split(','):
        update(url, args.context, args.state, args.target, args.description)
