from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from nyct_gtfs import NYCTFeed


@dataclass(frozen=True)
class Arrival:
    line: str
    arrival_time: datetime


class Station(Enum):
    # https://github.com/briansukhnandan/where-is-the-train/blob/main/src/app/api/stops.json
    EIGHTYSIXTH_ST_SOUTHBOUND = (("1",), "121S", "86th St")
    GRAND_ARMY_NORTHBOUND = (("2",), "237N", "Grand Army Plaza")
    COURT_ST_NORTHBOUND = (("R",), "R28N", "Court St")
    CANAL_ST_SOUTHBOUND = (("R",), "R23S", "Canal St")
    BOROUGH_HALL_45_UPTOWN = (("4", "5"), "423N", "Borough Hall")
    BOROUGH_HALL_45_DOWNTOWN = (("4", "5"), "423S", "Borough Hall")
    BOROUGH_HALL_23_UPTOWN = (("2", "3"), "232N", "Borough Hall")
    BOROUGH_HALL_23_DOWNTOWN = (("2", "3"), "232S", "Borough Hall")
    JAY_ST_METROTECH_F_UPTOWN = (("F",), "A41N", "Jay St-MetroTech")
    JAY_ST_METROTECH_AC_UPTOWN = (("A", "C"), "A41N", "Jay St-MetroTech")

    def __init__(self, line_ids: tuple[str, ...], stop_id: str, stop_name: str):
        self.line_ids = line_ids
        self.stop_id = stop_id
        self.stop_name = stop_name


def get_next_arrivals(station: Station) -> list[Arrival]:
    """
    Get the next arrival times for trains at the specified stop.

    Args:
        station: The station, routes, and direction to query

    Returns:
        Arrivals with their train lines, sorted chronologically
    """
    # Load the realtime feed from the MTA site
    feed = NYCTFeed(station.line_ids[0])

    # Get all trains currently underway to this stop
    trains = feed.filter_trips(
        line_id=list(station.line_ids),
        headed_for_stop_id=[station.stop_id],
        underway=True,
    )

    # Extract arrival times for the specified stop
    arrivals: list[Arrival] = []
    for train in trains:
        for stop_update in train.stop_time_updates:
            if stop_update.stop_id == station.stop_id:
                if stop_update.arrival:
                    arrivals.append(Arrival(train.route_id, stop_update.arrival))
                break

    return sorted(arrivals, key=lambda arrival: arrival.arrival_time)


def minutes_until_arrivals(arrivals: list[Arrival]) -> list[int]:
    """
    Convert arrival datetimes to minutes until arrival from now.

    Args:
        arrivals: Arrivals to convert to minutes from now

    Returns:
        List of integers representing minutes until each arrival, rounded down
    """
    now = datetime.now()
    return [int((arrival.arrival_time - now).total_seconds() // 60) for arrival in arrivals]
