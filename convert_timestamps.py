import datetime
import json
import os
from copy import deepcopy


def convert_timestamp(ts):
    """Convert Unix timestamp to dd/mm/yyyy format"""
    if (
        isinstance(ts, (int, float)) and ts > 1000000000
    ):  # Basic validation for Unix timestamp
        try:
            dt = datetime.datetime.fromtimestamp(ts)
            return dt.strftime("%d/%m/%Y")
        except (ValueError, OverflowError, TypeError):
            return ts
    return ts


def process_active_period(periods):
    """Process active_period arrays which contain start/end timestamps"""
    if not isinstance(periods, list):
        return periods

    for period in periods:
        if isinstance(period, dict):
            if "start" in period and isinstance(period["start"], (int, float)):
                period["start"] = convert_timestamp(period["start"])
            if "end" in period and isinstance(period["end"], (int, float)):
                period["end"] = convert_timestamp(period["end"])

    return periods


def process_mercury_alert(alert_data):
    """Process mercury_alert objects which contain timestamp fields"""
    if not isinstance(alert_data, dict):
        return alert_data

    # Convert common timestamp fields
    for field in ["created_at", "updated_at"]:
        if field in alert_data:
            alert_data[field] = convert_timestamp(alert_data[field])

    return alert_data


def process_entity(entity):
    """Process an individual entity in the data"""
    if not isinstance(entity, dict) or "alert" not in entity:
        return entity

    # Process active periods
    if "active_period" in entity["alert"]:
        entity["alert"]["active_period"] = process_active_period(
            entity["alert"]["active_period"]
        )

    # Process mercury alert
    if "transit_realtime.mercury_alert" in entity["alert"]:
        entity["alert"]["transit_realtime.mercury_alert"] = process_mercury_alert(
            entity["alert"]["transit_realtime.mercury_alert"]
        )

    return entity


def main():
    # Path to the data.json file
    json_path = "/Users/wilson/Desktop/project/MTAalertTracker/backend/data.json"

    # Load the JSON data
    with open(json_path, "r") as f:
        data = json.load(f)

    # Make a deep copy to work with
    updated_data = deepcopy(data)

    # Convert the main timestamp if it's in Unix format
    if "header" in updated_data and "timestamp" in updated_data["header"]:
        # Check if it's not already in dd/mm/yyyy format
        if (
            not isinstance(updated_data["header"]["timestamp"], str)
            or not updated_data["header"]["timestamp"].count("/") == 2
        ):
            updated_data["header"]["timestamp"] = convert_timestamp(
                updated_data["header"]["timestamp"]
            )

    # Process each entity
    if "entity" in updated_data:
        for i, entity in enumerate(updated_data["entity"]):
            updated_data["entity"][i] = process_entity(entity)

    # Write the updated data back to the file
    with open(json_path, "w") as f:
        json.dump(updated_data, f, indent=2)

    print(f"Timestamps in {json_path} have been converted to dd/mm/yyyy format.")


if __name__ == "__main__":
    main()
