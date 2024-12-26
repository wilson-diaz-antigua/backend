import copy
import csv
import json
import os
import re
from collections import defaultdict
from pathlib import Path

import requests
from dotenv import load_dotenv

# from backend.route import server
from backend.util.utils import convert_to_datetime, dateparsing

from .database import db
from .models import Alerts, Stop

stopsPath = (
    Path(__file__).parent.parent.parent / "alertsDisplayApp" / "util" / "stops.csv"
)
load_dotenv(".env.MTA")
MTA_API_KEY = os.getenv("MTA_API_KEY")
service_status = {
    "Delays": "delays.png",
    "Planned - Part Suspended": "suspended.png",
    "Planned - Stations Skipped": "skipped.png",
    "Station Notice": "information.png",
    "Reduced Service": "reduced.png",
}


def process_alert_feed() -> dict:
    """
    Process the alert feed and extract relevant information about subway alerts.

    Returns:
        dict: A dictionary containing information about affected stops and alerts.

         'stop name': { 'line':  str
                        'alertInfo': {'alertType': str,
                                    'createdAt': datetime,
                                    'updatedAt': datetime},
                                    'dates': {'date': [datetime],
                                            'time': [datetime],
                                            'dateText': str },
                                    'direction': str,
                                    'heading': str,
                                    'description': str
                         }



    """

    headers = {"x-api-key": MTA_API_KEY}
    Response = requests.get(
        "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/camsys%2Fsubway-alerts.json",
        headers=headers,
        timeout=10,
    )
    alert_feed = json.loads(Response.content)
    info = defaultdict()
    info = {
        "alertInfo": [],
    }
    affected_stops = defaultdict()
    with stopsPath.open() as csvfile:
        reader = csv.DictReader(csvfile)
        affected_stops.update(
            {
                col["stop_id"]: info
                for col in reader
                if col["stop_id"] and col["stop_id"][-1].isdigit()
            }
        )
        affected_stops["None"] = info
    line_stops = defaultdict()
    line_stops = {
        key: copy.deepcopy(value) for key, value in affected_stops.items() if value
    }

    alert_info = []
    for entity in alert_feed["entity"]:

        informed_ent = entity.get("alert", {}).get("informed_entity", {})

        if informed_ent[0].get("route_id", None):

            alert = entity.get("alert", {})
            alert_type = alert.get("transit_realtime.mercury_alert", {})
            translation = alert_type.get("human_readable_active_period", {}).get(
                "translation", {}
            )
            date = (
                translation[0].get("text", {})
                if isinstance(translation, list)
                else translation.get("text", {})
            )
            alert_info = defaultdict()
            alert_info = {
                "alertType": alert_type.get("alert_type", {}),
                "createdAt": alert_type.get("created_at", {}),
                "updatedAt": alert_type.get("updated_at", {}),
                "date": date,
                "direction": None,
                "heading": None,
                "description": None,
                "line": None,
            }
            alert_info["line"] = informed_ent[0].get("route_id", None)

            for info in informed_ent:

                head = alert.get("header_text", {}).get("translation", {})
                descr = alert.get("description_text", {}).get("translation", {})

                stop_id = info.get("stop_id", None)
                heading = head[0]["text"]
                direction = re.search(
                    r"(downtown|uptown)|(?!(the|a|an))\b(\w+\s?)(\w*-?)bound",
                    heading,
                )

                alert_info["heading"] = head[0]["text"]
                alert_info["direction"] = direction.group(0) if direction else None
                alert_info["description"] = descr[0]["text"] if descr else ""

                if info.get("stop_id", None) is not None:

                    line_stops[stop_id]["alertInfo"].append(alert_info)
                else:
                    line_stops["None"]["alertInfo"].append(alert_info)

    return line_stops


def convert_dates(dic):

    for stop in dic.values():
        for alert in stop["alertInfo"]:

            try:

                alert["date"] = dateparsing(alert["date"])
            except AttributeError:
                pass

            alert["createdAt"] = convert_to_datetime(alert["createdAt"])
            alert["updatedAt"] = convert_to_datetime(alert["updatedAt"])
    return dic


def add_alerts_to_db():
    alert_dict = process_alert_feed()
    with db.session.no_autoflush:
        try:
            for key, values in alert_dict.items():
                existing_stop = Stop.query.filter_by(stop=str(key)).first()

                if existing_stop:
                    stop = existing_stop
                else:
                    stop = Stop(stop=str(key))
                    db.session.add(stop)
                    db.session.flush()

                for alert in values["alertInfo"]:
                    date_text = alert.get("date", {})
                    if isinstance(date_text, dict):
                        date_text = json.dumps(date_text)
                    alerts = Alerts(
                        alert_type=alert["alertType"],
                        created_at=alert["createdAt"],
                        updated_at=alert["updatedAt"],
                        direction=alert["direction"],
                        heading=alert["heading"],
                        route=str(alert["line"]),
                        dateText=date_text,
                    )

                    instance = Alerts.query.filter_by(
                        alert_type=alerts.alert_type,
                        route=alerts.route,
                        direction=alerts.direction,
                        heading=alerts.heading,
                        created_at=alerts.created_at,
                        updated_at=alerts.updated_at,
                        parsedDate=alerts.parsedDate,
                        stop_id=stop.id,
                    ).first()

                    if not instance:
                        alerts.stop = stop
                        db.session.add(alerts)

            db.session.commit()

        except Exception as e:
            db.session.rollback()
            raise RuntimeError(f"Failed to add alerts: {str(e)}")
