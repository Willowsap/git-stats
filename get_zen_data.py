import argparse
import os.path
import requests
import datetime
import json

file_name = "issues.json"


def get_zenurl(api_url, api_token):
    headers = {'X-Authentication-Token': str(api_token)}
    return requests.get(api_url, headers=headers).json()


def get_date(datetime_string):
    dt = datetime_string.split('T')
    d = [int(i) for i in dt[0].split('-')]
    t = [int(i) for i in dt[1][0:-1].split(':')]
    return datetime.datetime(d[0], d[1], d[2], t[0], t[1], t[2])


def get_date_from_stored_string(dt_string):
    return datetime.datetime(int(dt_string[0:4]), int(dt_string[4:6]), int(dt_string[6:8]))


def write_to_file(data):
    json_object = json.dumps(data, indent=4)
    with open(file_name, "w") as outfile:
        outfile.write(json_object)


def get_issues(zentoken, repo, oldest_date):
    issues = {}
    if os.path.exists(file_name):
        with open(file_name, 'r') as openfile:
            issues = json.load(openfile)
    else:
        print("There is no " + file_name + " file. Run get_git_data")
        exit(1)
    oldest_date = get_date_from_stored_string(oldest_date)
    for _, issue in issues["data"]:
        if get_date(issue["updated_at"]) < oldest_date:
            issue["zen_data"] = get_zenurl(repo + "/issues/" + issue["number"], zentoken)
            if issue["zen_data"]["is_epic"]:
                issue["epic"] = get_zenurl(repo + "/epics/" + issue["number"], zentoken)
    write_to_file(issues)


def prog_entry():
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", help="your zen repo url", required=True)
    parser.add_argument("zen_token", help="your zenhub api authtoken")
    parser.add_argument("oldest_valid", help="oldest ")
    args = parser.parse_args()
    get_issues(args.token, args.repo, args.oldest_valid)


prog_entry()
