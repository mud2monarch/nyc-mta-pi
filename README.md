# NYC MTA Train Arrivals API

Real-time NYC subway arrival times via a simple REST API.

## Usage

**Get arrival times (JSON):**
```
GET /arrivals?station=court_st_northbound
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
