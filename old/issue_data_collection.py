import requests
import datetime
import csv
from pprint import pprint


def get_issue_stat():
    return {
        "issue_num": "-1",
        "title": "BLANK ISSUE",
        "opened": "",
        "closed": "",
        "opened_by": "",
        "points": "0",
        "labels": "",
        "parent": "",
        "children": ""
    }


def get_giturl(api_url, api_token):
    headers = {'Authorization': 'token %s' % str(api_token)}
    return requests.get(api_url, headers=headers).json()


def get_zenurl(api_url, api_token):
    headers = {'X-Authentication-Token': str(api_token)}
    return requests.get(api_url, headers=headers).json()


def get_date(datetime_string):
    dt = datetime_string.split('T')
    d = [int(i) for i in dt[0].split('-')]
    t = [int(i) for i in dt[1][0:-1].split(':')]
    return datetime.datetime(d[0], d[1], d[2], t[0], t[1], t[2])


def format_date(dt):
    return dt.strftime("%Y") + "-" + dt.strftime("%m") + "-" + dt.strftime("%d") + " " \
           + dt.strftime("%H") + ":" + dt.strftime("%M") + ":" + dt.strftime("%S")


def convert_to_list(issue_data):
    output = [["Issue Number", "Title", "Opened", "Closed", "Creator", "# Points", "Labels", "Parent", "Children"]]
    for issue in issue_data:
        if issue["title"] != "BLANK ISSUE":
            output.append([issue["issue_num"], issue["title"], issue["opened"], issue["closed"], issue["creator"],
                           issue["points"], issue["labels"], issue["parent"], issue["children"]])
    return output


def get_issue_data(gittoken, zentoken, giturl, zenurl, oldest_date):
    issues = {}
    num_per_page = "30"
    page = 1
    more_issues = True
    while more_issues:
        data = get_giturl(
            giturl + "/issues?state=closed&sort=updated&per_page=" + num_per_page + "&page=" + str(page), gittoken)
        if len(data) < int(num_per_page):
            more_issues = False
        else:
            page += 1
        for issue in data:
            if get_date(issue["closed_at"]) < oldest_date:
                more_issues = False
                break
            if "pull_request" not in issue:
                iid = issue["number"]
                if iid not in issues:
                    issues[iid] = get_issue_stat()
                zen_data = get_zenurl(zenurl + "/issues/" + str(iid), zentoken)
                issues[iid]["issue_num"] = iid
                issues[iid]["title"] = issue["title"]
                issues[iid]["opened"] = format_date(get_date(issue["created_at"]))
                issues[iid]["closed"] = format_date(get_date(issue["closed_at"]))
                issues[iid]["creator"] = issue["user"]["login"]
                # get points
                if "estimate" in zen_data:
                    issues[iid]["points"] = str(zen_data["estimate"]["value"])
                # get labels
                for label in issue["labels"]:
                    issues[iid]["labels"] += label["name"] + ", "
                if len(issues[iid]["labels"]) > 2:
                    issues[iid]["labels"] = issues[iid]["labels"][:-2]
                # get children
                if zen_data["is_epic"]:
                    epic_data = get_zenurl(zenurl + "/epics/" + str(issue["number"]), zentoken)
                    for child in epic_data["issues"]:
                        issues[iid]["children"] += str(child["issue_number"]) + ", "
                        if child["issue_number"] not in issues:
                            issues[child["issue_number"]] = get_issue_stat()
                        issues[child["issue_number"]]["parent"] = str(iid)
                    if len(issues[iid]["children"]) > 2:
                        issues[iid]["children"] = issues[iid]["children"][:-2]
    write_to_csv("issue_stats.csv", convert_to_list(issues))


def write_to_csv(path, rows):
    with open(path, 'w', encoding='UTF8', newline='') as f:
        writer = csv.writer(f, quoting='csv.QUOTE_NONNUMERIC')
        for row in rows:
            writer.writerow(row)


agittoken = "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"
azentoken = ""
agiturl = "https://api.github.com/repos/AgileAppstate/givecoco-the-caffeinated-pajama-bandits"
azenurl = ""
aoldest = datetime.datetime(2020, 9, 2)  # year - month - day
get_issue_data(agittoken, azentoken, agiturl, azenurl, aoldest)
