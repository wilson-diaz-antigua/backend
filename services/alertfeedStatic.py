# Standard library imports
import copy
import csv
import json
import os
import re
from collections import defaultdict
from pathlib import Path
from pprint import pprint

# Third-party imports
import requests
from dotenv import load_dotenv

# Local imports (currently commented)
# from .database import db
# from .models import Alerts, Stop
# from backend.route import server
# from util.utils import convert_to_datetime, dateparsing

# Configuration and constants
load_dotenv(".env.MTA")
MTA_API_KEY = os.getenv("MTA_API_KEY")
STOPS_PATH = Path(__file__).parent.parent / "util" / "stops.csv"
MTA_ALERTS_URL = (
    "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/camsys%2Fsubway-alerts.json"
)

SERVICE_STATUS = {
    "Delays": "delays.png",
    "Planned - Part Suspended": "suspended.png",
    "Planned - Stations Skipped": "skipped.png",
    "Station Notice": "information.png",
    "Reduced Service": "reduced.png",
}


def fetch_alert_data():
    """Fetch alert data from MTA API."""
    headers = {"x-api-key": MTA_API_KEY}
    response = requests.get(
        MTA_ALERTS_URL,
        headers=headers,
        timeout=10,
    )
    return json.loads(response.content)


def initialize_stops_data():
    """Initialize data structure for storing stops information."""
    base_info = {
        "alertInfo": [],
    }
    affected_stops = defaultdict(dict)

    with STOPS_PATH.open() as csvfile:
        reader = csv.DictReader(csvfile)
        for col in reader:
            stop_id = col.get("stop_id", "")
            if stop_id and stop_id[-1].isdigit():
                affected_stops[stop_id] = copy.deepcopy(base_info)

    affected_stops["None"] = copy.deepcopy(base_info)

    return {key: copy.deepcopy(value) for key, value in affected_stops.items() if value}


def extract_alert_info(alert, informed_entity):
    """Extract relevant information from an alert entity."""
    alert_type = alert.get("transit_realtime.mercury_alert", {})
    translation = alert_type.get("human_readable_active_period", {}).get(
        "translation", {}
    )
    date = (
        translation[0].get("text", {})
        if isinstance(translation, list)
        else translation.get("text", {})
    )

    head = alert.get("header_text", {}).get("translation", {})
    descr = alert.get("description_text", {}).get("translation", {})

    heading = head[0]["text"] if head else ""
    direction_match = re.search(
        r"(downtown|uptown)|(?!(the|a|an))\b(\w+\s?)(\w*-?)bound",
        heading,
    )

    return {
        "alertType": alert_type.get("alert_type", {}),
        "createdAt": alert_type.get("created_at", {}),
        "updatedAt": alert_type.get("updated_at", {}),
        "date": date,
        "direction": direction_match.group(0) if direction_match else None,
        "heading": heading,
        "description": descr[0]["text"] if descr else "",
        "line": informed_entity[0].get("route_id", None),
        "activePeriod": alert.get("active_period", {}),
    }


def process_alert_feed() -> list:
    """
    Process the alert feed and extract relevant information about subway alerts.

    Returns:
        list: A list of dictionaries containing stops and their alerts.
    """
    alert_feed = fetch_alert_data()
    line_stops = initialize_stops_data()

    # Create a dictionary to collect alerts by stop_id
    alerts_by_stop = defaultdict(list)

    for entity in alert_feed["entity"]:
        informed_entities = entity.get("alert", {}).get("informed_entity", {})

        # Skip if there are no informed entities or no route ID
        if not informed_entities or not informed_entities[0].get("route_id", None):
            continue

        alert = entity.get("alert", {})
        alert_info = extract_alert_info(alert, informed_entities)

        # Process each informed entity to determine affected stops
        for info in informed_entities:
            stop_id = info.get("stop_id", None)

            if stop_id and stop_id in line_stops:
                # Format the alert data according to desired output structure
                formatted_alert = {
                    "alert_type": alert_info["alertType"],
                    "dateText": alert_info["date"],
                    "direction": alert_info["direction"],
                    "heading": alert_info["heading"],
                    "parsedDate": None,  # Will be set by convert_dates if needed
                    "route": alert_info["line"],
                    "activePeriod": alert_info["activePeriod"],  # Added activePeriod
                }
                alerts_by_stop[stop_id].append(formatted_alert)

    # Convert to the final output format
    result = []
    for stop_id, alerts in alerts_by_stop.items():
        result.append({"alerts": alerts, "stop": stop_id})

    # Add stops with no alerts
    for stop_id in line_stops:
        if stop_id not in alerts_by_stop and stop_id != "None":
            result.append({"alerts": [], "stop": stop_id})

    return result


def convert_dates(dic):
    """Convert date strings in the alert dictionary to datetime objects."""
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
    """Add alerts to the database."""
    alert_dict = process_alert_feed()
    with db.session.no_autoflush:
        try:
            for key, values in alert_dict.items():
                # Find or create stop
                existing_stop = Stop.query.filter_by(stop=str(key)).first()
                stop = existing_stop or Stop(stop=str(key))

                if not existing_stop:
                    db.session.add(stop)
                    db.session.flush()

                # Process each alert for this stop
                for alert in values["alertInfo"]:
                    date_text = alert.get("date", {})
                    if isinstance(date_text, dict):
                        date_text = json.dumps(date_text)

                    # Create alert object
                    alert_obj = Alerts(
                        alert_type=alert["alertType"],
                        created_at=alert["createdAt"],
                        updated_at=alert["updatedAt"],
                        direction=alert["direction"],
                        heading=alert["heading"],
                        route=str(alert["line"]),
                        dateText=date_text,
                    )

                    # Check if alert already exists
                    instance = Alerts.query.filter_by(
                        alert_type=alert_obj.alert_type,
                        route=alert_obj.route,
                        direction=alert_obj.direction,
                        heading=alert_obj.heading,
                        created_at=alert_obj.created_at,
                        updated_at=alert_obj.updated_at,
                        parsedDate=alert_obj.parsedDate,
                        stop_id=stop.id,
                    ).first()

                    # Add if not exists
                    if not instance:
                        alert_obj.stop = stop
                        db.session.add(alert_obj)

            db.session.commit()
            return True

        except Exception as e:
            db.session.rollback()
            raise RuntimeError(f"Failed to add alerts: {str(e)}")


def main():
    """Entry point for running the script directly."""
    with open("result.json", "w") as f:
        json.dump(process_alert_feed(), f, indent=4)


if __name__ == "__main__":
    main()
