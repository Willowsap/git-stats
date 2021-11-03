import csv
import datetime
import os.path
import json
import argparse

input_file_names = {
    "Issues": "issues.json",
    "PRs": "prs.json",
    "Comments": "comments.json"
}
output_file_names = {
    "Issues": "issues.csv",
    "PRs": "prs.csv",
    "Comments": "comments.csv"
}


def write_to_csv(data_type, rows):
    with open(output_file_names[data_type], 'w', encoding='UTF8', newline='') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
        for row in rows:
            writer.writerow(row)


def read_data_file(data_type):
    if os.path.exists(input_file_names[data_type]):
        with open(input_file_names[data_type], 'r') as openfile:
            return json.load(openfile)
    else:
        print("File: " + input_file_names[data_type] + "does not exist. Run get_data first.")
        exit(1)


def get_squad(labels):
    for label in labels:
        if label["name"].count("Squad") > 0:
            return str.strip(label["name"][7:])
    return "No Squad"


def is_bug(line):
    if line.count("Bug") > 0:
        return 1
    else:
        return 0


def get_days_to_add(weekday):
    return (9 - weekday) % 7


def get_sprint(close_date):
    date = datetime.datetime(int(close_date[:4]), int(close_date[5:7]), int(close_date[8:10]))
    date = date + datetime.timedelta(days=(9 - int(date.strftime("%w"))) % 7)
    return date.strftime("%m") + "-" + date.strftime("%d") + "-" + date.strftime("%Y")


def get_labels(labels):
    just_names = []
    for label in labels:
        just_names.append(label["name"])
    return just_names


def get_date(datetime_string):
    dt = datetime_string.split('T')
    d = [int(i) for i in dt[0].split('-')]
    t = [int(i) for i in dt[1][0:-1].split(':')]
    return datetime.datetime(d[0], d[1], d[2], t[0], t[1], t[2])


def format_date(dt):
    return dt.strftime("%Y") + "-" + dt.strftime("%m") + "-" + dt.strftime("%d") + " " \
           + dt.strftime("%H") + ":" + dt.strftime("%M") + ":" + dt.strftime("%S")


def process_prs(data):
    pass


def process_comments(data):
    pass


def process_issues(data):
    issues = [["Issue URL", "Opened", "Closed", "Squad", "Labels"]]
    for _, issue in data["data"].items():
        issues.append([issue["url"], format_date(get_date(issue["created_at"])),
                       format_date(get_date(issue["closed_at"])), get_squad(issue["labels"]), get_labels(issue["labels"])])
    write_to_csv("Issues", issues)


def prog_entry():
    parser = argparse.ArgumentParser()
    parser.add_argument("type", help="PRs, Issues, or Comments")
    args = parser.parse_args()
    data = read_data_file(args.type)
    if args.type == "Issues":
        process_issues(data)
    elif args.type == "PRs":
        process_prs(data)
    elif args.type == "Comments":
        process_comments(data)
    else:
        print("Type must be Issues, PRs, or Comments")
        exit(1)


prog_entry()
