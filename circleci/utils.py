import re
import argparse
import yaml

def digests_to_custom_values(values, digests):
    '''
    Generates a custom values for integration using docker digests.
    Expects a values.yaml file with with tags and repo names in the following format:

    mysql:
      tag: latest
      repo: mysql
    mongo:
      tag: latest
      repo: mongo

    Expects a file containing docker digests in the following format:

    Image ID:		docker-pullable://mongo@sha256:fa24030aec1989c1df5440562282891b95a92e00e28ed05332e8f0270efe34d1
    Image ID:		docker-pullable://mysql@sha256:967a8020398f76f99ba74144e6e661f46003c685192b83d7bb87d026562319ae
    '''
    with open(values, "r") as stream:
        try:
            values = yaml.load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    #search only for a list of charts with configurable tags
    charts = []
    for chart in values:
        if type(values[chart]) is dict:
            if values[chart].get("tag"):
                charts.append(chart)

    custom_values = []
    with open(digests, "r") as image_versions:
        for line in image_versions:
            for chart in charts:
                if re.search(values[chart]["repo"], line):
                    custom_values.append('"{}": {{"repo": "{}@sha256","tag": "{}"}}'.format(
                        chart,
                        values[chart]["repo"],
                        line.split(":")[3].strip()
                    ))
    return "{{ {} }}".format(",".join(custom_values))


def arg_parser():
    p = argparse.ArgumentParser()
    p.add_argument('values', type=str, help='helm values file')
    p.add_argument("digests", type=str, help="file containing docker digests")
    return p.parse_args()

def digests_to_custom_values_cli():
    args = arg_parser()
    print digests_to_custom_values(args.values, args.digests)
