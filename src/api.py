from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import PlainTextResponse
from src.etl import Station, get_next_arrivals, minutes_until_arrivals
from src.alta_parking import check_parking_availability, get_availability_calendar

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
            "/parking": "Check Alta parking availability for a date",
            "/parking/calendar": "Get full Alta parking availability calendar",
            "/docs": "Interactive API documentation"
        },
        "available_stations": [s.name.lower() for s in Station]
    }


@app.get("/parking")
async def get_parking_availability(
    date: str = Query(..., description="Date to check in YYYY-MM-DD format (e.g., 2025-01-15)")
):
    """
    Check parking availability at Alta Ski Area for a specific date.

    Args:
        date: Date string in YYYY-MM-DD format

    Returns:
        JSON object with availability status and rate information
    """
    # Validate date format
    try:
        from datetime import datetime
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid date format '{date}'. Use YYYY-MM-DD format (e.g., 2025-01-15)"
        )

    result = await check_parking_availability(date)

    if result.get("error"):
        raise HTTPException(
            status_code=500,
            detail=f"Error checking availability: {result['error']}"
        )

    return result


@app.get("/parking/calendar")
async def get_parking_calendar():
    """
    Get the full parking availability calendar for Alta Ski Area.

    Returns:
        JSON object with availability status for each date in the calendar
    """
    result = await get_availability_calendar()

    if result.get("error"):
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching calendar: {result['error']}"
        )

    return result
