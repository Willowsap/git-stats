import argparse
import os.path
import requests
import datetime
import pprint
import json

file_names = {
    "Issues": "issues.json",
    "PRs": "prs.json",
    "Comments": "comments.json"
}
num_per_page = "10"


def get_giturl(api_url, api_token):
    headers = {'Authorization': 'token %s' % str(api_token)}
    return requests.get(api_url, headers=headers).json()


def get_date(datetime_string):
    dt = datetime_string.split('T')
    d = [int(i) for i in dt[0].split('-')]
    t = [int(i) for i in dt[1][0:-1].split(':')]
    return datetime.datetime(d[0], d[1], d[2], t[0], t[1], t[2])


def get_date_from_stored_string(dt_string):
    return datetime.datetime(int(dt_string[0:4]), int(dt_string[4:6]), int(dt_string[6:8]))


def format_date(dt):
    return dt.strftime("%Y") + "-" + dt.strftime("%m") + "-" + dt.strftime("%d") + " " \
           + dt.strftime("%H") + ":" + dt.strftime("%M") + ":" + dt.strftime("%S")


def write_to_file(data, data_type):
    json_object = json.dumps(data, indent=4)
    with open(file_names[data_type], "w") as outfile:
        outfile.write(json_object)


def get_prs(pr_data, oldest_date):
    page = 1
    more_data = True
    oldest_date = get_date_from_stored_string(oldest_date)
    while more_data:
        data = get_giturl(
            pr_data["repo"] + "/pulls?state=all&sort=updated&per_page=" + num_per_page + "&page=" + str(page), pr_data["token"])
        pprint.pprint(data)
        if len(data) < int(num_per_page):
            more_data = False
        else:
            page += 1
        for pr in data:
            if get_date(pr["updated_at"]) < oldest_date:
                more_data = False
                break
            pr_data["data"][pr["id"]] = pr


def get_issues(issue_data, oldest_date):
    page = 1
    more_data = True
    oldest_date = get_date_from_stored_string(oldest_date)
    while more_data:
        data = get_giturl(
            issue_data["repo"] + "/issues?state=all&sort=updated&per_page=" + num_per_page + "&page=" + str(page), issue_data["token"])
        if len(data) < int(num_per_page):
            more_data = False
        else:
            page += 1
        for issue in data:
            if get_date(issue["updated_at"]) < oldest_date:
                more_data = False
                break
            if "pull_request" not in issue:
                issue_data["data"][issue["id"]] = issue


def get_comments(comment_data, oldest_date):
    page = 1
    more_data = True
    oldest_date = get_date_from_stored_string(oldest_date)
    while more_data:
        data = get_giturl(
            comment_data["repo"] + "/pulls?state=all&sort=updated&per_page=" + num_per_page + "&page=" + str(page), comment_data["token"])
        if len(data) < int(num_per_page):
            more_data = False
        else:
            page += 1
        for pr in data:
            if get_date(pr["updated_at"]) < oldest_date:
                more_data = False
                break
            pr_comments = get_giturl(pr["_links"]["comments"]["href"], comment_data["token"])
            pr_comments.extend(get_giturl(pr["_links"]["review_comments"]["href"], comment_data["token"]))
            for comment in pr_comments:
                comment_data["data"][comment["id"]] = comment


def get_data(gittoken, repo, data_type, oldest_date):
    if os.path.exists(file_names[data_type]):
        with open(file_names[data_type], 'r') as openfile:
            output_data = json.load(openfile)
    else:
        if repo is None or gittoken is None:
            print("You must provide a repo and token as this file does not already exist")
            exit(1)
        output_data = {
            "type": data_type,
            "repo": repo,
            "token": gittoken,
            "last_updated": format_date(datetime.datetime.now()),
            "data": {}
        }
    if oldest_date is None:
        oldest_date = "19900101"
    if data_type == "PRs":
        get_prs(output_data, oldest_date)
    elif data_type == "Issues":
        get_issues(output_data, oldest_date)
    elif data_type == "Comments":
        get_comments(output_data, oldest_date)
    else:
        print("Data Type must be PRs, Issues, or Comments")
        exit(1)
    write_to_file(output_data, data_type)


def prog_entry():
    parser = argparse.ArgumentParser()
    parser.add_argument("type", help="PRs, Issues, or Comments")
    parser.add_argument("--token", dest="token", help="your git api authtoken. see"
                                                      "https://docs.github.com/en/github/authenticating-to-github/keeping-your-account-and-data-secure/creating-a-personal-access-token "
                                                      "for more details")
    parser.add_argument("--repo", dest="repo",
                        help="A comma seperated list of git api urls to search. ex: https://github.ibm.com/api/v3/repos/symposium/track-and-plan")
    parser.add_argument("--oldest", dest="oldest_valid", help="oldest acceptable date")
    args = parser.parse_args()
    get_data(args.token, args.repo, args.type, args.oldest_valid)


prog_entry()


'''
"Issues" "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" "https://api.github.com/repos/AgileAppstate/givecoco-the-caffeinated-pajama-bandits" "19900101"
'''
