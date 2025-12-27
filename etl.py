from datetime import datetime
from enum import Enum
from nyct_gtfs import NYCTFeed


class Station(Enum):
    # https://github.com/briansukhnandan/where-is-the-train/blob/main/src/app/api/stops.json
    EIGHTYSIXTH_ST_SOUTHBOUND = ("1", "121S", "86th St")
    GRAND_ARMY_NORTHBOUND = ("2", "237N", "Grand Army Plaza")
    COURT_ST_NORTHBOUND = ("R", "R28N", "Court St")
    CANAL_ST_SOUTHBOUND = ("R", "R23S", "Canal St")
    def __init__(self, line_id: str, stop_id: str, stop_name: str):
        self.line_id = line_id
        self.stop_id = stop_id
        self.stop_name = stop_name


def get_next_arrivals(station: Station) -> list[datetime]:
    """
    Get the next arrival times for trains at the specified stop.

    Args:
        stop: The Stop enum representing the desired station and direction

    Returns:
        A list of datetime objects representing arrival times, sorted in ascending order
    """
    # Load the realtime feed from the MTA site
    feed = NYCTFeed(station.line_id)

    # Get all trains currently underway to this stop
    trains: list[str] = feed.filter_trips(headed_for_stop_id=[station.stop_id], underway=True)

    # Extract arrival times for the specified stop
    arrival_times: list[datetime] = []
    for train in trains:
        for stop_update in train.stop_time_updates:
            if stop_update.stop_name == station.stop_name:
                if stop_update.arrival:
                    arrival_times.append(stop_update.arrival)
                break

    # Sort and return arrival times
    return sorted(arrival_times)


def minutes_until_arrivals(arrival_times: list[datetime]) -> list[int]:
    """
    Convert arrival datetimes to minutes until arrival from now.

    Args:
        arrival_times: List of datetime objects representing arrival times

    Returns:
        List of integers representing minutes until each arrival, rounded down
    """
    now = datetime.now()
    return [int((arrival - now).total_seconds() // 60) for arrival in arrival_times]
