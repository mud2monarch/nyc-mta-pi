# NYC MTA Train Arrivals API

Real-time NYC subway arrival times via a simple REST API.

## Usage

**Get arrival times (JSON):**
```
GET /arrivals?station=court_st_northbound
```

Each arrival includes its train line, which distinguishes trains in combined
queries such as 4/5, 2/3, and A/C:

```json
{
  "line": "4",
  "arrival_time": "2026-08-10T12:34:56",
  "minutes_until_arrival": 5
}
```

**Get next 3 arrivals (plain text):**
```
GET /arrivals?station=canal_st_southbound&config=short
```
Returns: `5 12 18` (minutes until arrival)

## Available Stations

- `eightysixth_st_southbound` - 1 train to 86th St
- `grand_army_northbound` - 2 train to Grand Army Plaza
- `court_st_northbound` - R train to Court St
- `canal_st_southbound` - R train to Canal St
- `borough_hall_45_uptown` - Uptown 4/5 trains at Borough Hall
- `borough_hall_45_downtown` - Downtown 4/5 trains at Borough Hall
- `borough_hall_23_uptown` - Uptown 2/3 trains at Borough Hall
- `borough_hall_23_downtown` - Downtown 2/3 trains at Borough Hall
- `jay_st_metrotech_f_uptown` - Uptown F trains at Jay St-MetroTech
- `jay_st_metrotech_ac_uptown` - Uptown A/C trains at Jay St-MetroTech

Add more in `src/etl.py`.

## Development

```bash
make install  # Install dependencies
make run      # Run locally at http://localhost:8000
make deploy   # Deploy to DigitalOcean
```

## API Docs

Visit `/docs` for interactive Swagger documentation.

## License

MIT
