from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import PlainTextResponse
from src.etl import Station, get_next_arrivals, minutes_until_arrivals

app = FastAPI(title="NYC MTA Train Arrivals API")


@app.get("/arrivals")
def get_arrivals(
    station: str = Query(..., description="Station name in lowercase with underscores (e.g., canal_st_southbound)"),
    config: str = Query("full", description="Response format: 'full' (JSON) or 'short' (plain text with top 3 minutes)")
):
    """
    Get the next train arrival times for a specified station.

    Args:
        station: Station identifier (e.g., "canal_st_southbound", "court_st_northbound")
        config: Response format - "full" returns JSON, "short" returns plain text with top 3 minutes

    Returns:
        JSON object with arrival times and minutes until arrival (config=full)
        Plain text string with top 3 minutes separated by spaces (config=short)
    """
    # Convert station string to enum format (e.g., "canal_st_southbound" -> "CANAL_ST_SOUTHBOUND")
    station_enum_name = station.upper()

    try:
        station_enum = Station[station_enum_name]
    except KeyError:
        available_stations = [s.name.lower() for s in Station]
        raise HTTPException(
            status_code=400,
            detail=f"Invalid station '{station}'. Available stations: {', '.join(available_stations)}"
        )

    # Get arrival data
    arrival_times = get_next_arrivals(station_enum)
    minutes = minutes_until_arrivals(arrival_times)

    # Handle short format
    if config == "short":
        top_three = minutes[:3]
        return PlainTextResponse(" ".join(map(str, top_three)))

    # Handle full format (default)
    return {
        "station": station,
        "count": len(arrival_times),
        "arrivals": [
            {
                "arrival_time": arrival_time.isoformat(),
                "minutes_until_arrival": mins
            }
            for arrival_time, mins in zip(arrival_times, minutes)
        ]
    }


@app.get("/")
def root():
    """Root endpoint with API information."""
    return {
        "message": "NYC MTA Train Arrivals API",
        "endpoints": {
            "/arrivals": "Get train arrival times for a station",
            "/docs": "Interactive API documentation"
        },
        "available_stations": [s.name.lower() for s in Station]
    }
