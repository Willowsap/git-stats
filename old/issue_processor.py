import csv
import datetime


def write_to_csv(path, rows):
    with open(path, 'w', encoding='UTF8', newline='') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_NONNUMERIC)
        for row in rows:
            writer.writerow(row)


def read_from_csv(path):
    output = []
    with open(path, 'r', encoding='utf-8') as f:
        file = csv.reader(f)
        first_line = True
        for lines in file:
            if first_line:
                first_line = False
            else:
                output.append(lines)
    return output


def greater(date1, date2):
    if len(date1) < 8:
        if date1[3:7] > date2[3:7]:
            return True
        elif date1[:2] > date2[:2]:
            return True
    else:
        if date1[6:] > date2[6:]:
            return True
        elif date1[3:5] > date2[3:5]:
            return True
        elif date1[:2] > date2[:2]:
            return True
    return False


def sort_dates(dates):
    n = len(dates)
    for i in range(n - 1):
        for j in range(0, n - i - 1):
            if greater(dates[j], dates[j + 1]):
                dates[j], dates[j + 1] = dates[j + 1], dates[j]


def format_section(section, stats, headers):
    output = [["Squad Name"]]
    for header in headers:
        output[0].append(header)
    if section == 1:
        print(headers)
        print(stats)
        for squad in stats:
            srow = [squad]
            for month in headers:
                if month not in stats[squad]["months"]:
                    srow.append(0)
                else:
                    srow.append(stats[squad]["months"][month]["bugs"])
            output.append(srow)
    elif section == 2:
        for squad in stats:
            srow = [squad]
            for month in headers:
                if month not in stats[squad]["months"]:
                    srow.append(0)
                else:
                    srow.append(stats[squad]["months"][month]["points"])
            output.append(srow)
    elif section == 3:
        for squad in stats:
            srow = [squad]
            for sprint in headers:
                if sprint not in stats[squad]["sprints"]:
                    srow.append(0)
                else:
                    srow.append(stats[squad]["sprints"][sprint]["points"])
            output.append(srow)
    return output


def get_squad(labels):
    labels = labels.split(',')
    for label in labels:
        if label.count("Squad") > 0:
            return str.strip(label[7:])
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


def process(input_file, output_file):
    lines = read_from_csv(input_file)
    first_section = [["Bugs per Month"]]
    second_section = [["Points per Month"]]
    third_section = [["Points per Sprint"]]
    squad_stats = {}
    month_list = []
    sprint_list = []
    for line in lines:
        squad = get_squad(line[4])
        sprint = get_sprint(line[1])
        month = line[1][5:7] + "-" + line[1][:4]
        if sprint not in sprint_list:
            sprint_list.append(sprint)
        if month not in month_list:
            month_list.append(month)
        if squad not in squad_stats:
            squad_stats[squad] = {"months": {}, "sprints": {}}
        if month not in squad_stats[squad]["months"]:
            squad_stats[squad]["months"][month] = {"points": 0, "bugs": 0}
        if sprint not in squad_stats[squad]["sprints"]:
            squad_stats[squad]["sprints"][sprint] = {"points": 0}
        squad_stats[squad]["months"][month]["points"] += float(line[3])
        squad_stats[squad]["months"][month]["bugs"] += is_bug(line[4])
        squad_stats[squad]["sprints"][sprint]["points"] += float(line[3])
    sort_dates(month_list)
    sort_dates(sprint_list)
    first_section += format_section(1, squad_stats, month_list)
    second_section += format_section(2, squad_stats, month_list)
    third_section += format_section(3, squad_stats, sprint_list)
    write_to_csv(output_file, first_section + second_section + third_section)


ainput_file = "issues.csv"
aoutput_file = "stats_processed.csv"
process(ainput_file, aoutput_file)
