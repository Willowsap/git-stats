import requests
import argparse
from pprint import pprint


def get_url(api_url, api_token):
    headers = {'X-Authentication-Token': str(api_token)}
    return requests.get(api_url, headers=headers).json()


def get_zen_stats(token, repos):
    for repo in repos:
        data = get_url(repo, token)
        pprint(data)


def prog_entry():
    parser = argparse.ArgumentParser()
    parser.add_argument("token", help="your zenhub api authtoken")
    parser.add_argument("repos", help="a list of comma seperated zenhub urls to search")
    args = parser.parse_args()
    get_zen_stats(args.token, args.repos.split(','))


prog_entry()
