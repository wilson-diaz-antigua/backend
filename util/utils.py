import logging
import re
import time
from datetime import date, datetime
from itertools import zip_longest
from pathlib import Path
from typing import Union

from dateparser.search import search_dates

stopsPath = (
    Path(__file__).parent.parent.parent / "alertsDisplayApp" / "util" / "stops.csv"
)
print(stopsPath)
logging.basicConfig(
    filename="logging.log",
    level=logging.DEBUG,
    format="%(levelname)s:%(asctime)s: %(message)s",
)


def dateparsing(date) -> dict:
    res = search_dates(date)
    timer = datetime.strptime("00:00:00", "%H:%M:%S").time()
    datePeriod = {"dateText": date, "time": [], "date": []}
    for x in res:

        if x[1].strftime("%a, %b %d") not in datePeriod["date"]:
            datePeriod["date"].append(x[1].strftime("%a, %b %d"))
        if (
            x[1].time() != timer
            and x[1].time().strftime("%I:%M %p") not in datePeriod["time"]
        ):
            datePeriod["time"].append(x[1].time().strftime("%I:%M %p"))

    return datePeriod


def stopid(stop: str):
    import csv

    stop = stop
    col = {}

    with stopsPath.open() as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            if row["stop_name"] not in col:
                col[row["stop_id"]] = col.setdefault(row["stop_id"], [row["stop_name"]])
            else:
                col[row["stop_id"]] += [row["stop_name"]]

        if stop != "None":
            return f"{col[stop][0]}"
        else:
            return "None"


# Define a function to convert a timestamp to a datetime object if it isn't already
def convert_to_datetime(timestamp: Union[int, float, datetime]) -> datetime:
    if not isinstance(timestamp, datetime):
        return datetime.fromtimestamp(timestamp)
    return timestamp


def secToTime(row):
    if row:
        return time.strftime("%I:%M %p", time.localtime(int(row)))


def secToMin(row):
    if row:
        return int((int(row) - time.time()) / 60)


def parseDates(string):
    try:
        reg = re.compile(
            r"(?:(?P<ranged>\w{3}\s\d*\s?-\s?(?:\w{3}\s)?\d+)|(?P<single>(?:\b\w{3}\s\d+(?!\d*\:|\s*-\s*))))"
        )

        output = {"start_date": [], "end_date": []}
        dic = {"ranged": [], "single": []}
        dates = list(
            re.finditer(
                reg,
                string,
            )
        )
        month = None
        daterange = []
        if not dates:
            output = date.today()
            return output

        for x in dates:
            if x.group("ranged"):
                dic["ranged"].append(x.group("ranged"))
            elif x.group("single"):
                dic["single"].append(x.group("single"))
        if dic["ranged"]:
            for dateRange in dic["ranged"]:
                month = re.findall(r"\w{3}", dateRange)
                daterange = re.findall(r"\d+", dateRange)

                zipedrange = list(zip_longest(month, daterange, fillvalue=month[0]))
                comp = [
                    search_dates(f"{ranges[0]} {ranges[1]}")[0][1]
                    for ranges in zipedrange
                ]
                output["start_date"].append(comp[0])
                output["end_date"].append(comp[1])

        if dic["single"]:
            for single in dic["single"]:

                output["start_date"].append(search_dates(single)[0][1])
                output["end_date"].append(None)

    except Exception as e:
        output["start_date"] = date.today()
        output["end_date"] = None

        logging.debug(string if string is not None else "None" + " " + str(e))

    return output

    # print(parseDates("Through Summer 2024"))
    # print(parseDates(None))
