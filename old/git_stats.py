import requests
import datetime
import csv
import os
import argparse
from pprint import pprint


def new_pa_stat():
    return {
        "prs": 0,
        "total_comments_received": 0,
        "avg_comments_received": 0,
        "total_loc": 0,
        "avg_loc": 0,
        "total_comments_made": 0,
        "total_approvals_made": 0
    }


def new_pr_stat():
    return {"prs": []}


# returns data from a given url using a given auth token
def get_url(api_url, api_token):
    headers = {'Authorization': 'token %s' % str(api_token)}
    return requests.get(api_url, headers=headers).json()


def get_prs(url, timeframe, token):
    num_pr_per_page = "30"
    page = 1
    state = "closed"
    more_prs = True
    pr_data = []
    if timeframe[0] == "-":
        min_date = datetime.datetime(1600, 1, 1)
    else:
        min_date = datetime.datetime(int(timeframe[4:8]), int(timeframe[0:2]), int(timeframe[2:4]))
    if timeframe[-1] == "-":
        max_date = datetime.datetime.now()
    else:
        max_date = datetime.datetime(int(timeframe[13:17]), int(timeframe[9:11]), int(timeframe[11:13]))
    while more_prs:
        prs = get_url(url + "?state=" + state + "&per_page=" + num_pr_per_page + "&page=" + str(page), token)
        page += 1
        for pr in prs:
            if type(pr) is not dict:
                print("Error in getting pull requests. Received: ")
                pprint(pr)
                exit(1)
            created = get_date(pr["created_at"])
            if created < min_date:
                more_prs = False
                break
            if min_date <= created <= max_date:
                pr_data.append(pr)
        if len(prs) < int(num_pr_per_page):
            more_prs = False
    return pr_data


def get_file_changes(api_url, api_token):
    files_changed = 0
    lines_changed = 0
    files = get_url(api_url + "/files", api_token)
    for file in files:
        files_changed += 1
        lines_changed += file["changes"]
    return {"files": files_changed, "lines": lines_changed}


# convert the date as returned by git to a datetime object
def get_date(datetime_string):
    dt = datetime_string.split('T')
    d = [int(i) for i in dt[0].split('-')]
    t = [int(i) for i in dt[1][0:-1].split(':')]
    return datetime.datetime(d[0], d[1], d[2], t[0], t[1], t[2])


# returns an object where each key is a user and their value is the number of comments they made
def get_commentor_counts(comment_data):
    commentor_counts = {}
    for comment in comment_data:
        name = comment['user']['login']
        if name not in commentor_counts:
            commentor_counts[name] = 1
        else:
            commentor_counts[name] += 1
    return commentor_counts


def get_header(style):
    # PR List
    if style == 1:
        return ["PR ID", "Owner", "Repo", "Submitted", "Closed", "Elapsed",
                "Comments", "Files Changed", "Lines Changed", "Commits", "Title"]
    # Monthly Programmer Activity List
    elif style == 2:
        return ["Programmer", "Month", "PRs Submitted", "Total Comments Received",
                "Average Comments Received", "Total Loc Updated", "Average Loc Updated",
                "Comments Provided on Others' PRs", "Approvals Provided on Others' PRs"]
    # Comment List
    elif style == 3:
        return ["PR id", "Comment id", "Date / Time Submitted", "Comment Provider", "Size of Comment"]
    else:
        return []


def format_output(style, output_data):
    formatted_data = []
    avg_time = []
    if style == 1:
        for user in output_data:
            if isinstance(output_data[user], str):
                avg_time.append(output_data[user])
            else:
                for pr in output_data[user]["prs"]:
                    formatted_data.append([
                        pr["pr_id"], pr["owner"], pr["repo"], pr["submitted"], pr["closed"],
                        pr["elapsed"], pr["comments"], pr["files_changed"], pr["lines_changed"],
                        pr["commits"], pr["title"]
                    ])
        formatted_data.insert(0, avg_time)
    elif style == 2:
        for user in output_data:
            for month in output_data[user]:
                md = output_data[user][month]
                formatted_data.append([
                    user, month, md["prs"], md["total_comments_received"], md["avg_comments_received"],
                    md["total_loc"], md["avg_loc"], md["total_comments_made"], md["total_approvals_made"]
                ])
    elif style == 3:
        for comment in output_data:
            formatted_data.append([
                comment["pr_id"],
                comment["comment_id"],
                comment["submitted"],
                comment["commentor"],
                comment["size"]
            ])
    return formatted_data


def verify_args(args):
    if args.style != 1 and args.style != 2 and args.style != 3:
        print("style argument must be 1, 2, or 3. run python git_stats.py help for more informatiopn")
        exit(1)


# dt_type must be either 'date' or 'time'
def format_date(dt, dt_type):
    output = ""
    if dt_type == "date":
        output = dt.strftime("%Y") + "-" + dt.strftime("%m") + "-" + dt.strftime("%d") + " "\
            + dt.strftime("%H") + ":" + dt.strftime("%M") + ":" + dt.strftime("%S")
    elif dt_type == "time":
        if 'day' in dt:
            parts = dt.split(', ')
            days = int(parts[0].split(' ')[0])
            time_parts = parts[1].split(':')
            hours = int(time_parts[0])
            while days > 0:
                hours += 24
                days -= 1
            output = str(hours) + ":" + time_parts[1] + ":" + time_parts[2]
        else:
            output = dt
    else:
        print("Invalid type passed to format_date")
        exit(1)
    return output


def get_pr_list(pr_data, pr_stats, token, exclude_comments):
    deltas = []
    for pr in pr_data:
        creator = pr["user"]["login"]
        # if this user has not been encountered yet, add them to the pr_stats object
        if creator not in pr_stats:
            pr_stats[creator] = new_pr_stat()
        # add a new pull request object for this user
        pr_stats[creator]["prs"].append(
            {"pr_id": pr["_links"]["html"]["href"],
             "owner": creator,
             "repo": pr["head"]["repo"]["name"],
             "submitted": None,
             "closed": None,
             "elapsed": None,
             "comments": 0,
             "files_changed": 0,
             "lines_changed": 0,
             "commits": 0,
             "title": pr["body"]})
        # index in the creator's pr list of this pr
        pr_i = len(pr_stats[creator]["prs"]) - 1
        # ----- Enter date pr_stats -----
        creation_date = get_date(pr["created_at"])
        closed_date = get_date(pr["closed_at"])
        # pr_stats[creator]["prs"][pr_i]["submitted"] = creation_date.strftime("%c")
        # pr_stats[creator]["prs"][pr_i]["closed"] = closed_date.strftime("%c")
        # pr_stats[creator]["prs"][pr_i]["elapsed"] = str(closed_date - creation_date)
        pr_stats[creator]["prs"][pr_i]["submitted"] = format_date(creation_date, 'date')
        pr_stats[creator]["prs"][pr_i]["closed"] = format_date(closed_date, 'date')
        pr_stats[creator]["prs"][pr_i]["elapsed"] = format_date(str(closed_date - creation_date), 'time')
        deltas.append(closed_date - creation_date)
        # ----- Enter comments pr_stats -----
        if not exclude_comments:
            comments = get_url(pr["_links"]["comments"]["href"] + "?state=all", token)
            comments.extend(get_url(pr["_links"]["review_comments"]["href"] + "?state=all", token))
            pr_stats[creator]["prs"][pr_i]["comments"] = len(comments)
            # for commentor, count in get_commentor_counts(comments).items():
            #    if commentor not in pr_stats:
            #        pr_stats[commentor] = new_pr_stat()
            #    pr_stats[commentor]["comments"] += count
        # ----- Enter changes pr_stats
        changes = get_file_changes(pr["_links"]["commits"]["href"][:-8], token)
        pr_stats[creator]["prs"][pr_i]["files_changed"] = changes["files"]
        pr_stats[creator]["prs"][pr_i]["lines_changed"] = changes["lines"]
        # ----- Enter commit pr_stats -----
        commits = get_url(pr["_links"]["commits"]["href"] + "?state=all", token)
        pr_stats[creator]["prs"][pr_i]["commits"] = len(commits)
    if len(deltas) > 0:
        pr_stats["avg_time"] = ("avg open time: " + str(sum(deltas, datetime.timedelta(0)) / len(deltas)))


def get_pa_list(pr_data, pa_stats, token):
    for pr in pr_data:
        creator = pr["user"]["login"]
        date = get_date(pr["created_at"])
        month_year = date.strftime("%B") + date.strftime("%Y")
        # if this user has not been encountered yet, add them to the pr_stats object
        if creator not in pa_stats:
            pa_stats[creator] = {}
        if month_year not in pa_stats[creator]:
            pa_stats[creator][month_year] = new_pa_stat()
        pa_stats[creator][month_year]["prs"] += 1
        # ----- Enter comments pa_stats -----
        comments = get_url(pr["_links"]["comments"]["href"] + "?state=all", token)
        comments.extend(get_url(pr["_links"]["review_comments"]["href"] + "?state=all", token))
        pa_stats[creator][month_year]["total_comments_received"] += len(comments)
        pa_stats[creator][month_year]["avg_comments_received"] = \
            pa_stats[creator][month_year]["total_comments_received"] / pa_stats[creator][month_year]["prs"]
        for commentor, count in get_commentor_counts(comments).items():
            if commentor not in pa_stats:
                pa_stats[commentor] = {}
            if month_year not in pa_stats[commentor]:
                pa_stats[commentor][month_year] = new_pa_stat()
            pa_stats[commentor][month_year]["total_comments_made"] += count
        # files = get_url(pr["_links"]["comments"]["href"][:-8] + "/files", token)
    pprint(pa_stats)


def get_cm_list(pr_data, cm_stats, token):
    for pr in pr_data:
        comments = get_url(pr["_links"]["comments"]["href"] + "?state=all", token)
        comments.extend(get_url(pr["_links"]["review_comments"]["href"] + "?state=all", token))
        for comment in comments:
            cm_stats.append({
                "pr_id": pr["_links"]["html"]["href"],
                "comment_id": comment["html_url"],
                "submitted": get_date(comment["created_at"]).strftime("%c"),
                "commentor": comment["user"]["login"],
                "size": len(comment["body"])
            })


def write_to_csv(path, rows):
    with open(path, 'w', encoding='UTF8', newline='') as f:
        writer = csv.writer(f)
        for row in rows:
            writer.writerow(row)


def get_stats(token, repos, filename, timeframe, style, exclude_comments):
    # change to make these the same in the future
    if style == 3:
        output = []
    else:
        output = {}
    for repo in repos:
        aurl = repo + "/pulls"
        if style == 1:
            get_pr_list(get_prs(aurl, timeframe, token), output, token, exclude_comments)
        elif style == 2:
            if exclude_comments:
                print("You must include comment data when using style 2")
                exit(1)
            else:
                get_pa_list(get_prs(aurl, timeframe, token), output, token)
        elif style == 3:
            if exclude_comments:
                print("You must include comment data when using style 3")
                exit(1)
            else:
                get_cm_list(get_prs(aurl, timeframe, token), output, token)
    script_dir = os.path.dirname(__file__)
    abs_file_path = os.path.join(script_dir, filename)
    formatted_output = format_output(style, output)
    formatted_output.insert(0, get_header(style))
    write_to_csv(abs_file_path, formatted_output)


def prog_entry():
    parser = argparse.ArgumentParser()
    parser.add_argument("token", help="your git api authtoken. see"
                                      "https://docs.github.com/en/github/authenticating-to-github/keeping-your-account-and-data-secure/creating-a-personal-access-token "
                                      "for more details")
    parser.add_argument("repos",
                        help="A comma seperated list of git api urls to search. ex: https://github.ibm.com/api/v3/repos/symposium/track-and-plan")
    parser.add_argument("output_file", help="the name of the file you want the results output to. ex: activity.csv")
    parser.add_argument("timeframe",
                        help="the starting date to the ending date in which to search pull requests. timeframe should be in the form: mmddyyy-mmddyyy. "
                             "you can omit the date before and/or after the dash. -mmddyyy means all pull requests before the given date. "
                             "mmddyyy- means all pull requests after the given date. - means all pull requests")
    parser.add_argument("style", help="1 for pull request list. 2 for programmer activity list. 3 for comment list",
                        type=int)
    parser.add_argument("--nc", help="do not retrieve comment data", action="store_true")
    args = parser.parse_args()
    verify_args(args)
    get_stats(args.token, args.repos.split(','), args.output_file, args.timeframe, int(args.style), args.nc)


prog_entry()
